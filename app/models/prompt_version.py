from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class PromptVersion(Base, TimestampMixin):
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)  # NULL = global

    version = Column(String(50), nullable=False)  # e.g., "1.0.0", "1.1.0"
    name = Column(String(255), nullable=False)  # e.g., "Default Support Prompt"
    description = Column(Text)

    # Prompt components
    system_prompt = Column(Text, nullable=False)
    context_template = Column(Text, nullable=False)  # Template for injecting RAG context
    task_template = Column(Text, nullable=False)  # Template for the task/instruction

    # Configuration
    model = Column(String(100), default="gpt-4o-mini")
    temperature = Column(Integer, default=0.3)  # Stored as int, divide by 10
    max_tokens = Column(Integer, default=1000)

    # Metadata
    is_active = Column(Boolean, default=False)  # Only one active per tenant
    is_default = Column(Boolean, default=False)  # Default for new tenants
    performance_metrics = Column(JSON, default=dict)  # Avg confidence, edit rate, etc.

    # Relationships
    tenant = relationship("Tenant", back_populates="prompt_versions")
    ai_replies = relationship("AIReply", back_populates="prompt_version")
