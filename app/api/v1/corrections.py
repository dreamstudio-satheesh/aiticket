from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user, require_admin
from app.models import User
from app.schemas.corrections import (
    CorrectionListItem, CorrectionDetail,
    CorrectionsStatsResponse, SimilarCorrectionResponse
)
from app.services.learning.corrections_service import (
    get_corrections, get_correction_detail,
    rebuild_corrections_index, get_corrections_stats,
    search_similar_corrections
)

router = APIRouter(prefix="/corrections", tags=["Corrections Learning"])


@router.get("/", response_model=List[CorrectionListItem])
def list_corrections(
    intent: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List corrections (significantly edited replies)."""
    corrections = get_corrections(
        db=db,
        tenant_id=current_user.tenant_id,
        intent=intent,
        limit=limit,
        offset=offset
    )
    return [CorrectionListItem(**c) for c in corrections]


@router.get("/stats", response_model=CorrectionsStatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get correction statistics."""
    stats = get_corrections_stats(db, current_user.tenant_id)
    return CorrectionsStatsResponse(**stats)


@router.get("/search", response_model=List[SimilarCorrectionResponse])
def search_corrections(
    q: str,
    top_k: int = Query(3, ge=1, le=10),
    current_user: User = Depends(get_current_user)
):
    """Search for similar past corrections (useful for checking if similar mistakes were made)."""
    results = search_similar_corrections(current_user.tenant_id, q, top_k)
    return [SimilarCorrectionResponse(**r) for r in results]


@router.get("/{correction_id}", response_model=CorrectionDetail)
def get_detail(
    correction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed view of a correction with full diff."""
    detail = get_correction_detail(db, current_user.tenant_id, correction_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Correction not found")
    return CorrectionDetail(**detail)


@router.post("/rebuild-index")
def rebuild_index(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Rebuild the corrections index (Admin only)."""
    count = rebuild_corrections_index(db, current_user.tenant_id)
    return {
        "indexed_count": count,
        "message": f"Successfully indexed {count} corrections"
    }
