from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, TimestampMixin


class AuditAction(str, enum.Enum):
    TICKET_SYNCED = "ticket_synced"
    DRAFT_GENERATED = "draft_generated"
    DRAFT_REGENERATED = "draft_regenerated"
    REPLY_APPROVED = "reply_approved"
    REPLY_EDITED = "reply_edited"
    CORRECTION_FLAGGED = "correction_flagged"
    KB_INDEXED = "kb_indexed"
    PROMPT_CHANGED = "prompt_changed"


class AuditLog(Base, TimestampMixin):
    """Audit log for tracking all significant actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    action = Column(Enum(AuditAction), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # ticket, ai_reply, approved_reply, etc.
    entity_id = Column(Integer, nullable=True)

    # Action details
    details = Column(JSON, default=dict)

    # For reply actions
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True)
    ai_reply_id = Column(Integer, ForeignKey("ai_replies.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")
