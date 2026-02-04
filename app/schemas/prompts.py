from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class PromptVersionCreate(BaseModel):
    name: str
    version: str = "custom"
    description: Optional[str] = ""
    system_prompt: str
    context_template: str
    task_template: str
    model: str = "gpt-4o-mini"
    temperature: int = 3  # Divide by 10 for actual value
    max_tokens: int = 1000


class PromptVersionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    context_template: Optional[str] = None
    task_template: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[int] = None
    max_tokens: Optional[int] = None


class PromptVersionResponse(BaseModel):
    id: int
    tenant_id: Optional[int]
    version: str
    name: str
    description: Optional[str]
    system_prompt: str
    context_template: str
    task_template: str
    model: str
    temperature: int
    max_tokens: int
    is_active: bool
    is_default: bool
    performance_metrics: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SetActivePromptRequest(BaseModel):
    prompt_id: int


class DuplicatePromptRequest(BaseModel):
    prompt_id: int
    new_name: str
