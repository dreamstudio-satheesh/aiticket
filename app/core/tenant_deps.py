from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.tenant_query import TenantQuery
from app.core.deps import get_current_user
from app.models import User, Tenant, Ticket, AIReply, ApprovedReply, PromptVersion, RerankingConfig
from app.middleware.tenant import get_tenant_id


def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Tenant:
    """Get the current user's tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant not found or inactive")
    return tenant


def verify_tenant_access(resource_tenant_id: int, current_user: User = Depends(get_current_user)) -> bool:
    """Verify the current user has access to a resource's tenant."""
    if current_user.tenant_id != resource_tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return True


# Tenant-scoped query factories
def get_ticket_query(db: Session = Depends(get_db)) -> TenantQuery[Ticket]:
    return TenantQuery(db, Ticket)


def get_ai_reply_query(db: Session = Depends(get_db)) -> TenantQuery[AIReply]:
    return TenantQuery(db, AIReply)


def get_approved_reply_query(db: Session = Depends(get_db)) -> TenantQuery[ApprovedReply]:
    return TenantQuery(db, ApprovedReply)


def get_prompt_version_query(db: Session = Depends(get_db)) -> TenantQuery[PromptVersion]:
    return TenantQuery(db, PromptVersion)
