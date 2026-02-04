from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class EditMetricsResponse(BaseModel):
    total_drafts: int
    total_approved: int
    approval_rate: float
    edited_count: int
    edit_rate: float
    correction_count: int
    correction_rate: float
    avg_confidence: float
    avg_similarity: float
    avg_latency_ms: float


class ConfidenceAccuracyResponse(BaseModel):
    high_confidence_edit_rate: float
    medium_confidence_edit_rate: float
    low_confidence_edit_rate: float
    avg_confidence_edited: float
    avg_confidence_unedited: float


class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[int]
    ticket_id: Optional[int]
    details: Dict
    created_at: datetime

    class Config:
        from_attributes = True


class DailyStatsResponse(BaseModel):
    date: str
    drafts_generated: int
    replies_approved: int
    replies_edited: int


class AnalyticsDashboard(BaseModel):
    metrics: EditMetricsResponse
    confidence_accuracy: ConfidenceAccuracyResponse
    intent_performance: Dict[str, Dict]
    daily_stats: List[DailyStatsResponse]
