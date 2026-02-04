from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, TimestampMixin


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    ANSWERED = "answered"
    CUSTOMER_REPLY = "customer_reply"
    CLOSED = "closed"
    ON_HOLD = "on_hold"


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    whmcs_ticket_id = Column(Integer, nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    department = Column(String(100))
    priority = Column(String(50))
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    client_email = Column(String(255))

    # Relationships
    tenant = relationship("Tenant", back_populates="tickets")
    ai_replies = relationship("AIReply", back_populates="ticket", cascade="all, delete-orphan")
    approved_reply = relationship("ApprovedReply", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
