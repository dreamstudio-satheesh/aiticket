"""Service for tuning retrieval weights based on learning patterns."""

from typing import Dict, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import RerankingConfig, AIReply, ApprovedReply, Ticket


@dataclass
class WeightRecommendation:
    """Recommended weights based on performance analysis."""
    weights: Dict[str, float]
    reasoning: Dict[str, str]
    confidence: float  # How confident we are in these recommendations


def get_current_weights(db: Session, tenant_id: int) -> Dict[str, float]:
    """Get current weights for tenant."""
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

    # Default weights from SRS
    return {
        "global_kb": 0.2,
        "tenant_kb": 0.3,
        "examples": 0.35,
        "corrections": 0.15,
    }


def update_weights(
    db: Session,
    tenant_id: int,
    weights: Dict[str, float]
) -> RerankingConfig:
    """Update retrieval weights for tenant."""
    # Validate weights sum to 1.0
    total = sum(weights.values())
    if abs(total - 1.0) > 0.01:
        # Normalize
        weights = {k: v / total for k, v in weights.items()}

    config = db.query(RerankingConfig).filter(
        RerankingConfig.tenant_id == tenant_id
    ).first()

    if not config:
        config = RerankingConfig(tenant_id=tenant_id)
        db.add(config)

    config.weight_global_kb = weights.get("global_kb", 0.2)
    config.weight_tenant_kb = weights.get("tenant_kb", 0.3)
    config.weight_approved_examples = weights.get("examples", 0.35)
    config.weight_corrections = weights.get("corrections", 0.15)

    db.commit()
    db.refresh(config)
    return config


def analyze_source_effectiveness(db: Session, tenant_id: int, days: int = 30) -> Dict[str, Dict]:
    """
    Analyze which context sources lead to better (less edited) replies.
    Returns effectiveness metrics per source type.
    """
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(days=days)

    # Get all approved replies with their AI replies
    results = db.query(AIReply, ApprovedReply).join(
        ApprovedReply, ApprovedReply.ai_reply_id == AIReply.id
    ).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.created_at >= since
    ).all()

    if not results:
        return {}

    # Analyze context sources vs edit outcomes
    source_stats = {
        "global_kb": {"total": 0, "unedited": 0, "avg_score": 0, "scores": []},
        "tenant_kb": {"total": 0, "unedited": 0, "avg_score": 0, "scores": []},
        "example": {"total": 0, "unedited": 0, "avg_score": 0, "scores": []},
        "correction": {"total": 0, "unedited": 0, "avg_score": 0, "scores": []},
    }

    for ai_reply, approved in results:
        context_sources = ai_reply.context_sources or []
        was_unedited = not approved.edited

        # Track which source types were present and their scores
        source_types_present = set()
        for source in context_sources:
            source_type = source.get("type", "unknown")
            score = source.get("score", 0)

            if source_type in source_stats:
                source_stats[source_type]["scores"].append(score)
                source_types_present.add(source_type)

        # Credit sources that were present in unedited replies
        for source_type in source_types_present:
            source_stats[source_type]["total"] += 1
            if was_unedited:
                source_stats[source_type]["unedited"] += 1

    # Calculate effectiveness rates
    for source_type, stats in source_stats.items():
        if stats["total"] > 0:
            stats["effectiveness"] = stats["unedited"] / stats["total"]
        else:
            stats["effectiveness"] = 0

        if stats["scores"]:
            stats["avg_score"] = sum(stats["scores"]) / len(stats["scores"])

        del stats["scores"]  # Remove raw scores from output

    return source_stats


