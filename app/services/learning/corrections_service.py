"""Service for managing corrections and using them to avoid repeating mistakes."""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from app.models import Ticket, AIReply, ApprovedReply
from app.services.embeddings import get_tenant_store
from app.services.tracking import analyze_edit


def add_to_corrections_index(
    db: Session,
    tenant_id: int,
    approved: ApprovedReply,
    ticket: Ticket,
    ai_reply: AIReply,
    edit_summary: Optional[str] = None
) -> bool:
    """
    Add a correction to the corrections index.
    Corrections help the AI avoid repeating past mistakes.
    """
    store = get_tenant_store(tenant_id, "corrections")

    # Generate edit summary if not provided
    if not edit_summary:
        edit_summary = generate_edit_summary(ai_reply.ai_reply, approved.final_reply)

    # Format: What was wrong + What was correct
    correction_text = f"""Customer Issue: {ticket.subject}
{ticket.content}

INCORRECT AI Response (Avoid This):
{ai_reply.ai_reply}

CORRECT Response (Use This Instead):
{approved.final_reply}

What Was Wrong: {edit_summary}"""

    metadata = {
        "source": f"correction_{approved.id}",
        "ticket_id": ticket.id,
        "ai_reply_id": ai_reply.id,
        "approved_reply_id": approved.id,
        "subject": ticket.subject,
        "department": ticket.department,
        "intent": ai_reply.intent_detected,
        "original_confidence": ai_reply.confidence_score,
        "edit_summary": edit_summary,
        "type": "correction",
    }

    store.add([correction_text], [metadata])

    # Update approved reply with summary
    approved.edit_summary = edit_summary
    db.commit()

    return True


def generate_edit_summary(original: str, corrected: str) -> str:
    """
    Generate a brief summary of what was changed.
    Simple heuristic-based approach (can be enhanced with LLM later).
    """
    edit_analysis = analyze_edit(original, corrected)

    summaries = []

    # Length changes
    if edit_analysis.char_diff > 100:
        summaries.append("Response was expanded with more detail")
    elif edit_analysis.char_diff < -100:
        summaries.append("Response was shortened/simplified")

    # Similarity-based inference
    if edit_analysis.similarity_ratio < 0.3:
        summaries.append("Response was completely rewritten")
    elif edit_analysis.similarity_ratio < 0.5:
        summaries.append("Major changes to content and approach")
    elif edit_analysis.similarity_ratio < 0.7:
        summaries.append("Significant corrections to accuracy or tone")

    # Check for specific patterns
    original_lower = original.lower()
    corrected_lower = corrected.lower()

    if "sorry" in corrected_lower and "sorry" not in original_lower:
        summaries.append("Added apology/empathy")

    if "escalat" in corrected_lower and "escalat" not in original_lower:
        summaries.append("Added escalation recommendation")

    if any(word in corrected_lower for word in ["unfortunately", "cannot", "unable"]) and \
       not any(word in original_lower for word in ["unfortunately", "cannot", "unable"]):
        summaries.append("Changed to acknowledge limitations")

    if not summaries:
        summaries.append("Content corrections made")

    return "; ".join(summaries)


def rebuild_corrections_index(db: Session, tenant_id: int) -> int:
    """Rebuild entire corrections index from approved replies marked as corrections."""
    store = get_tenant_store(tenant_id, "corrections")
    store.clear()

    # Get all corrections with AI replies
    corrections = db.query(ApprovedReply, Ticket, AIReply).join(
        Ticket, ApprovedReply.ticket_id == Ticket.id
    ).join(
        AIReply, ApprovedReply.ai_reply_id == AIReply.id
    ).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.is_correction == True,
        ApprovedReply.ai_reply_id.isnot(None)
    ).all()

    if not corrections:
        return 0

    texts = []
    metadata_list = []

    for approved, ticket, ai_reply in corrections:
        edit_summary = approved.edit_summary or generate_edit_summary(
            ai_reply.ai_reply, approved.final_reply
        )

        correction_text = f"""Customer Issue: {ticket.subject}
{ticket.content}

INCORRECT AI Response (Avoid This):
{ai_reply.ai_reply}

CORRECT Response (Use This Instead):
{approved.final_reply}

What Was Wrong: {edit_summary}"""

        texts.append(correction_text)
        metadata_list.append({
            "source": f"correction_{approved.id}",
            "ticket_id": ticket.id,
            "ai_reply_id": ai_reply.id,
            "approved_reply_id": approved.id,
            "subject": ticket.subject,
            "department": ticket.department,
            "intent": ai_reply.intent_detected,
            "original_confidence": ai_reply.confidence_score,
            "edit_summary": edit_summary,
            "type": "correction",
        })

        # Update summary if not set
        if not approved.edit_summary:
            approved.edit_summary = edit_summary

    store.add(texts, metadata_list)
    db.commit()

    return len(texts)


