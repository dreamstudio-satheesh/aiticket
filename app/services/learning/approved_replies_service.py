"""Service for managing approved replies and using them for learning."""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from app.models import Ticket, AIReply, ApprovedReply
from app.services.embeddings import get_tenant_store
from app.services.tracking import analyze_edit, track_reply_approval, EditAnalysis


def approve_reply(
    db: Session,
    tenant_id: int,
    user_id: int,
    ticket: Ticket,
    ai_reply: AIReply,
    final_reply: str,
    auto_index: bool = True
) -> tuple[ApprovedReply, EditAnalysis]:
    """
    Approve an AI reply with optional edits.
    Automatically indexes good replies for future learning.
    """
    # Analyze edits
    edit_analysis = analyze_edit(ai_reply.ai_reply, final_reply)

    # Create approved reply
    approved = ApprovedReply(
        ticket_id=ticket.id,
        ai_reply_id=ai_reply.id,
        final_reply=final_reply,
        edited=edit_analysis.was_edited,
        edit_distance=edit_analysis.similarity_ratio,
        is_correction=edit_analysis.is_significant_edit,
        used_for_training=False,
    )
    db.add(approved)
    db.commit()
    db.refresh(approved)

    # Track in audit log
    track_reply_approval(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        ticket=ticket,
        ai_reply=ai_reply,
        approved_reply=approved,
        edit_analysis=edit_analysis
    )

    # Auto-index based on edit significance
    if auto_index:
        if edit_analysis.is_significant_edit:
            # Index as correction to avoid repeating mistakes
            from app.services.learning.corrections_service import add_to_corrections_index
            add_to_corrections_index(db, tenant_id, approved, ticket, ai_reply)
        else:
            # Index as good example for future reference
            add_to_examples_index(db, tenant_id, approved, ticket)

    return approved, edit_analysis


def add_to_examples_index(
    db: Session,
    tenant_id: int,
    approved: ApprovedReply,
    ticket: Ticket
) -> bool:
    """Add a single approved reply to the examples index."""
    store = get_tenant_store(tenant_id, "examples")

    # Format: Question + Approved Answer
    example_text = f"""Customer Issue: {ticket.subject}
{ticket.content}

Approved Response:
{approved.final_reply}"""

    metadata = {
        "source": f"example_{approved.id}",
        "ticket_id": ticket.id,
        "reply_id": approved.id,
        "subject": ticket.subject,
        "department": ticket.department,
        "type": "approved_example",
        "was_edited": approved.edited,
        "similarity_ratio": approved.edit_distance,
    }

    store.add([example_text], [metadata])

    # Mark as used for training
    approved.used_for_training = True
    db.commit()

    return True


def rebuild_examples_index(db: Session, tenant_id: int) -> int:
    """
    Rebuild entire examples index from approved replies.
    Use when index is corrupted or after bulk changes.
    """
    store = get_tenant_store(tenant_id, "examples")
    store.clear()

    # Get all approved replies that aren't corrections
    approved_replies = db.query(ApprovedReply, Ticket).join(
        Ticket, ApprovedReply.ticket_id == Ticket.id
    ).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.is_correction == False
    ).all()

    if not approved_replies:
        return 0

    texts = []
    metadata_list = []

    for approved, ticket in approved_replies:
        example_text = f"""Customer Issue: {ticket.subject}
{ticket.content}

Approved Response:
{approved.final_reply}"""

        texts.append(example_text)
        metadata_list.append({
            "source": f"example_{approved.id}",
            "ticket_id": ticket.id,
            "reply_id": approved.id,
            "subject": ticket.subject,
            "department": ticket.department,
            "type": "approved_example",
            "was_edited": approved.edited,
            "similarity_ratio": approved.edit_distance,
        })

        approved.used_for_training = True

    store.add(texts, metadata_list)
    db.commit()

    return len(texts)


