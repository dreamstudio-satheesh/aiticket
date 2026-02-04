"""Analytics service for tracking AI performance and edit patterns."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import AIReply, ApprovedReply, Ticket
from app.models.audit_log import AuditLog, AuditAction


@dataclass
class EditMetrics:
    """Aggregate edit metrics for a time period."""
    total_drafts: int
    total_approved: int
    approval_rate: float  # approved / drafts
    edited_count: int
    edit_rate: float  # edited / approved
    correction_count: int
    correction_rate: float  # corrections / approved
    avg_confidence: float
    avg_similarity: float  # How similar approved replies are to drafts
    avg_latency_ms: float


@dataclass
class ConfidenceAccuracy:
    """Analysis of confidence score accuracy."""
    high_confidence_edit_rate: float  # Edits when confidence >= 80
    medium_confidence_edit_rate: float  # Edits when 60 <= confidence < 80
    low_confidence_edit_rate: float  # Edits when confidence < 60
    avg_confidence_edited: float  # Avg confidence of edited replies
    avg_confidence_unedited: float  # Avg confidence of unedited replies


def get_edit_metrics(
    db: Session,
    tenant_id: int,
    days: int = 30
) -> EditMetrics:
    """Get aggregate edit metrics for last N days."""
    since = datetime.utcnow() - timedelta(days=days)

    # Total drafts generated
    total_drafts = db.query(func.count(AIReply.id)).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        AIReply.created_at >= since
    ).scalar() or 0

    # Total approved
    total_approved = db.query(func.count(ApprovedReply.id)).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.created_at >= since
    ).scalar() or 0

    # Edited count
    edited_count = db.query(func.count(ApprovedReply.id)).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.created_at >= since,
        ApprovedReply.edited == True
    ).scalar() or 0

    # Correction count
    correction_count = db.query(func.count(ApprovedReply.id)).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.created_at >= since,
        ApprovedReply.is_correction == True
    ).scalar() or 0

    # Average confidence
    avg_confidence = db.query(func.avg(AIReply.confidence_score)).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        AIReply.created_at >= since
    ).scalar() or 0

    # Average similarity (edit distance)
    avg_similarity = db.query(func.avg(ApprovedReply.edit_distance)).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.created_at >= since
    ).scalar() or 1.0

    # Average latency
    avg_latency = db.query(func.avg(AIReply.latency_ms)).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        AIReply.created_at >= since
    ).scalar() or 0

    return EditMetrics(
        total_drafts=total_drafts,
        total_approved=total_approved,
        approval_rate=total_approved / total_drafts if total_drafts > 0 else 0,
        edited_count=edited_count,
        edit_rate=edited_count / total_approved if total_approved > 0 else 0,
        correction_count=correction_count,
        correction_rate=correction_count / total_approved if total_approved > 0 else 0,
        avg_confidence=round(avg_confidence, 2),
        avg_similarity=round(avg_similarity, 4),
        avg_latency_ms=round(avg_latency, 0),
    )


def get_confidence_accuracy(
    db: Session,
    tenant_id: int,
    days: int = 30
) -> ConfidenceAccuracy:
    """Analyze how well confidence scores predict edit likelihood."""
    since = datetime.utcnow() - timedelta(days=days)

    def get_edit_rate_for_confidence_range(min_conf: float, max_conf: float) -> float:
        total = db.query(func.count(ApprovedReply.id)).join(
            AIReply, ApprovedReply.ai_reply_id == AIReply.id
        ).join(Ticket).filter(
            Ticket.tenant_id == tenant_id,
            ApprovedReply.created_at >= since,
            AIReply.confidence_score >= min_conf,
            AIReply.confidence_score < max_conf
        ).scalar() or 0

        edited = db.query(func.count(ApprovedReply.id)).join(
            AIReply, ApprovedReply.ai_reply_id == AIReply.id
        ).join(Ticket).filter(
            Ticket.tenant_id == tenant_id,
            ApprovedReply.created_at >= since,
            AIReply.confidence_score >= min_conf,
            AIReply.confidence_score < max_conf,
            ApprovedReply.edited == True
        ).scalar() or 0

        return edited / total if total > 0 else 0

    # Average confidence for edited vs unedited
    avg_conf_edited = db.query(func.avg(AIReply.confidence_score)).join(
        ApprovedReply, ApprovedReply.ai_reply_id == AIReply.id
    ).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.created_at >= since,
        ApprovedReply.edited == True
    ).scalar() or 0

    avg_conf_unedited = db.query(func.avg(AIReply.confidence_score)).join(
        ApprovedReply, ApprovedReply.ai_reply_id == AIReply.id
    ).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.created_at >= since,
        ApprovedReply.edited == False
    ).scalar() or 0

    return ConfidenceAccuracy(
        high_confidence_edit_rate=get_edit_rate_for_confidence_range(80, 101),
        medium_confidence_edit_rate=get_edit_rate_for_confidence_range(60, 80),
        low_confidence_edit_rate=get_edit_rate_for_confidence_range(0, 60),
        avg_confidence_edited=round(avg_conf_edited, 2),
        avg_confidence_unedited=round(avg_conf_unedited, 2),
    )


def get_intent_performance(
    db: Session,
    tenant_id: int,
    days: int = 30
) -> Dict[str, Dict]:
    """Get edit rates by detected intent."""
    since = datetime.utcnow() - timedelta(days=days)

    # Get all intents with their stats
    results = db.query(
        AIReply.intent_detected,
        func.count(ApprovedReply.id).label('total'),
        func.sum(func.cast(ApprovedReply.edited, db.bind.dialect.name == 'postgresql' and 'INTEGER' or 'INT')).label('edited_count'),
        func.avg(AIReply.confidence_score).label('avg_confidence'),
    ).join(
        ApprovedReply, ApprovedReply.ai_reply_id == AIReply.id
    ).join(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        ApprovedReply.created_at >= since
    ).group_by(AIReply.intent_detected).all()

    intent_stats = {}
    for row in results:
        intent = row.intent_detected or 'general'
        edited = row.edited_count or 0
        total = row.total or 0
        intent_stats[intent] = {
            'total': total,
            'edited': edited,
            'edit_rate': round(edited / total, 4) if total > 0 else 0,
            'avg_confidence': round(row.avg_confidence or 0, 2),
        }

    return intent_stats


def get_daily_stats(
    db: Session,
    tenant_id: int,
    days: int = 7
) -> List[Dict]:
    """Get daily stats for charting."""
    stats = []

    for i in range(days, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).date()
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())

        drafts = db.query(func.count(AIReply.id)).join(Ticket).filter(
            Ticket.tenant_id == tenant_id,
            AIReply.created_at >= start,
            AIReply.created_at <= end
        ).scalar() or 0

        approved = db.query(func.count(ApprovedReply.id)).join(Ticket).filter(
            Ticket.tenant_id == tenant_id,
            ApprovedReply.created_at >= start,
            ApprovedReply.created_at <= end
        ).scalar() or 0

        edited = db.query(func.count(ApprovedReply.id)).join(Ticket).filter(
            Ticket.tenant_id == tenant_id,
            ApprovedReply.created_at >= start,
            ApprovedReply.created_at <= end,
            ApprovedReply.edited == True
        ).scalar() or 0

        stats.append({
            'date': date.isoformat(),
            'drafts_generated': drafts,
            'replies_approved': approved,
            'replies_edited': edited,
        })

    return stats
