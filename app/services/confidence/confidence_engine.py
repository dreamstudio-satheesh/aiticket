"""
Confidence Scoring Engine

Formula from SRS:
confidence = 0.4 × example_similarity + 0.3 × KB_similarity + 0.2 × intent_certainty + 0.1 × correction_safety

Score range: 0-100
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from app.services.knowledge.unified_retrieval import RetrievalContext


class ConfidenceLevel(str, Enum):
    """Confidence levels for decision making."""
    HIGH = "high"          # 80-100: Can auto-reply (future)
    MEDIUM = "medium"      # 60-79: Good draft, minor review
    LOW = "low"            # 40-59: Needs careful review
    VERY_LOW = "very_low"  # 0-39: Likely needs escalation


@dataclass
class ConfidenceResult:
    """Detailed confidence scoring result."""
    score: float  # 0-100
    level: ConfidenceLevel
    breakdown: Dict[str, float]
    recommendations: List[str]
    should_escalate: bool


# Intent patterns with confidence weights
INTENT_PATTERNS = {
    "billing": {
        "keywords": ["invoice", "payment", "charge", "refund", "bill", "price", "cost", "renew", "cancel subscription"],
        "confidence": 0.85,
        "requires_tenant_kb": True,
    },
    "email": {
        "keywords": ["email", "mail", "smtp", "imap", "inbox", "spam", "sending", "receiving", "outlook", "thunderbird"],
        "confidence": 0.80,
        "requires_tenant_kb": False,
    },
    "website_error": {
        "keywords": ["500 error", "503", "404", "website down", "site not loading", "internal server error", "white screen"],
        "confidence": 0.75,
        "requires_tenant_kb": False,
    },
    "website_slow": {
        "keywords": ["slow", "loading time", "performance", "speed", "timeout"],
        "confidence": 0.70,
        "requires_tenant_kb": False,
    },
    "dns": {
        "keywords": ["dns", "domain", "nameserver", "propagation", "mx record", "a record", "cname", "pointing"],
        "confidence": 0.80,
        "requires_tenant_kb": False,
    },
    "ssl": {
        "keywords": ["ssl", "https", "certificate", "secure", "let's encrypt", "not secure", "expired cert"],
        "confidence": 0.85,
        "requires_tenant_kb": False,
    },
    "database": {
        "keywords": ["database", "mysql", "sql", "phpmyadmin", "connection error", "db error"],
        "confidence": 0.75,
        "requires_tenant_kb": False,
    },
    "ftp": {
        "keywords": ["ftp", "sftp", "filezilla", "upload", "file manager", "connection refused"],
        "confidence": 0.80,
        "requires_tenant_kb": False,
    },
    "cpanel": {
        "keywords": ["cpanel", "control panel", "whm", "can't login", "cpanel access"],
        "confidence": 0.75,
        "requires_tenant_kb": False,
    },
    "suspension": {
        "keywords": ["suspended", "suspension", "disabled", "blocked", "account locked", "terminated"],
        "confidence": 0.70,
        "requires_tenant_kb": True,
    },
    "upgrade": {
        "keywords": ["upgrade", "plan", "more resources", "more space", "bandwidth limit", "disk full"],
        "confidence": 0.75,
        "requires_tenant_kb": True,
    },
    "malware": {
        "keywords": ["hacked", "malware", "virus", "compromised", "phishing", "spam sending"],
        "confidence": 0.60,  # Lower - often needs escalation
        "requires_tenant_kb": False,
    },
    "migration": {
        "keywords": ["migrate", "transfer", "move", "backup", "restore", "import"],
        "confidence": 0.65,
        "requires_tenant_kb": True,
    },
}


def detect_intent_with_confidence(content: str) -> Tuple[str, float, bool]:
    """
    Detect intent from ticket content with confidence score.
    Returns: (intent, confidence, requires_tenant_kb)
    """
    content_lower = content.lower()

    best_match = ("general", 0.5, False)
    best_keyword_count = 0

    for intent, config in INTENT_PATTERNS.items():
        keyword_count = sum(1 for kw in config["keywords"] if kw in content_lower)
        if keyword_count > best_keyword_count:
            best_keyword_count = keyword_count
            best_match = (intent, config["confidence"], config["requires_tenant_kb"])

    # Boost confidence if multiple keywords matched
    intent, base_confidence, requires_kb = best_match
    if best_keyword_count >= 3:
        base_confidence = min(base_confidence + 0.1, 0.95)
    elif best_keyword_count >= 2:
        base_confidence = min(base_confidence + 0.05, 0.90)

    return intent, base_confidence, requires_kb


def calculate_example_score(context: RetrievalContext) -> float:
    """
    Calculate example similarity component.
    High score if we have good matching examples.
    """
    if not context.examples:
        return 0.0

    # Best example score
    best_score = max(r.score for r in context.examples)

    # Boost if multiple good examples
    good_examples = [r for r in context.examples if r.score > 0.5]
    if len(good_examples) >= 2:
        best_score = min(best_score * 1.1, 1.0)

    return best_score


def calculate_kb_score(context: RetrievalContext, requires_tenant_kb: bool) -> float:
    """
    Calculate KB similarity component.
    Considers both global and tenant KB.
    """
    global_scores = [r.score for r in context.global_kb] if context.global_kb else [0]
    tenant_scores = [r.score for r in context.tenant_kb] if context.tenant_kb else [0]

    best_global = max(global_scores)
    best_tenant = max(tenant_scores)

    # If intent requires tenant KB but none found, penalize
    if requires_tenant_kb and best_tenant < 0.3:
        return best_global * 0.6  # Significant penalty

    # Weighted combination favoring tenant KB
    return (best_tenant * 0.6 + best_global * 0.4)


def calculate_correction_safety(context: RetrievalContext) -> float:
    """
    Calculate correction safety component.
    Lower score if similar corrections exist (we've made mistakes here before).
    """
    if not context.corrections:
        return 1.0  # No corrections = safe

    # If high-scoring corrections exist, reduce safety
    best_correction_score = max(r.score for r in context.corrections)

    if best_correction_score > 0.8:
        return 0.4  # Very similar to past mistake
    elif best_correction_score > 0.6:
        return 0.6  # Somewhat similar
    elif best_correction_score > 0.4:
        return 0.8  # Slightly similar
    else:
        return 0.95  # Not very similar


def calculate_confidence(
    context: RetrievalContext,
    ticket_content: str,
    weights: Optional[Dict[str, float]] = None
) -> ConfidenceResult:
    """
    Calculate comprehensive confidence score.

    Default weights from SRS:
    - example_similarity: 0.4
    - kb_similarity: 0.3
    - intent_certainty: 0.2
    - correction_safety: 0.1
    """
    if weights is None:
        weights = {
            "example_similarity": 0.4,
            "kb_similarity": 0.3,
            "intent_certainty": 0.2,
            "correction_safety": 0.1,
        }

    # Detect intent
    intent, intent_confidence, requires_tenant_kb = detect_intent_with_confidence(ticket_content)

    # Calculate components
    example_score = calculate_example_score(context)
    kb_score = calculate_kb_score(context, requires_tenant_kb)
    intent_score = intent_confidence
    correction_safety = calculate_correction_safety(context)

    # Weighted sum
    raw_score = (
        weights["example_similarity"] * example_score +
        weights["kb_similarity"] * kb_score +
        weights["intent_certainty"] * intent_score +
        weights["correction_safety"] * correction_safety
    )

    # Convert to 0-100 scale
    score = round(raw_score * 100, 2)

    # Determine level
    if score >= 80:
        level = ConfidenceLevel.HIGH
    elif score >= 60:
        level = ConfidenceLevel.MEDIUM
    elif score >= 40:
        level = ConfidenceLevel.LOW
    else:
        level = ConfidenceLevel.VERY_LOW

    # Generate recommendations
    recommendations = []
    should_escalate = False

    if example_score < 0.3:
        recommendations.append("No similar past tickets found - review carefully")

    if kb_score < 0.3:
        recommendations.append("Limited knowledge base matches - verify accuracy")

    if requires_tenant_kb and not context.tenant_kb:
        recommendations.append("This topic may require company-specific information")

    if correction_safety < 0.7:
        recommendations.append("Similar issues had corrections before - check for past mistakes")
        should_escalate = True

    if intent == "malware":
        recommendations.append("Security issue - consider escalation to senior staff")
        should_escalate = True

    if score < 40:
        recommendations.append("Low confidence - recommend manual review or escalation")
        should_escalate = True

    breakdown = {
        "example_similarity": round(example_score * 100, 2),
        "kb_similarity": round(kb_score * 100, 2),
        "intent_certainty": round(intent_score * 100, 2),
        "correction_safety": round(correction_safety * 100, 2),
        "detected_intent": intent,
    }

    return ConfidenceResult(
        score=score,
        level=level,
        breakdown=breakdown,
        recommendations=recommendations,
        should_escalate=should_escalate,
    )


def get_confidence_thresholds() -> Dict[str, float]:
    """Get configurable confidence thresholds."""
    return {
        "auto_reply_threshold": 85,     # Future: auto-send above this
        "review_threshold": 60,          # Needs quick review
        "escalation_threshold": 40,      # Should escalate below this
    }
