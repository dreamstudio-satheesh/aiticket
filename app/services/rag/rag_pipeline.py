from typing import Dict, Optional, List
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models import Ticket, PromptVersion, RerankingConfig
from app.services.knowledge import retrieve_context, format_context_for_prompt, RetrievalContext
from app.services.llm import generate_completion, rerank_results
from app.services.confidence import calculate_confidence, ConfidenceResult, ConfidenceLevel


@dataclass
class RAGResponse:
    """Response from RAG pipeline."""
    reply: str
    confidence_score: float
    confidence_level: ConfidenceLevel
    confidence_breakdown: Dict[str, float]
    recommendations: List[str]
    should_escalate: bool
    context: RetrievalContext
    reranked_sources: List[Dict]
    intent_detected: str
    tokens_used: int
    latency_ms: int
    prompt_version_id: Optional[int]


def get_active_prompt(db: Session, tenant_id: int) -> Optional[PromptVersion]:
    """Get active prompt version for tenant, or global default."""
    prompt = db.query(PromptVersion).filter(
        PromptVersion.tenant_id == tenant_id,
        PromptVersion.is_active == True
    ).first()

    if not prompt:
        prompt = db.query(PromptVersion).filter(
            PromptVersion.tenant_id == None,
            PromptVersion.is_default == True
        ).first()

    return prompt


def get_reranking_config(db: Session, tenant_id: int) -> Optional[RerankingConfig]:
    """Get reranking config for tenant."""
    return db.query(RerankingConfig).filter(
        RerankingConfig.tenant_id == tenant_id
    ).first()


def build_prompt(
    ticket: Ticket,
    context: RetrievalContext,
    prompt_version: Optional[PromptVersion] = None
) -> tuple[str, str]:
    """Build system and user prompts for LLM."""

    if prompt_version:
        system_prompt = prompt_version.system_prompt
        context_template = prompt_version.context_template
        task_template = prompt_version.task_template
    else:
        system_prompt = """You are a professional hosting support assistant. Your role is to help draft accurate, helpful support ticket replies.

Guidelines:
- Be professional and friendly
- Provide specific, actionable steps when possible
- If you're unsure about company-specific policies, say so
- Never guess at technical details you don't know
- Suggest escalation if the issue is complex or outside your knowledge"""

        context_template = """## Retrieved Context
{context}"""

        task_template = """## Customer Ticket
Subject: {subject}
Department: {department}

{content}

---

Please draft a professional support reply for this ticket. Use the context provided above when relevant."""

    formatted_context = format_context_for_prompt(context)
    context_section = context_template.format(context=formatted_context)

    user_prompt = f"{context_section}\n\n{task_template.format(subject=ticket.subject, department=ticket.department or 'General', priority=ticket.priority or 'Normal', content=ticket.content)}"

    return system_prompt, user_prompt


def generate_reply(
    db: Session,
    ticket: Ticket,
    top_k: int = 5,
    use_reranking: bool = True,
) -> RAGResponse:
    """
    Main RAG pipeline: retrieve context, rerank, generate reply with confidence scoring.
    """
    tenant_id = ticket.tenant_id

    # 1. Retrieve context from all sources
    query = f"{ticket.subject} {ticket.content}"
    context = retrieve_context(db, tenant_id, query, top_k=top_k * 2)

    # 2. Optional reranking
    reranked_sources = []
    reranking_config = get_reranking_config(db, tenant_id)

    if use_reranking and reranking_config and reranking_config.is_enabled:
        reranked = rerank_results(
            query,
            context.merged,
            top_k=reranking_config.top_k_rerank,
            score_threshold=reranking_config.score_threshold
        )
        reranked_sources = [{"content": r.content, "score": r.score, "source": r.source} for r in reranked]
        context.merged = reranked

    # 3. Calculate confidence (includes intent detection)
    confidence_result: ConfidenceResult = calculate_confidence(
        context=context,
        ticket_content=ticket.content
    )

    # 4. Get active prompt version
    prompt_version = get_active_prompt(db, tenant_id)

    # 5. Build prompts
    system_prompt, user_prompt = build_prompt(ticket, context, prompt_version)

    # 6. Generate reply
    model = prompt_version.model if prompt_version else "gpt-4o-mini"
    temperature = (prompt_version.temperature / 10) if prompt_version else 0.3
    max_tokens = prompt_version.max_tokens if prompt_version else 1000

    llm_response = generate_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return RAGResponse(
        reply=llm_response["content"],
        confidence_score=confidence_result.score,
        confidence_level=confidence_result.level,
        confidence_breakdown=confidence_result.breakdown,
        recommendations=confidence_result.recommendations,
        should_escalate=confidence_result.should_escalate,
        context=context,
        reranked_sources=reranked_sources,
        intent_detected=confidence_result.breakdown.get("detected_intent", "general"),
        tokens_used=llm_response["tokens_used"],
        latency_ms=llm_response["latency_ms"],
        prompt_version_id=prompt_version.id if prompt_version else None,
    )
