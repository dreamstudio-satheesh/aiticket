from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, TimestampMixin


class KBCategory(str, enum.Enum):
    PRODUCT = "product"
    PRICING = "pricing"
    POLICY = "policy"
    SLA = "sla"
    FAQ = "faq"
    CUSTOM = "custom"


class KBArticle(Base, TimestampMixin):
    """Tenant-specific knowledge base articles."""
    __tablename__ = "kb_articles"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(Enum(KBCategory), default=KBCategory.CUSTOM)
    tags = Column(String(500))  # Comma-separated tags

    is_active = Column(Boolean, default=True)
    is_indexed = Column(Boolean, default=False)  # Synced to FAISS

    # Relationships
    tenant = relationship("Tenant", backref="kb_articles")
