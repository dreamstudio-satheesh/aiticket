from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User, Ticket, AIReply, ApprovedReply
from app.schemas.ai_reply import (
    GenerateReplyRequest, AIReplyResponse, AIReplyListResponse,
    TicketWithDraftResponse, ApproveReplyRequest
)
from app.schemas.confidence import ConfidenceLevelEnum
from app.services.rag import generate_reply
from app.services.whmcs import get_ticket_by_id

router = APIRouter(prefix="/replies", tags=["AI Replies"])


@router.post("/generate", response_model=AIReplyResponse)
def generate_ai_reply(
    request: GenerateReplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI draft reply for a ticket."""
    # Get ticket
    ticket = get_ticket_by_id(db, current_user.tenant_id, request.ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Generate reply using RAG pipeline
    rag_response = generate_reply(
        db=db,
        ticket=ticket,
        use_reranking=request.use_reranking
    )

    # Save AI reply to database
    ai_reply = AIReply(
        ticket_id=ticket.id,
        prompt_version_id=rag_response.prompt_version_id,
        ai_reply=rag_response.reply,
        confidence_score=rag_response.confidence_score,
        confidence_breakdown=rag_response.confidence_breakdown,
        context_sources=[{
            "content": r.content[:200],
            "score": r.score,
            "source": r.source,
            "type": r.source_type
        } for r in rag_response.context.merged[:5]],
        reranked_sources=rag_response.reranked_sources,
        intent_detected=rag_response.intent_detected,
        tokens_used=rag_response.tokens_used,
        latency_ms=rag_response.latency_ms,
    )
    db.add(ai_reply)
    db.commit()
    db.refresh(ai_reply)

    return AIReplyResponse(
        id=ai_reply.id,
        ticket_id=ai_reply.ticket_id,
        ai_reply=ai_reply.ai_reply,
        confidence_score=ai_reply.confidence_score,
        confidence_level=_score_to_level(ai_reply.confidence_score),
        confidence_breakdown=ai_reply.confidence_breakdown,
        recommendations=rag_response.recommendations,
        should_escalate=rag_response.should_escalate,
        intent_detected=ai_reply.intent_detected,
        tokens_used=ai_reply.tokens_used,
        latency_ms=ai_reply.latency_ms,
        prompt_version_id=ai_reply.prompt_version_id,
        created_at=ai_reply.created_at,
    )


@router.get("/ticket/{ticket_id}", response_model=TicketWithDraftResponse)
def get_ticket_with_draft(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ticket with its latest AI draft reply."""
    ticket = get_ticket_by_id(db, current_user.tenant_id, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Get latest AI reply
    latest_reply = db.query(AIReply).filter(
        AIReply.ticket_id == ticket_id
    ).order_by(AIReply.created_at.desc()).first()

    # Check if approved
    has_approved = db.query(ApprovedReply).filter(
        ApprovedReply.ticket_id == ticket_id
    ).first() is not None

    draft = None
    if latest_reply:
        draft = AIReplyResponse(
            id=latest_reply.id,
            ticket_id=latest_reply.ticket_id,
            ai_reply=latest_reply.ai_reply,
            confidence_score=latest_reply.confidence_score,
            confidence_level=_score_to_level(latest_reply.confidence_score),
            confidence_breakdown=latest_reply.confidence_breakdown or {},
            recommendations=_get_recommendations(latest_reply),
            should_escalate=latest_reply.confidence_score < 40,
            intent_detected=latest_reply.intent_detected,
            tokens_used=latest_reply.tokens_used or 0,
            latency_ms=latest_reply.latency_ms or 0,
            prompt_version_id=latest_reply.prompt_version_id,
            created_at=latest_reply.created_at,
        )

    return TicketWithDraftResponse(
        id=ticket.id,
        whmcs_ticket_id=ticket.whmcs_ticket_id,
        subject=ticket.subject,
        content=ticket.content,
        department=ticket.department,
        priority=ticket.priority,
        status=ticket.status.value,
        client_email=ticket.client_email,
        created_at=ticket.created_at,
        draft=draft,
        has_approved_reply=has_approved,
    )


@router.get("/ticket/{ticket_id}/history", response_model=List[AIReplyListResponse])
def get_reply_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all AI replies generated for a ticket."""
    ticket = get_ticket_by_id(db, current_user.tenant_id, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    replies = db.query(AIReply).filter(
        AIReply.ticket_id == ticket_id
    ).order_by(AIReply.created_at.desc()).all()

    return replies


@router.post("/approve", status_code=status.HTTP_201_CREATED)
def approve_reply_endpoint(
    request: ApproveReplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve an AI reply (with optional edits). Auto-indexes good replies for learning."""
    from app.services.learning import approve_reply as learning_approve

    # Get AI reply
    ai_reply = db.query(AIReply).filter(AIReply.id == request.ai_reply_id).first()
    if not ai_reply:
        raise HTTPException(status_code=404, detail="AI reply not found")

    # Verify ticket belongs to tenant
    ticket = get_ticket_by_id(db, current_user.tenant_id, ai_reply.ticket_id)
    if not ticket:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if already approved
    existing = db.query(ApprovedReply).filter(
        ApprovedReply.ticket_id == ticket.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Ticket already has approved reply")

    # Use learning service to approve and auto-index
    approved, edit_analysis = learning_approve(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        ticket=ticket,
        ai_reply=ai_reply,
        final_reply=request.final_reply,
        auto_index=True
    )

    return {
        "message": "Reply approved",
        "approved_reply_id": approved.id,
        "edited": edit_analysis.was_edited,
        "is_correction": edit_analysis.is_significant_edit,
        "indexed_for_learning": approved.used_for_training,
    }


@router.get("/pending", response_model=List[TicketWithDraftResponse])
def get_pending_drafts(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tickets with AI drafts pending approval."""
    # Get tickets with AI replies but no approved reply
    from app.models.ticket import TicketStatus

    tickets = db.query(Ticket).filter(
        Ticket.tenant_id == current_user.tenant_id,
        Ticket.status.in_([TicketStatus.OPEN, TicketStatus.CUSTOMER_REPLY])
    ).order_by(Ticket.updated_at.desc()).limit(limit).all()

    results = []
    for ticket in tickets:
        # Check if has approved reply
        has_approved = db.query(ApprovedReply).filter(
            ApprovedReply.ticket_id == ticket.id
        ).first() is not None

        if has_approved:
            continue

        # Get latest AI reply
        latest_reply = db.query(AIReply).filter(
            AIReply.ticket_id == ticket.id
        ).order_by(AIReply.created_at.desc()).first()

        draft = None
        if latest_reply:
            draft = AIReplyResponse(
                id=latest_reply.id,
                ticket_id=latest_reply.ticket_id,
                ai_reply=latest_reply.ai_reply,
                confidence_score=latest_reply.confidence_score,
                confidence_level=_score_to_level(latest_reply.confidence_score),
                confidence_breakdown=latest_reply.confidence_breakdown or {},
                recommendations=_get_recommendations(latest_reply),
                should_escalate=latest_reply.confidence_score < 40,
                intent_detected=latest_reply.intent_detected,
                tokens_used=latest_reply.tokens_used or 0,
                latency_ms=latest_reply.latency_ms or 0,
                prompt_version_id=latest_reply.prompt_version_id,
                created_at=latest_reply.created_at,
            )

        results.append(TicketWithDraftResponse(
            id=ticket.id,
            whmcs_ticket_id=ticket.whmcs_ticket_id,
            subject=ticket.subject,
            content=ticket.content,
            department=ticket.department,
            priority=ticket.priority,
            status=ticket.status.value,
            client_email=ticket.client_email,
            created_at=ticket.created_at,
            draft=draft,
            has_approved_reply=False,
        ))

    return results


def _score_to_level(score: float) -> ConfidenceLevelEnum:
    if score >= 80:
        return ConfidenceLevelEnum.HIGH
    elif score >= 60:
        return ConfidenceLevelEnum.MEDIUM
    elif score >= 40:
        return ConfidenceLevelEnum.LOW
    return ConfidenceLevelEnum.VERY_LOW


def _get_recommendations(ai_reply: AIReply) -> List[str]:
    """Generate recommendations based on confidence."""
    recommendations = []
    if ai_reply.confidence_score < 40:
        recommendations.append("Low confidence - recommend escalation")
    if ai_reply.confidence_score < 60:
        recommendations.append("Review carefully before sending")
    breakdown = ai_reply.confidence_breakdown or {}
    if breakdown.get("example_similarity", 0) < 30:
        recommendations.append("No similar past tickets found")
    if breakdown.get("kb_similarity", 0) < 30:
        recommendations.append("Limited knowledge base matches")
    return recommendations


def _calculate_edit_distance(original: str, edited: str) -> float:
    """Calculate similarity ratio between original and edited text."""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, original, edited).ratio()
