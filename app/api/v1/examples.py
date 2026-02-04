from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user, require_admin
from app.models import User
from app.schemas.approved_reply import (
    ApprovedReplyListItem, ApprovedReplyDetail,
    ExamplesStatsResponse, RebuildIndexResponse
)
from app.services.learning import (
    get_approved_replies, get_approved_reply_detail,
    rebuild_examples_index, remove_from_training,
    mark_as_correction, get_examples_stats
)

router = APIRouter(prefix="/examples", tags=["Training Examples"])


@router.get("/", response_model=List[ApprovedReplyListItem])
def list_approved_replies(
    include_corrections: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List approved replies used for training."""
    replies = get_approved_replies(
        db=db,
        tenant_id=current_user.tenant_id,
        include_corrections=include_corrections,
        limit=limit,
        offset=offset
    )
    return [ApprovedReplyListItem(**r) for r in replies]


@router.get("/stats", response_model=ExamplesStatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics about training examples."""
    stats = get_examples_stats(db, current_user.tenant_id)
    return ExamplesStatsResponse(**stats)


@router.get("/{approved_id}", response_model=ApprovedReplyDetail)
def get_detail(
    approved_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed view of an approved reply with diff."""
    detail = get_approved_reply_detail(db, current_user.tenant_id, approved_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Approved reply not found")
    return ApprovedReplyDetail(**detail)


@router.post("/rebuild-index", response_model=RebuildIndexResponse)
def rebuild_index(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Rebuild the examples index from approved replies (Admin only)."""
    count = rebuild_examples_index(db, current_user.tenant_id)
    return RebuildIndexResponse(
        indexed_count=count,
        message=f"Successfully indexed {count} approved replies"
    )


@router.post("/{approved_id}/remove-from-training")
def remove_from_training_endpoint(
    approved_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Remove an approved reply from training examples (Admin only)."""
    success = remove_from_training(db, current_user.tenant_id, approved_id)
    if not success:
        raise HTTPException(status_code=404, detail="Approved reply not found")
    return {"message": "Removed from training. Run rebuild-index to update."}


@router.post("/{approved_id}/mark-correction")
def mark_as_correction_endpoint(
    approved_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Manually mark an approved reply as a correction (Admin only)."""
    success = mark_as_correction(db, current_user.tenant_id, approved_id)
    if not success:
        raise HTTPException(status_code=404, detail="Approved reply not found")
    return {"message": "Marked as correction. Will be used for correction learning."}
