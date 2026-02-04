from typing import List, Dict, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models import RerankingConfig
from app.services.knowledge.global_kb_service import search_global_kb
from app.services.knowledge.tenant_kb_service import search_tenant_kb
from app.services.knowledge.examples_service import search_examples
from app.services.knowledge.corrections_service import search_corrections


@dataclass
class RetrievalResult:
    content: str
    score: float
    source: str
    source_type: str  # global_kb, tenant_kb, example, correction
    metadata: Dict


@dataclass
class RetrievalContext:
    """Combined context from all sources for RAG."""
    global_kb: List[RetrievalResult]
    tenant_kb: List[RetrievalResult]
    examples: List[RetrievalResult]
    corrections: List[RetrievalResult]
    merged: List[RetrievalResult]  # Weighted merge


def get_default_weights() -> Dict[str, float]:
    """Default retrieval weights from SRS."""
    return {
        "global_kb": 0.2,
        "tenant_kb": 0.3,
        "examples": 0.35,
        "corrections": 0.15,
    }


def get_tenant_weights(db: Session, tenant_id: int) -> Dict[str, float]:
    """Get tenant-specific weights or defaults."""
    config = db.query(RerankingConfig).filter(
        RerankingConfig.tenant_id == tenant_id
    ).first()

    if config:
        return {
            "global_kb": config.weight_global_kb,
            "tenant_kb": config.weight_tenant_kb,
            "examples": config.weight_approved_examples,
            "corrections": config.weight_corrections,
        }
    return get_default_weights()


def retrieve_context(
    db: Session,
    tenant_id: int,
    query: str,
    top_k: int = 5,
) -> RetrievalContext:
    """
    Retrieve context from all 4 sources and merge with weights.
    """
    weights = get_tenant_weights(db, tenant_id)

    # Search all sources
    global_results = search_global_kb(query, top_k=top_k)
    tenant_results = search_tenant_kb(tenant_id, query, top_k=top_k)
    example_results = search_examples(tenant_id, query, top_k=top_k)
    correction_results = search_corrections(tenant_id, query, top_k=3)

    # Convert to RetrievalResult
    def to_results(items: List[Dict], source_type: str) -> List[RetrievalResult]:
        return [
            RetrievalResult(
                content=item["content"],
                score=item["score"],
                source=item.get("source", ""),
                source_type=source_type,
                metadata=item
            )
            for item in items
        ]

    global_kb = to_results(global_results, "global_kb")
    tenant_kb = to_results(tenant_results, "tenant_kb")
    examples = to_results(example_results, "example")
    corrections = to_results(correction_results, "correction")

    # Weighted merge
    all_results = []
    for result in global_kb:
        result.score *= weights["global_kb"]
        all_results.append(result)
    for result in tenant_kb:
        result.score *= weights["tenant_kb"]
        all_results.append(result)
    for result in examples:
        result.score *= weights["examples"]
        all_results.append(result)
    for result in corrections:
        result.score *= weights["corrections"]
        all_results.append(result)

    # Sort by weighted score and take top_k
    merged = sorted(all_results, key=lambda x: x.score, reverse=True)[:top_k]

    return RetrievalContext(
        global_kb=global_kb,
        tenant_kb=tenant_kb,
        examples=examples,
        corrections=corrections,
        merged=merged
    )


def format_context_for_prompt(context: RetrievalContext) -> str:
    """Format retrieved context for LLM prompt."""
    sections = []

    # Global KB
    if context.global_kb:
        kb_text = "\n\n".join([r.content for r in context.global_kb[:3]])
        sections.append(f"## Hosting Knowledge\n{kb_text}")

    # Tenant KB
    if context.tenant_kb:
        tenant_text = "\n\n".join([r.content for r in context.tenant_kb[:3]])
        sections.append(f"## Company Knowledge\n{tenant_text}")

    # Examples
    if context.examples:
        example_text = "\n\n---\n\n".join([r.content for r in context.examples[:2]])
        sections.append(f"## Similar Past Tickets (Approved Responses)\n{example_text}")

    # Corrections (important to avoid mistakes)
    if context.corrections:
        correction_text = "\n\n---\n\n".join([r.content for r in context.corrections[:2]])
        sections.append(f"## Corrections (Avoid These Mistakes)\n{correction_text}")

    return "\n\n".join(sections)
