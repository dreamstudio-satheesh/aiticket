from sqlalchemy import Column, Integer, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class AIReply(Base, TimestampMixin):
    __tablename__ = "ai_replies"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt_version_id = Column(Integer, ForeignKey("prompt_versions.id", ondelete="SET NULL"), nullable=True, index=True)

    # Generated content
    ai_reply = Column(Text, nullable=False)

    # Confidence scoring breakdown
    confidence_score = Column(Float, nullable=False)  # 0-100
    confidence_breakdown = Column(JSON, default=dict)  # Individual component scores

    # Context tracking (for audit)
    context_sources = Column(JSON, default=list)  # List of retrieved chunks with scores
    reranked_sources = Column(JSON, default=list)  # After reranking

    # RAG metadata
    intent_detected = Column(Text)
    tokens_used = Column(Integer)
    latency_ms = Column(Integer)

    # Relationships
    ticket = relationship("Ticket", back_populates="ai_replies")
    prompt_version = relationship("PromptVersion", back_populates="ai_replies")
