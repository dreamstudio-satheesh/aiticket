from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.knowledge import (
    search_global_kb,
    search_examples,
    search_corrections,
    retrieve_context,
    format_context_for_prompt,
)
from app.services.knowledge.tenant_kb_service import search_tenant_kb

router = APIRouter(prefix="/search", tags=["Search"])


class SearchResult(BaseModel):
    content: str
    score: float
    source: str
    source_type: str


class UnifiedSearchResponse(BaseModel):
    global_kb: List[SearchResult]
    tenant_kb: List[SearchResult]
    examples: List[SearchResult]
    corrections: List[SearchResult]
    merged: List[SearchResult]
    formatted_context: str


@router.get("/global", response_model=List[SearchResult])
def search_global(q: str, top_k: int = 5):
    """Search global knowledge base (public)."""
    results = search_global_kb(q, top_k=top_k)
    return [SearchResult(
        content=r["content"],
        score=r["score"],
        source=r.get("source", ""),
        source_type="global_kb"
    ) for r in results]


@router.get("/tenant", response_model=List[SearchResult])
def search_tenant(
    q: str,
    top_k: int = 5,
    current_user: User = Depends(get_current_user)
):
    """Search tenant knowledge base."""
    results = search_tenant_kb(current_user.tenant_id, q, top_k=top_k)
    return [SearchResult(
        content=r["content"],
        score=r["score"],
        source=r.get("source", ""),
        source_type="tenant_kb"
    ) for r in results]


@router.get("/examples", response_model=List[SearchResult])
def search_tenant_examples(
    q: str,
    top_k: int = 5,
    current_user: User = Depends(get_current_user)
):
    """Search approved examples."""
    results = search_examples(current_user.tenant_id, q, top_k=top_k)
    return [SearchResult(
        content=r["content"],
        score=r["score"],
        source=r.get("source", ""),
        source_type="example"
    ) for r in results]


@router.get("/unified", response_model=UnifiedSearchResponse)
def unified_search(
    q: str,
    top_k: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search all sources with weighted merge.
    Returns context ready for RAG pipeline.
    """
    context = retrieve_context(db, current_user.tenant_id, q, top_k=top_k)

    def to_search_result(r) -> SearchResult:
        return SearchResult(
            content=r.content,
            score=r.score,
            source=r.source,
            source_type=r.source_type
        )

    return UnifiedSearchResponse(
        global_kb=[to_search_result(r) for r in context.global_kb],
        tenant_kb=[to_search_result(r) for r in context.tenant_kb],
        examples=[to_search_result(r) for r in context.examples],
        corrections=[to_search_result(r) for r in context.corrections],
        merged=[to_search_result(r) for r in context.merged],
        formatted_context=format_context_for_prompt(context)
    )
