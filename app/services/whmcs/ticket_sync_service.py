"""Service for syncing tickets from WHMCS to local database."""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import Ticket, Tenant, TicketStatus
from app.services.whmcs.whmcs_client import create_client_from_tenant, WHMCSTicket


STATUS_MAP = {
    "Open": TicketStatus.OPEN,
    "Answered": TicketStatus.ANSWERED,
    "Customer-Reply": TicketStatus.CUSTOMER_REPLY,
    "Closed": TicketStatus.CLOSED,
    "On Hold": TicketStatus.ON_HOLD,
}


def map_status(whmcs_status: str) -> TicketStatus:
    """Map WHMCS status to local enum."""
    return STATUS_MAP.get(whmcs_status, TicketStatus.OPEN)


def sync_ticket(db: Session, tenant_id: int, whmcs_ticket: WHMCSTicket) -> Ticket:
    """Sync a single ticket from WHMCS to local database."""
    # Check if ticket exists
    existing = db.query(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        Ticket.whmcs_ticket_id == whmcs_ticket.id
    ).first()

    if existing:
        # Update existing ticket
        existing.subject = whmcs_ticket.subject
        existing.content = whmcs_ticket.message
        existing.department = whmcs_ticket.dept_name
        existing.priority = whmcs_ticket.priority
        existing.status = map_status(whmcs_ticket.status)
        existing.client_email = whmcs_ticket.email
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new ticket
        ticket = Ticket(
            tenant_id=tenant_id,
            whmcs_ticket_id=whmcs_ticket.id,
            subject=whmcs_ticket.subject,
            content=whmcs_ticket.message,
            department=whmcs_ticket.dept_name,
            priority=whmcs_ticket.priority,
            status=map_status(whmcs_ticket.status),
            client_email=whmcs_ticket.email,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket


def sync_tickets_from_whmcs(
    db: Session,
    tenant: Tenant,
    status: Optional[str] = None,
    limit: int = 25
) -> List[Ticket]:
    """Sync multiple tickets from WHMCS."""
    client = create_client_from_tenant(tenant)

    # Fetch tickets from WHMCS
    whmcs_tickets = client.get_tickets(status=status, limit=limit)

    synced = []
    for whmcs_ticket in whmcs_tickets:
        ticket = sync_ticket(db, tenant.id, whmcs_ticket)
        synced.append(ticket)

    return synced


def sync_single_ticket(
    db: Session,
    tenant: Tenant,
    whmcs_ticket_id: int
) -> Optional[Ticket]:
    """Sync a single ticket by WHMCS ticket ID."""
    client = create_client_from_tenant(tenant)

    whmcs_ticket = client.get_ticket(whmcs_ticket_id)
    if not whmcs_ticket:
        return None

    return sync_ticket(db, tenant.id, whmcs_ticket)


def get_local_tickets(
    db: Session,
    tenant_id: int,
    status: Optional[TicketStatus] = None,
    limit: int = 25,
    offset: int = 0
) -> List[Ticket]:
    """Get tickets from local database."""
    query = db.query(Ticket).filter(Ticket.tenant_id == tenant_id)

    if status:
        query = query.filter(Ticket.status == status)

    return query.order_by(Ticket.updated_at.desc()).offset(offset).limit(limit).all()


def get_ticket_by_id(db: Session, tenant_id: int, ticket_id: int) -> Optional[Ticket]:
    """Get a single ticket by local ID."""
    return db.query(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        Ticket.id == ticket_id
    ).first()


def get_pending_tickets(db: Session, tenant_id: int, limit: int = 10) -> List[Ticket]:
    """Get tickets that need AI response (Open or Customer-Reply status)."""
    return db.query(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        Ticket.status.in_([TicketStatus.OPEN, TicketStatus.CUSTOMER_REPLY])
    ).order_by(Ticket.updated_at.desc()).limit(limit).all()
