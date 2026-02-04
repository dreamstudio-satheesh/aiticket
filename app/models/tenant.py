from sqlalchemy import Column, Integer, String, Text, JSON, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)

    # WHMCS integration
    whmcs_url = Column(String(500))
    whmcs_api_identifier = Column(Text)  # Encrypted
    whmcs_api_secret = Column(Text)  # Encrypted

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="tenant", cascade="all, delete-orphan")
    prompt_versions = relationship("PromptVersion", back_populates="tenant", cascade="all, delete-orphan")
    reranking_config = relationship("RerankingConfig", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
