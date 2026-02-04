from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user, require_admin
from app.core.tenant_deps import get_current_tenant
from app.models import User, Tenant, Ticket
from app.models.ticket import TicketStatus
from app.schemas.whmcs import (
    WHMCSConfigCreate, WHMCSConfigResponse, WHMCSDepartment,
    TicketResponse, TicketListResponse, SyncRequest, SyncResponse
)
from app.services.encryption import encrypt
from app.services.whmcs import (
    create_client_from_tenant, WHMCSAPIError,
    sync_tickets_from_whmcs, get_local_tickets, get_ticket_by_id, get_pending_tickets
)

router = APIRouter(prefix="/whmcs", tags=["WHMCS Integration"])


@router.post("/config", response_model=WHMCSConfigResponse)
def configure_whmcs(
    config: WHMCSConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Configure WHMCS API credentials (Admin only). Credentials are encrypted."""
    # Encrypt credentials
    tenant.whmcs_url = config.whmcs_url
    tenant.whmcs_api_identifier = encrypt(config.api_identifier)
    tenant.whmcs_api_secret = encrypt(config.api_secret)
    db.commit()

    # Test connection
    try:
        client = create_client_from_tenant(tenant)
        valid = client.test_connection()
    except Exception:
        valid = False

    return WHMCSConfigResponse(
        whmcs_url=tenant.whmcs_url,
        is_configured=True,
        connection_valid=valid
    )


@router.get("/config", response_model=WHMCSConfigResponse)
def get_whmcs_config(
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get WHMCS configuration status."""
    is_configured = bool(tenant.whmcs_url and tenant.whmcs_api_identifier)

    valid = False
    if is_configured:
        try:
            client = create_client_from_tenant(tenant)
            valid = client.test_connection()
        except Exception:
            valid = False

    return WHMCSConfigResponse(
        whmcs_url=tenant.whmcs_url if is_configured else None,
        is_configured=is_configured,
        connection_valid=valid
    )


@router.get("/departments", response_model=List[WHMCSDepartment])
def get_departments(
    tenant: Tenant = Depends(get_current_tenant)
):
    """Get WHMCS support departments."""
    try:
        client = create_client_from_tenant(tenant)
        departments = client.get_departments()
        return [WHMCSDepartment(**d) for d in departments]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WHMCSAPIError as e:
        raise HTTPException(status_code=502, detail=f"WHMCS API error: {str(e)}")


@router.post("/sync", response_model=SyncResponse)
def sync_tickets(
    request: SyncRequest,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Sync tickets from WHMCS to local database."""
    try:
        tickets = sync_tickets_from_whmcs(
            db=db,
            tenant=tenant,
            status=request.status,
            limit=request.limit
        )

        return SyncResponse(
            synced_count=len(tickets),
            tickets=[_ticket_to_response(t, db) for t in tickets]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WHMCSAPIError as e:
        raise HTTPException(status_code=502, detail=f"WHMCS API error: {str(e)}")


@router.get("/tickets", response_model=TicketListResponse)
def list_tickets(
    status: Optional[str] = None,
    page: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List synced tickets from local database."""
    status_enum = None
    if status:
        try:
            status_enum = TicketStatus(status)
        except ValueError:
            pass

    tickets = get_local_tickets(
        db=db,
        tenant_id=current_user.tenant_id,
        status=status_enum,
        limit=limit,
        offset=page * limit
    )

    total = db.query(Ticket).filter(Ticket.tenant_id == current_user.tenant_id).count()

    return TicketListResponse(
        tickets=[_ticket_to_response(t, db) for t in tickets],
        total=total,
        page=page,
        limit=limit
    )


@router.get("/tickets/pending", response_model=List[TicketResponse])
def list_pending_tickets(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tickets needing AI response (Open or Customer-Reply)."""
    tickets = get_pending_tickets(db, current_user.tenant_id, limit=limit)
    return [_ticket_to_response(t, db) for t in tickets]


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific ticket."""
    ticket = get_ticket_by_id(db, current_user.tenant_id, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _ticket_to_response(ticket, db)


def _ticket_to_response(ticket: Ticket, db: Session) -> TicketResponse:
    """Convert ticket model to response with AI reply status."""
    has_ai_reply = len(ticket.ai_replies) > 0 if ticket.ai_replies else False

    return TicketResponse(
        id=ticket.id,
        whmcs_ticket_id=ticket.whmcs_ticket_id,
        subject=ticket.subject,
        content=ticket.content,
        department=ticket.department,
        priority=ticket.priority,
        status=ticket.status,
        client_email=ticket.client_email,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        has_ai_reply=has_ai_reply
    )