def get_approved_replies(
    db: Session,
    tenant_id: int,
    include_corrections: bool = False,
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """Get approved replies with ticket details."""
    query = db.query(ApprovedReply, Ticket, AIReply).join(
        Ticket, ApprovedReply.ticket_id == Ticket.id
    ).outerjoin(
        AIReply, ApprovedReply.ai_reply_id == AIReply.id
    ).filter(
        Ticket.tenant_id == tenant_id
    )

    if not include_corrections:
        query = query.filter(ApprovedReply.is_correction == False)

    results = query.order_by(ApprovedReply.created_at.desc()).offset(offset).limit(limit).all()

    return [{
        "id": approved.id,
        "ticket_id": ticket.id,
        "ticket_subject": ticket.subject,
        "ticket_content": ticket.content[:200] + "..." if len(ticket.content) > 200 else ticket.content,
        "ai_reply": ai_reply.ai_reply if ai_reply else None,
        "final_reply": approved.final_reply,
        "edited": approved.edited,
        "edit_distance": approved.edit_distance,
        "is_correction": approved.is_correction,
        "used_for_training": approved.used_for_training,
        "ai_confidence": ai_reply.confidence_score if ai_reply else None,
        "created_at": approved.created_at,
    } for approved, ticket, ai_reply in results]


def get_approved_reply_detail(
    db: Session,
    tenant_id: int,
    approved_id: int
) -> Optional[Dict]:
    """Get detailed view of an approved reply."""
    result = db.query(ApprovedReply, Ticket, AIReply).join(
        Ticket, ApprovedReply.ticket_id == Ticket.id
    ).outerjoin(
        AIReply, ApprovedReply.ai_reply_id == AIReply.id
    ).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.id == approved_id
    ).first()

    if not result:
        return None

    approved, ticket, ai_reply = result

    # Generate diff if edited
    diff_lines = []
    if approved.edited and ai_reply:
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
            "priority": ticket.priority,
            "client_email": ticket.client_email,
        },
        "ai_reply": {
            "id": ai_reply.id if ai_reply else None,
            "content": ai_reply.ai_reply if ai_reply else None,
            "confidence_score": ai_reply.confidence_score if ai_reply else None,
            "intent_detected": ai_reply.intent_detected if ai_reply else None,
        },
        "final_reply": approved.final_reply,
        "edited": approved.edited,
        "edit_distance": approved.edit_distance,
        "is_correction": approved.is_correction,
        "used_for_training": approved.used_for_training,
        "diff_lines": diff_lines,
        "created_at": approved.created_at,
    }


def remove_from_training(db: Session, tenant_id: int, approved_id: int) -> bool:
    """Remove an approved reply from training (requires re-index)."""
    result = db.query(ApprovedReply, Ticket).join(
        Ticket, ApprovedReply.ticket_id == Ticket.id
    ).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.id == approved_id
    ).first()

    if not result:
        return False

    approved, ticket = result
    approved.used_for_training = False
    db.commit()

    return True


def mark_as_correction(db: Session, tenant_id: int, approved_id: int) -> bool:
    """Manually mark an approved reply as a correction."""
    result = db.query(ApprovedReply, Ticket).join(
        Ticket, ApprovedReply.ticket_id == Ticket.id
    ).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.id == approved_id
    ).first()

    if not result:
        return False

    approved, ticket = result
    approved.is_correction = True
    approved.used_for_training = False
    db.commit()

    return True


def get_examples_stats(db: Session, tenant_id: int) -> Dict:
    """Get statistics about approved replies and examples."""
    total = db.query(ApprovedReply).join(Ticket).filter(
        Ticket.tenant_id == tenant_id
    ).count()

    indexed = db.query(ApprovedReply).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.used_for_training == True
    ).count()

    corrections = db.query(ApprovedReply).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.is_correction == True
    ).count()

    edited = db.query(ApprovedReply).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.edited == True
    ).count()

    store = get_tenant_store(tenant_id, "examples")

    return {
        "total_approved": total,
        "indexed_examples": indexed,
        "corrections": corrections,
        "edited_replies": edited,
        "edit_rate": round(edited / total, 4) if total > 0 else 0,
        "index_chunks": store.count,
    }
