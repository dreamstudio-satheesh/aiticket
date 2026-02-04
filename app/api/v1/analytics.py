from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user, require_admin
from app.models import User
from app.schemas.analytics import (
    EditMetricsResponse, ConfidenceAccuracyResponse,
    AuditLogResponse, DailyStatsResponse, AnalyticsDashboard
)
from app.services.tracking import (
    get_edit_metrics, get_confidence_accuracy,
    get_intent_performance, get_daily_stats,
    get_edit_history, get_correction_history
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=AnalyticsDashboard)
def get_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get full analytics dashboard data."""
    tenant_id = current_user.tenant_id

    metrics = get_edit_metrics(db, tenant_id, days)
    confidence = get_confidence_accuracy(db, tenant_id, days)
    intent_perf = get_intent_performance(db, tenant_id, days)
    daily = get_daily_stats(db, tenant_id, min(days, 30))

    return AnalyticsDashboard(
        metrics=EditMetricsResponse(
            total_drafts=metrics.total_drafts,
            total_approved=metrics.total_approved,
            approval_rate=round(metrics.approval_rate, 4),
            edited_count=metrics.edited_count,
            edit_rate=round(metrics.edit_rate, 4),
            correction_count=metrics.correction_count,
            correction_rate=round(metrics.correction_rate, 4),
            avg_confidence=metrics.avg_confidence,
            avg_similarity=metrics.avg_similarity,
            avg_latency_ms=metrics.avg_latency_ms,
        ),
        confidence_accuracy=ConfidenceAccuracyResponse(
            high_confidence_edit_rate=round(confidence.high_confidence_edit_rate, 4),
            medium_confidence_edit_rate=round(confidence.medium_confidence_edit_rate, 4),
            low_confidence_edit_rate=round(confidence.low_confidence_edit_rate, 4),
            avg_confidence_edited=confidence.avg_confidence_edited,
            avg_confidence_unedited=confidence.avg_confidence_unedited,
        ),
        intent_performance=intent_perf,
        daily_stats=[DailyStatsResponse(**d) for d in daily],
    )


@router.get("/metrics", response_model=EditMetricsResponse)
def get_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get edit metrics for time period."""
    metrics = get_edit_metrics(db, current_user.tenant_id, days)
    return EditMetricsResponse(
        total_drafts=metrics.total_drafts,
        total_approved=metrics.total_approved,
        approval_rate=round(metrics.approval_rate, 4),
        edited_count=metrics.edited_count,
        edit_rate=round(metrics.edit_rate, 4),
        correction_count=metrics.correction_count,
        correction_rate=round(metrics.correction_rate, 4),
        avg_confidence=metrics.avg_confidence,
        avg_similarity=metrics.avg_similarity,
        avg_latency_ms=metrics.avg_latency_ms,
    )


@router.get("/confidence", response_model=ConfidenceAccuracyResponse)
def get_confidence_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get confidence accuracy analysis."""
    conf = get_confidence_accuracy(db, current_user.tenant_id, days)
    return ConfidenceAccuracyResponse(
        high_confidence_edit_rate=round(conf.high_confidence_edit_rate, 4),
        medium_confidence_edit_rate=round(conf.medium_confidence_edit_rate, 4),
        low_confidence_edit_rate=round(conf.low_confidence_edit_rate, 4),
        avg_confidence_edited=conf.avg_confidence_edited,
        avg_confidence_unedited=conf.avg_confidence_unedited,
    )


@router.get("/history", response_model=List[AuditLogResponse])
def get_audit_history(
    ticket_id: int = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get edit history audit log."""
    logs = get_edit_history(db, current_user.tenant_id, ticket_id, limit)
    return [AuditLogResponse(
        id=log.id,
        action=log.action.value,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        ticket_id=log.ticket_id,
        details=log.details or {},
        created_at=log.created_at,
    ) for log in logs]


@router.get("/corrections", response_model=List[AuditLogResponse])
def get_corrections(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get correction history for learning analysis."""
    logs = get_correction_history(db, current_user.tenant_id, limit)
    return [AuditLogResponse(
        id=log.id,
        action=log.action.value,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        ticket_id=log.ticket_id,
        details=log.details or {},
        created_at=log.created_at,
    ) for log in logs]
