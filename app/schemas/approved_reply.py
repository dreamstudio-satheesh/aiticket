from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class ApprovedReplyListItem(BaseModel):
    id: int
    ticket_id: int
    ticket_subject: str
    ticket_content: str
    ai_reply: Optional[str]
    final_reply: str
    edited: bool
    edit_distance: Optional[float]
    is_correction: bool
    used_for_training: bool
    ai_confidence: Optional[float]
    created_at: datetime


class TicketDetail(BaseModel):
    id: int
    whmcs_ticket_id: int
    subject: str
    content: str
    department: Optional[str]
    priority: Optional[str]
    client_email: Optional[str]


class AIReplyDetail(BaseModel):
    id: Optional[int]
    content: Optional[str]
    confidence_score: Optional[float]
    intent_detected: Optional[str]


class ApprovedReplyDetail(BaseModel):
    id: int
    ticket: TicketDetail
    ai_reply: AIReplyDetail
    final_reply: str
    edited: bool
    edit_distance: Optional[float]
    is_correction: bool
    used_for_training: bool
    diff_lines: List[str]
    created_at: datetime


class ExamplesStatsResponse(BaseModel):
    total_approved: int
    indexed_examples: int
    corrections: int
    edited_replies: int
    edit_rate: float
    index_chunks: int


class RebuildIndexResponse(BaseModel):
    indexed_count: int
    message: str
