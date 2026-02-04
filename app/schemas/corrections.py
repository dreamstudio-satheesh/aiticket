from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class CorrectionListItem(BaseModel):
    id: int
    ticket_id: int
    ticket_subject: str
    ai_reply_preview: Optional[str]
    final_reply_preview: str
    edit_summary: Optional[str]
    edit_distance: Optional[float]
    ai_confidence: Optional[float]
    intent: Optional[str]
    created_at: datetime


class CorrectionTicketDetail(BaseModel):
    id: int
    whmcs_ticket_id: int
    subject: str
    content: str
    department: Optional[str]
    client_email: Optional[str]


class CorrectionAIReplyDetail(BaseModel):
    id: Optional[int]
    content: Optional[str]
    confidence_score: Optional[float]
    confidence_breakdown: Optional[Dict]
    intent_detected: Optional[str]


class CorrectionDetail(BaseModel):
    id: int
    ticket: CorrectionTicketDetail
    ai_reply: CorrectionAIReplyDetail
    corrected_reply: str
    edit_summary: Optional[str]
    edit_distance: Optional[float]
    diff_lines: List[str]
    created_at: datetime


class CorrectionsStatsResponse(BaseModel):
    total_corrections: int
    avg_original_confidence: float
    avg_edit_distance: float
    by_intent: Dict[str, int]
    index_chunks: int


class SimilarCorrectionResponse(BaseModel):
    content: str
    score: float
    source: str
    edit_summary: Optional[str]
    original_confidence: Optional[float]
    intent: Optional[str]