def recommend_weights(db: Session, tenant_id: int, days: int = 30) -> WeightRecommendation:
    """
    Recommend optimal weights based on historical performance.
    Higher effectiveness = higher weight.
    """
    source_effectiveness = analyze_source_effectiveness(db, tenant_id, days)

    if not source_effectiveness:
        # No data, return defaults
        return WeightRecommendation(
            weights={
                "global_kb": 0.2,
                "tenant_kb": 0.3,
                "examples": 0.35,
                "corrections": 0.15,
            },
            reasoning={
                "global_kb": "Default - no data available",
                "tenant_kb": "Default - no data available",
                "examples": "Default - no data available",
                "corrections": "Default - no data available",
            },
            confidence=0.0
        )

    # Calculate recommended weights based on effectiveness
    # Higher effectiveness = higher weight
    # But keep corrections with minimum weight (they prevent mistakes)

    effectiveness = {
        "global_kb": source_effectiveness.get("global_kb", {}).get("effectiveness", 0.5),
        "tenant_kb": source_effectiveness.get("tenant_kb", {}).get("effectiveness", 0.5),
        "examples": source_effectiveness.get("example", {}).get("effectiveness", 0.5),
        "corrections": source_effectiveness.get("correction", {}).get("effectiveness", 0.5),
    }

    total_samples = sum(
        source_effectiveness.get(st, {}).get("total", 0)
        for st in ["global_kb", "tenant_kb", "example", "correction"]
    )

    # Base weights on effectiveness, but apply constraints
    raw_weights = {}
    reasoning = {}

    for source, eff in effectiveness.items():
        base_weight = max(0.1, eff)  # Minimum 10%
        raw_weights[source] = base_weight

        sample_count = source_effectiveness.get(
            "example" if source == "examples" else source, {}
        ).get("total", 0)

        reasoning[source] = f"Effectiveness: {eff:.1%} based on {sample_count} samples"

    # Ensure corrections have minimum weight (prevent mistakes)
    if raw_weights["corrections"] < 0.1:
        raw_weights["corrections"] = 0.1
        reasoning["corrections"] += " (boosted to minimum 10%)"

    # Ensure examples are prioritized if effective
    if effectiveness["examples"] > 0.7 and raw_weights["examples"] < 0.3:
        raw_weights["examples"] = 0.35
        reasoning["examples"] += " (boosted due to high effectiveness)"

    # Normalize to sum to 1.0
    total = sum(raw_weights.values())
    weights = {k: round(v / total, 2) for k, v in raw_weights.items()}

    # Adjust for rounding
    diff = 1.0 - sum(weights.values())
    weights["examples"] = round(weights["examples"] + diff, 2)

    # Calculate confidence based on sample size
    confidence = min(1.0, total_samples / 100)  # 100 samples = full confidence

    return WeightRecommendation(
        weights=weights,
        reasoning=reasoning,
        confidence=round(confidence, 2)
    )


def apply_recommended_weights(db: Session, tenant_id: int) -> Dict:
    """Apply auto-recommended weights."""
    recommendation = recommend_weights(db, tenant_id)

    if recommendation.confidence < 0.3:
        return {
            "applied": False,
            "reason": "Insufficient data for confident recommendation",
            "current_confidence": recommendation.confidence,
            "min_required": 0.3,
        }

    update_weights(db, tenant_id, recommendation.weights)

    return {
        "applied": True,
        "weights": recommendation.weights,
        "reasoning": recommendation.reasoning,
        "confidence": recommendation.confidence,
    }


def get_weight_presets() -> Dict[str, Dict[str, float]]:
    """Get predefined weight presets for different scenarios."""
    return {
        "default": {
            "description": "Balanced weights from SRS specification",
            "weights": {
                "global_kb": 0.2,
                "tenant_kb": 0.3,
                "examples": 0.35,
                "corrections": 0.15,
            }
        },
        "examples_heavy": {
            "description": "Prioritize past approved replies (good for established tenants)",
            "weights": {
                "global_kb": 0.15,
                "tenant_kb": 0.2,
                "examples": 0.5,
                "corrections": 0.15,
            }
        },
        "kb_heavy": {
            "description": "Prioritize knowledge base (good for new tenants with few examples)",
            "weights": {
                "global_kb": 0.25,
                "tenant_kb": 0.4,
                "examples": 0.2,
                "corrections": 0.15,
            }
        },
        "safety_first": {
            "description": "Higher weight on corrections (good after many mistakes)",
            "weights": {
                "global_kb": 0.15,
                "tenant_kb": 0.25,
                "examples": 0.3,
                "corrections": 0.3,
            }
        },
    }
