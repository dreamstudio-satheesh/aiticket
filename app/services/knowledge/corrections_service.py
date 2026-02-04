from typing import List, Dict
from sqlalchemy.orm import Session

from app.models import ApprovedReply, Ticket, AIReply
from app.services.embeddings import get_tenant_store


def index_corrections(db: Session, tenant_id: int) -> int:
    """
    Index corrections (heavily edited AI replies) to avoid repeating mistakes.
    Stores: original AI reply, what was wrong, corrected response.
    """
    store = get_tenant_store(tenant_id, "corrections")
    store.clear()

    # Get approved replies marked as corrections (significant edits)
    corrections = db.query(ApprovedReply, Ticket, AIReply).join(
        Ticket, ApprovedReply.ticket_id == Ticket.id
    ).outerjoin(
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
        # Format: What AI got wrong and how to fix it
        correction_text = f"""Customer Issue: {ticket.subject}
{ticket.content}

INCORRECT Response (Do Not Use):
{ai_reply.ai_reply if ai_reply else 'N/A'}

CORRECT Response:
{approved.final_reply}

Edit Notes: {approved.edit_summary or 'Significant correction made'}"""

        texts.append(correction_text)
        metadata_list.append({
            "source": f"correction_{approved.id}",
            "ticket_id": ticket.id,
            "ai_reply_id": ai_reply.id if ai_reply else None,
            "subject": ticket.subject,
            "edit_distance": approved.edit_distance,
            "type": "correction"
        })

    store.add(texts, metadata_list)
    return len(texts)


def search_corrections(tenant_id: int, query: str, top_k: int = 3) -> List[Dict]:
    """Search corrections to avoid past mistakes."""
    store = get_tenant_store(tenant_id, "corrections")
    results = store.search(query, top_k=top_k)
    return [{
        "content": r[0]["content"],
        "score": r[1],
        "source": r[0].get("source", ""),
        "ticket_id": r[0].get("ticket_id"),
        "type": "correction"
    } for r in results]


def get_corrections_stats(tenant_id: int) -> Dict:
    """Get stats about corrections index."""
    store = get_tenant_store(tenant_id, "corrections")
    return {"total_corrections": store.count}
