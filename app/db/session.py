from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.base import Base

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. For MVP - just drop and recreate if schema changes."""
    from app.models import (Tenant, User, Ticket, PromptVersion,
                            RerankingConfig, AIReply, ApprovedReply)
    Base.metadata.create_all(bind=engine)
