from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user, require_admin
from app.models import User
from app.schemas.weights import (
    WeightsUpdate, WeightsResponse, EffectivenessAnalysis,
    WeightRecommendationResponse, WeightPreset, ApplyPresetRequest,
    ApplyRecommendationResponse, SourceEffectiveness
)
from app.services.learning.weight_tuning_service import (
    get_current_weights, update_weights, analyze_source_effectiveness,
    recommend_weights, apply_recommended_weights, get_weight_presets
)

router = APIRouter(prefix="/weights", tags=["Retrieval Weights"])


@router.get("/", response_model=WeightsResponse)
def get_weights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current retrieval weights for tenant."""
    weights = get_current_weights(db, current_user.tenant_id)
    return WeightsResponse(**weights)


@router.put("/", response_model=WeightsResponse)
def set_weights(
    weights: WeightsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update retrieval weights (Admin only). Weights are normalized to sum to 1.0."""
    weights_dict = weights.model_dump()
    config = update_weights(db, current_user.tenant_id, weights_dict)
    return WeightsResponse(
        global_kb=config.weight_global_kb,
        tenant_kb=config.weight_tenant_kb,
        examples=config.weight_approved_examples,
        corrections=config.weight_corrections,
    )


@router.get("/effectiveness", response_model=EffectivenessAnalysis)
def get_effectiveness(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze effectiveness of each context source type."""
    analysis = analyze_source_effectiveness(db, current_user.tenant_id, days)

    def to_response(data: Dict) -> SourceEffectiveness:
        return SourceEffectiveness(
            total=data.get("total", 0),
            unedited=data.get("unedited", 0),
            effectiveness=data.get("effectiveness", 0),
            avg_score=data.get("avg_score", 0),
        )

    return EffectivenessAnalysis(
        global_kb=to_response(analysis.get("global_kb", {})) if analysis.get("global_kb") else None,
        tenant_kb=to_response(analysis.get("tenant_kb", {})) if analysis.get("tenant_kb") else None,
        example=to_response(analysis.get("example", {})) if analysis.get("example") else None,
        correction=to_response(analysis.get("correction", {})) if analysis.get("correction") else None,
    )


@router.get("/recommend", response_model=WeightRecommendationResponse)
def get_recommendation(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recommended weights based on historical performance."""
    rec = recommend_weights(db, current_user.tenant_id, days)
    return WeightRecommendationResponse(
        weights=WeightsResponse(**rec.weights),
        reasoning=rec.reasoning,
        confidence=rec.confidence,
    )


@router.post("/apply-recommendation", response_model=ApplyRecommendationResponse)
def apply_recommendation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Apply auto-recommended weights (Admin only). Requires minimum confidence."""
    result = apply_recommended_weights(db, current_user.tenant_id)

    if result.get("applied"):
        return ApplyRecommendationResponse(
            applied=True,
            weights=WeightsResponse(**result["weights"]),
            reasoning=result["reasoning"],
            confidence=result["confidence"],
        )
    else:
        return ApplyRecommendationResponse(
            applied=False,
            reason=result.get("reason"),
        )


@router.get("/presets", response_model=Dict[str, WeightPreset])
def list_presets():
    """Get available weight presets."""
    presets = get_weight_presets()
    return {
        name: WeightPreset(
            description=preset["description"],
            weights=WeightsResponse(**preset["weights"])
        )
        for name, preset in presets.items()
    }


@router.post("/apply-preset", response_model=WeightsResponse)
def apply_preset(
    request: ApplyPresetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Apply a weight preset (Admin only)."""
    presets = get_weight_presets()

    if request.preset not in presets:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown preset. Available: {list(presets.keys())}"
        )

    weights = presets[request.preset]["weights"]
    config = update_weights(db, current_user.tenant_id, weights)

    return WeightsResponse(
        global_kb=config.weight_global_kb,
        tenant_kb=config.weight_tenant_kb,
        examples=config.weight_approved_examples,
        corrections=config.weight_corrections,
    )
