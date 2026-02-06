import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User, Ticket, TicketStatus
from app.schemas.playground import PlaygroundRequest, PlaygroundResponse
from app.services.rag import generate_reply

router = APIRouter(prefix="/playground", tags=["Playground"])


@router.post("/generate", response_model=PlaygroundResponse)
def playground_generate(
    req: PlaygroundRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Create a transient Ticket (never added to DB session)
    ticket = Ticket(
        tenant_id=current_user.tenant_id,
        whmcs_ticket_id=0,
        subject=req.subject,
        content=req.content,
        department="General",
        priority="Normal",
        status=TicketStatus.OPEN,
    )

    rag = generate_reply(db, ticket, use_reranking=req.use_reranking)

    # Map context sources for frontend
    context_sources = []
    for src in rag.reranked_sources:
        context_sources.append({
            "content": src.get("content", "")[:200],
            "score": src.get("score", 0),
            "source": src.get("source", "unknown"),
        })

    return PlaygroundResponse(
        id=str(int(time.time() * 1000)),
        content=rag.reply,
        confidence=round(rag.confidence_score / 100, 2),
        timestamp=int(time.time() * 1000),
        intent_detected=rag.intent_detected,
        confidence_breakdown=rag.confidence_breakdown,
        recommendations=rag.recommendations,
        context_sources=context_sources or None,
        latency_ms=rag.latency_ms,
    )
