from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class RerankingConfig(Base, TimestampMixin):
    __tablename__ = "reranking_configs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, unique=True, index=True)  # NULL = global default

    # Reranking model settings
    is_enabled = Column(Boolean, default=True)
    model_name = Column(String(255), default="cross-encoder/ms-marco-MiniLM-L-6-v2")

    # Retrieval weights (for weighted merge)
    weight_global_kb = Column(Float, default=0.2)
    weight_tenant_kb = Column(Float, default=0.3)
    weight_approved_examples = Column(Float, default=0.35)
    weight_corrections = Column(Float, default=0.15)

    # Reranking parameters
    top_k_initial = Column(Integer, default=20)  # Initial retrieval count
    top_k_rerank = Column(Integer, default=5)  # Final count after reranking
    score_threshold = Column(Float, default=0.5)  # Minimum rerank score

    # Advanced settings
    settings = Column(JSON, default=dict)

    # Relationships
    tenant = relationship("Tenant", back_populates="reranking_config")
