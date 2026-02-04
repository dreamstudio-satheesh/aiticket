from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ApprovedReply(Base, TimestampMixin):
    __tablename__ = "approved_replies"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    ai_reply_id = Column(Integer, ForeignKey("ai_replies.id", ondelete="SET NULL"), nullable=True)

    # Content
    final_reply = Column(Text, nullable=False)
    edited = Column(Boolean, default=False)

    # Edit tracking
    edit_distance = Column(Float)  # Levenshtein ratio (0-1, 0=completely different)
    edit_summary = Column(Text)  # AI-generated summary of what changed

    # Learning flags
    used_for_training = Column(Boolean, default=False)  # Added to examples index
    is_correction = Column(Boolean, default=False)  # Significant edit, added to corrections

    # Relationships
    ticket = relationship("Ticket", back_populates="approved_reply")
