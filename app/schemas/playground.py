from pydantic import BaseModel
from typing import Optional, List, Dict


class PlaygroundRequest(BaseModel):
    subject: str = "Playground Query"
    content: str
    use_reranking: bool = True


class PlaygroundResponse(BaseModel):
    id: str
    role: str = "assistant"
    content: str
    confidence: float
    timestamp: int
    intent_detected: Optional[str] = None
    confidence_breakdown: Optional[Dict[str, float]] = None
    recommendations: Optional[List[str]] = None
    context_sources: Optional[List[Dict]] = None
    latency_ms: Optional[int] = None
