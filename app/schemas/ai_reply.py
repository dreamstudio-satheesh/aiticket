from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

from app.schemas.confidence import ConfidenceLevelEnum


class GenerateReplyRequest(BaseModel):
    ticket_id: int
    use_reranking: bool = True


class AIReplyResponse(BaseModel):
    id: int
    ticket_id: int
    ai_reply: str
    confidence_score: float
    confidence_level: ConfidenceLevelEnum
    confidence_breakdown: Dict[str, float]
    recommendations: List[str]
    should_escalate: bool
    intent_detected: Optional[str]
    tokens_used: int
    latency_ms: int
    prompt_version_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class AIReplyListResponse(BaseModel):
    id: int
    ticket_id: int
    ai_reply: str
    confidence_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class TicketWithDraftResponse(BaseModel):
    """Ticket with its AI draft reply for UI display."""
    # Ticket info
    id: int
    whmcs_ticket_id: int
    subject: str
    content: str
    department: Optional[str]
    priority: Optional[str]
    status: str
    client_email: Optional[str]
    created_at: datetime

    # AI Reply
    draft: Optional[AIReplyResponse] = None
    has_approved_reply: bool = False


class EditDraftRequest(BaseModel):
    """Request to edit AI draft before approval."""
    edited_reply: str


class ApproveReplyRequest(BaseModel):
    """Request to approve a reply (with optional edits)."""
    ai_reply_id: int
    final_reply: str
