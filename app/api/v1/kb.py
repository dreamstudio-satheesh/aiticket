from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user, require_admin
from app.models import User
from app.models.kb_article import KBCategory
from app.schemas.kb import (
    KBArticleCreate, KBArticleUpdate, KBArticleResponse,
    KBSearchResult, KBBulkIngest
)
from app.services.knowledge import tenant_kb_service

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


@router.post("/articles", response_model=KBArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(
    data: KBArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new KB article (Admin only)."""
    return tenant_kb_service.create_article(db, current_user.tenant_id, data)


@router.get("/articles", response_model=List[KBArticleResponse])
def list_articles(
    category: Optional[KBCategory] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all KB articles for current tenant."""
    return tenant_kb_service.list_articles(db, current_user.tenant_id, category)


@router.get("/articles/{article_id}", response_model=KBArticleResponse)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific KB article."""
    article = tenant_kb_service.get_article(db, current_user.tenant_id, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.put("/articles/{article_id}", response_model=KBArticleResponse)
def update_article(
    article_id: int,
    data: KBArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a KB article (Admin only)."""
    article = tenant_kb_service.get_article(db, current_user.tenant_id, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return tenant_kb_service.update_article(db, article, data)


@router.delete("/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a KB article (Admin only)."""
    article = tenant_kb_service.get_article(db, current_user.tenant_id, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    tenant_kb_service.delete_article(db, article)


@router.post("/articles/bulk", status_code=status.HTTP_201_CREATED)
def bulk_create_articles(
    data: KBBulkIngest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Bulk create KB articles (Admin only)."""
    created = 0
    for article_data in data.articles:
        tenant_kb_service.create_article(db, current_user.tenant_id, article_data)
        created += 1
    return {"created": created}


@router.post("/index")
def index_kb(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Re-index all KB articles into FAISS (Admin only)."""
    chunks = tenant_kb_service.index_tenant_kb(db, current_user.tenant_id)
    return {"indexed_chunks": chunks}


@router.get("/search", response_model=List[KBSearchResult])
def search_kb(
    q: str,
    top_k: int = 5,
    current_user: User = Depends(get_current_user)
):
    """Search tenant KB."""
    return tenant_kb_service.search_tenant_kb(current_user.tenant_id, q, top_k)


@router.get("/stats")
def get_stats(current_user: User = Depends(get_current_user)):
    """Get KB index stats."""
    return tenant_kb_service.get_tenant_kb_stats(current_user.tenant_id)
