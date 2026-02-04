from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

from app.models.ticket import TicketStatus


class WHMCSConfigCreate(BaseModel):
    whmcs_url: str
    api_identifier: str
    api_secret: str


class WHMCSConfigResponse(BaseModel):
    whmcs_url: Optional[str]
    is_configured: bool
    connection_valid: bool = False


class WHMCSDepartment(BaseModel):
    id: int
    name: str
    description: str
    hidden: bool


class TicketResponse(BaseModel):
    id: int
    whmcs_ticket_id: int
    subject: str
    content: str
    department: Optional[str]
    priority: Optional[str]
    status: TicketStatus
    client_email: Optional[str]
    created_at: datetime
    updated_at: datetime
    has_ai_reply: bool = False

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    tickets: List[TicketResponse]
    total: int
    page: int
    limit: int


class SyncRequest(BaseModel):
    status: Optional[str] = None  # WHMCS status filter
    limit: int = 25


class SyncResponse(BaseModel):
    synced_count: int
    tickets: List[TicketResponse]
