from pydantic import BaseModel
from typing import Dict, List
from enum import Enum


class ConfidenceLevelEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class ConfidenceBreakdown(BaseModel):
    example_similarity: float
    kb_similarity: float
    intent_certainty: float
    correction_safety: float
    detected_intent: str


class ConfidenceResponse(BaseModel):
    score: float
    level: ConfidenceLevelEnum
    breakdown: ConfidenceBreakdown
    recommendations: List[str]
    should_escalate: bool


class ConfidenceThresholds(BaseModel):
    auto_reply_threshold: float = 85
    review_threshold: float = 60
    escalation_threshold: float = 40
