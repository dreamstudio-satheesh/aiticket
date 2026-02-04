from pydantic import BaseModel, Field
from typing import Dict, Optional


class WeightsUpdate(BaseModel):
    global_kb: float = Field(ge=0, le=1)
    tenant_kb: float = Field(ge=0, le=1)
    examples: float = Field(ge=0, le=1)
    corrections: float = Field(ge=0, le=1)


class WeightsResponse(BaseModel):
    global_kb: float
    tenant_kb: float
    examples: float
    corrections: float


class SourceEffectiveness(BaseModel):
    total: int
    unedited: int
    effectiveness: float
    avg_score: float


class EffectivenessAnalysis(BaseModel):
    global_kb: Optional[SourceEffectiveness]
    tenant_kb: Optional[SourceEffectiveness]
    example: Optional[SourceEffectiveness]
    correction: Optional[SourceEffectiveness]


class WeightRecommendationResponse(BaseModel):
    weights: WeightsResponse
    reasoning: Dict[str, str]
    confidence: float


class WeightPreset(BaseModel):
    description: str
    weights: WeightsResponse


class ApplyPresetRequest(BaseModel):
    preset: str


class ApplyRecommendationResponse(BaseModel):
    applied: bool
    weights: Optional[WeightsResponse] = None
    reasoning: Optional[Dict[str, str]] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None