def get_corrections(
    db: Session,
    tenant_id: int,
    intent: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """Get corrections with details."""
    query = db.query(ApprovedReply, Ticket, AIReply).join(
        Ticket, ApprovedReply.ticket_id == Ticket.id
    ).outerjoin(
        AIReply, ApprovedReply.ai_reply_id == AIReply.id
    ).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.is_correction == True
    )

    if intent:
        query = query.filter(AIReply.intent_detected == intent)

    results = query.order_by(ApprovedReply.created_at.desc()).offset(offset).limit(limit).all()

    return [{
        "id": approved.id,
        "ticket_id": ticket.id,
        "ticket_subject": ticket.subject,
        "ai_reply_preview": ai_reply.ai_reply[:200] + "..." if ai_reply and len(ai_reply.ai_reply) > 200 else (ai_reply.ai_reply if ai_reply else None),
        "final_reply_preview": approved.final_reply[:200] + "..." if len(approved.final_reply) > 200 else approved.final_reply,
        "edit_summary": approved.edit_summary,
        "edit_distance": approved.edit_distance,
        "ai_confidence": ai_reply.confidence_score if ai_reply else None,
        "intent": ai_reply.intent_detected if ai_reply else None,
        "created_at": approved.created_at,
    } for approved, ticket, ai_reply in results]


def get_correction_detail(
    db: Session,
    tenant_id: int,
    correction_id: int
) -> Optional[Dict]:
    """Get detailed view of a correction with full diff."""
    result = db.query(ApprovedReply, Ticket, AIReply).join(
        Ticket, ApprovedReply.ticket_id == Ticket.id
    ).outerjoin(
        AIReply, ApprovedReply.ai_reply_id == AIReply.id
    ).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.id == correction_id,
        ApprovedReply.is_correction == True
    ).first()

    if not result:
        return None

    approved, ticket, ai_reply = result

    # Generate diff
    diff_lines = []
    if ai_reply:
        edit_analysis = analyze_edit(ai_reply.ai_reply, approved.final_reply)
        diff_lines = edit_analysis.diff_lines

    return {
        "id": approved.id,
        "ticket": {
            "id": ticket.id,
            "whmcs_ticket_id": ticket.whmcs_ticket_id,
            "subject": ticket.subject,
            "content": ticket.content,
            "department": ticket.department,
            "client_email": ticket.client_email,
        },
        "ai_reply": {
            "id": ai_reply.id if ai_reply else None,
            "content": ai_reply.ai_reply if ai_reply else None,
            "confidence_score": ai_reply.confidence_score if ai_reply else None,
            "confidence_breakdown": ai_reply.confidence_breakdown if ai_reply else None,
            "intent_detected": ai_reply.intent_detected if ai_reply else None,
        },
        "corrected_reply": approved.final_reply,
        "edit_summary": approved.edit_summary,
        "edit_distance": approved.edit_distance,
        "diff_lines": diff_lines,
        "created_at": approved.created_at,
    }


def get_corrections_by_intent(db: Session, tenant_id: int) -> Dict[str, int]:
    """Get count of corrections grouped by intent."""
    from sqlalchemy import func

    results = db.query(
        AIReply.intent_detected,
        func.count(ApprovedReply.id)
    ).join(
        ApprovedReply, ApprovedReply.ai_reply_id == AIReply.id
    ).join(
        Ticket, ApprovedReply.ticket_id == Ticket.id
    ).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.is_correction == True
    ).group_by(AIReply.intent_detected).all()

    return {intent or "general": count for intent, count in results}


def get_corrections_stats(db: Session, tenant_id: int) -> Dict:
    """Get statistics about corrections."""
    from sqlalchemy import func

    total = db.query(func.count(ApprovedReply.id)).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.is_correction == True
    ).scalar() or 0

    avg_confidence = db.query(func.avg(AIReply.confidence_score)).join(
        ApprovedReply, ApprovedReply.ai_reply_id == AIReply.id
    ).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.is_correction == True
    ).scalar() or 0

    avg_edit_distance = db.query(func.avg(ApprovedReply.edit_distance)).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.is_correction == True
    ).scalar() or 0

    by_intent = get_corrections_by_intent(db, tenant_id)

    store = get_tenant_store(tenant_id, "corrections")

    return {
        "total_corrections": total,
        "avg_original_confidence": round(avg_confidence, 2),
        "avg_edit_distance": round(avg_edit_distance, 4),
        "by_intent": by_intent,
        "index_chunks": store.count,
    }


def search_similar_corrections(
    tenant_id: int,
    query: str,
    top_k: int = 3
) -> List[Dict]:
    """Search for similar past corrections to warn about potential mistakes."""
    store = get_tenant_store(tenant_id, "corrections")
    results = store.search(query, top_k=top_k)

    return [{
        "content": r[0]["content"],
        "score": r[1],
        "source": r[0].get("source", ""),
        "edit_summary": r[0].get("edit_summary", ""),
        "original_confidence": r[0].get("original_confidence"),
        "intent": r[0].get("intent"),
    } for r in results]
