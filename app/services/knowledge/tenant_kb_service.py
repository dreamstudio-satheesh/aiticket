from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models.kb_article import KBArticle, KBCategory
from app.schemas.kb import KBArticleCreate, KBArticleUpdate
from app.services.embeddings import chunk_text, get_tenant_store


def create_article(db: Session, tenant_id: int, data: KBArticleCreate) -> KBArticle:
    """Create a new KB article."""
    article = KBArticle(
        tenant_id=tenant_id,
        title=data.title,
        content=data.content,
        category=data.category,
        tags=data.tags,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def update_article(db: Session, article: KBArticle, data: KBArticleUpdate) -> KBArticle:
    """Update an existing KB article."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)
    article.is_indexed = False  # Mark for re-indexing
    db.commit()
    db.refresh(article)
    return article


def delete_article(db: Session, article: KBArticle) -> bool:
    """Delete a KB article."""
    db.delete(article)
    db.commit()
    return True


def get_article(db: Session, tenant_id: int, article_id: int) -> Optional[KBArticle]:
    """Get a single article by ID."""
    return db.query(KBArticle).filter(
        KBArticle.id == article_id,
        KBArticle.tenant_id == tenant_id
    ).first()


def list_articles(db: Session, tenant_id: int, category: Optional[KBCategory] = None) -> List[KBArticle]:
    """List all articles for a tenant."""
    query = db.query(KBArticle).filter(KBArticle.tenant_id == tenant_id)
    if category:
        query = query.filter(KBArticle.category == category)
    return query.order_by(KBArticle.updated_at.desc()).all()


def index_tenant_kb(db: Session, tenant_id: int) -> int:
    """
    Index all active KB articles for a tenant into FAISS.
    Returns number of chunks indexed.
    """
    store = get_tenant_store(tenant_id, "kb")
    store.clear()  # Fresh index

    articles = db.query(KBArticle).filter(
        KBArticle.tenant_id == tenant_id,
        KBArticle.is_active == True
    ).all()

    total_chunks = 0

    for article in articles:
        # Combine title and content for better context
        full_text = f"# {article.title}\n\n{article.content}"

        chunks = chunk_text(full_text, metadata={
            "source": f"kb_article_{article.id}",
            "article_id": article.id,
            "title": article.title,
            "category": article.category.value,
            "tags": article.tags,
            "type": "tenant_kb"
        })

        if chunks:
            texts = [c["content"] for c in chunks]
            metadata = [c["metadata"] for c in chunks]
            store.add(texts, metadata)
            total_chunks += len(chunks)

        # Mark as indexed
        article.is_indexed = True

    db.commit()
    return total_chunks


def search_tenant_kb(tenant_id: int, query: str, top_k: int = 5) -> List[Dict]:
    """Search tenant-specific knowledge base."""
    store = get_tenant_store(tenant_id, "kb")
    results = store.search(query, top_k=top_k)
    return [{
        "content": r[0]["content"],
        "score": r[1],
        "source": r[0].get("source", ""),
        "category": r[0].get("category"),
        "article_id": r[0].get("article_id"),
    } for r in results]


def get_tenant_kb_stats(tenant_id: int) -> Dict:
    """Get stats about tenant KB index."""
    store = get_tenant_store(tenant_id, "kb")
    return {
        "total_chunks": store.count,
        "index_path": str(store.index_path),
    }
