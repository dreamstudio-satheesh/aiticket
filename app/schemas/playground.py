from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class PlaygroundRequest(BaseModel):
    subject: str = "Playground Query"
    content: str
    use_reranking: bool = True
    prompt_id: Optional[int] = None
    temperature: Optional[int] = None  # 0-10, divide by 10 for actual value
    model: Optional[str] = None


class PlaygroundResponse(BaseModel):
    id: str
    role: str = "assistant"
    content: str
    confidence: float
    timestamp: int
    intent_detected: Optional[str] = None
    confidence_breakdown: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    context_sources: Optional[List[Dict]] = None
    latency_ms: Optional[int] = None
