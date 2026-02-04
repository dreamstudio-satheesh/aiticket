from typing import List, Dict
from sqlalchemy.orm import Session

from app.models import ApprovedReply, Ticket
from app.services.embeddings import get_tenant_store


def index_approved_examples(db: Session, tenant_id: int) -> int:
    """
    Index approved replies as examples for future RAG retrieval.
    Only includes non-edited or lightly edited replies (good AI outputs).
    """
    store = get_tenant_store(tenant_id, "examples")
    store.clear()

    # Get approved replies that weren't heavily edited
    approved = db.query(ApprovedReply, Ticket).join(
        Ticket, ApprovedReply.ticket_id == Ticket.id
    ).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.is_correction == False  # Not marked as correction
    ).all()

    if not approved:
        return 0

    texts = []
    metadata_list = []

    for reply, ticket in approved:
        # Format: Question + Approved Answer
        example_text = f"Customer Issue: {ticket.subject}\n{ticket.content}\n\nApproved Response:\n{reply.final_reply}"

        texts.append(example_text)
        metadata_list.append({
            "source": f"example_{reply.id}",
            "ticket_id": ticket.id,
            "reply_id": reply.id,
            "subject": ticket.subject,
            "department": ticket.department,
            "type": "approved_example"
        })

    store.add(texts, metadata_list)
    return len(texts)


def search_examples(tenant_id: int, query: str, top_k: int = 5) -> List[Dict]:
    """Search approved examples for similar past tickets."""
    store = get_tenant_store(tenant_id, "examples")
    results = store.search(query, top_k=top_k)
    return [{
        "content": r[0]["content"],
        "score": r[1],
        "source": r[0].get("source", ""),
        "ticket_id": r[0].get("ticket_id"),
        "subject": r[0].get("subject"),
        "type": "example"
    } for r in results]


def get_examples_stats(tenant_id: int) -> Dict:
    """Get stats about examples index."""
    store = get_tenant_store(tenant_id, "examples")
    return {"total_examples": store.count}
