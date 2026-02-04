from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.models.kb_article import KBCategory


class KBArticleCreate(BaseModel):
    title: str
    content: str
    category: KBCategory = KBCategory.CUSTOM
    tags: Optional[str] = None


class KBArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[KBCategory] = None
    tags: Optional[str] = None
    is_active: Optional[bool] = None


class KBArticleResponse(BaseModel):
    id: int
    title: str
    content: str
    category: KBCategory
    tags: Optional[str]
    is_active: bool
    is_indexed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KBSearchResult(BaseModel):
    content: str
    score: float
    source: str
    category: Optional[str] = None
    article_id: Optional[int] = None


class KBBulkIngest(BaseModel):
    """For bulk ingesting products/policies from external source."""
    articles: List[KBArticleCreate]
