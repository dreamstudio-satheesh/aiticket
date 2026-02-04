"""Edit tracking service for monitoring AI reply edits."""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher, unified_diff
from sqlalchemy.orm import Session

from app.models import AIReply, ApprovedReply, Ticket
from app.models.audit_log import AuditLog, AuditAction


@dataclass
class EditAnalysis:
    """Detailed analysis of edits made to AI reply."""
    similarity_ratio: float  # 0-1, 1 = identical
    was_edited: bool
    is_significant_edit: bool  # < 70% similarity
    char_diff: int  # Character count difference
    word_diff: int  # Word count difference
    additions: int  # Characters added
    deletions: int  # Characters deleted
    diff_lines: List[str]  # Unified diff output


def analyze_edit(original: str, edited: str) -> EditAnalysis:
    """Analyze the differences between original AI reply and edited version."""
    # Calculate similarity
    similarity = SequenceMatcher(None, original, edited).ratio()

    # Character and word counts
    orig_chars = len(original)
    edit_chars = len(edited)
    orig_words = len(original.split())
    edit_words = len(edited.split())

    # Calculate additions and deletions using opcodes
    matcher = SequenceMatcher(None, original, edited)
    additions = 0
    deletions = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'insert':
            additions += j2 - j1
        elif tag == 'delete':
            deletions += i2 - i1
        elif tag == 'replace':
            deletions += i2 - i1
            additions += j2 - j1

    # Generate unified diff
    orig_lines = original.splitlines(keepends=True)
    edit_lines = edited.splitlines(keepends=True)
    diff = list(unified_diff(orig_lines, edit_lines, fromfile='AI Draft', tofile='Final Reply', lineterm=''))

    return EditAnalysis(
        similarity_ratio=similarity,
        was_edited=similarity < 0.99,  # Allow tiny differences
        is_significant_edit=similarity < 0.7,
        char_diff=edit_chars - orig_chars,
        word_diff=edit_words - orig_words,
        additions=additions,
        deletions=deletions,
        diff_lines=diff,
    )


def track_reply_approval(
    db: Session,
    tenant_id: int,
    user_id: int,
    ticket: Ticket,
    ai_reply: AIReply,
    approved_reply: ApprovedReply,
    edit_analysis: EditAnalysis
) -> AuditLog:
    """Create audit log entry for reply approval."""
    action = AuditAction.REPLY_EDITED if edit_analysis.was_edited else AuditAction.REPLY_APPROVED

    details = {
        "similarity_ratio": round(edit_analysis.similarity_ratio, 4),
        "was_edited": edit_analysis.was_edited,
        "is_correction": edit_analysis.is_significant_edit,
        "char_diff": edit_analysis.char_diff,
        "word_diff": edit_analysis.word_diff,
        "additions": edit_analysis.additions,
        "deletions": edit_analysis.deletions,
        "ai_confidence_score": ai_reply.confidence_score,
        "ai_intent": ai_reply.intent_detected,
    }

    log = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        entity_type="approved_reply",
        entity_id=approved_reply.id,
        ticket_id=ticket.id,
        ai_reply_id=ai_reply.id,
        details=details,
    )
    db.add(log)

    # Also log if flagged as correction
    if edit_analysis.is_significant_edit:
        correction_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CORRECTION_FLAGGED,
            entity_type="approved_reply",
            entity_id=approved_reply.id,
            ticket_id=ticket.id,
            ai_reply_id=ai_reply.id,
            details={
                "similarity_ratio": round(edit_analysis.similarity_ratio, 4),
                "diff_preview": edit_analysis.diff_lines[:20] if edit_analysis.diff_lines else [],
            },
        )
        db.add(correction_log)

    db.commit()
    return log


def track_draft_generation(
    db: Session,
    tenant_id: int,
    user_id: int,
    ticket: Ticket,
    ai_reply: AIReply,
    is_regeneration: bool = False
) -> AuditLog:
    """Create audit log for draft generation."""
    action = AuditAction.DRAFT_REGENERATED if is_regeneration else AuditAction.DRAFT_GENERATED

    log = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        entity_type="ai_reply",
        entity_id=ai_reply.id,
        ticket_id=ticket.id,
        ai_reply_id=ai_reply.id,
        details={
            "confidence_score": ai_reply.confidence_score,
            "intent_detected": ai_reply.intent_detected,
            "tokens_used": ai_reply.tokens_used,
            "latency_ms": ai_reply.latency_ms,
            "prompt_version_id": ai_reply.prompt_version_id,
        },
    )
    db.add(log)
    db.commit()
    return log


def get_edit_history(
    db: Session,
    tenant_id: int,
    ticket_id: Optional[int] = None,
    limit: int = 50
) -> List[AuditLog]:
    """Get edit history for a tenant or specific ticket."""
    query = db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_id,
        AuditLog.action.in_([AuditAction.REPLY_APPROVED, AuditAction.REPLY_EDITED, AuditAction.CORRECTION_FLAGGED])
    )

    if ticket_id:
        query = query.filter(AuditLog.ticket_id == ticket_id)

    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()


def get_correction_history(db: Session, tenant_id: int, limit: int = 50) -> List[AuditLog]:
    """Get all corrections for learning analysis."""
    return db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_id,
        AuditLog.action == AuditAction.CORRECTION_FLAGGED
    ).order_by(AuditLog.created_at.desc()).limit(limit).all()
