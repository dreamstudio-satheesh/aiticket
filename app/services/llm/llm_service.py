from typing import Optional, Dict, List
import time
from openai import OpenAI

from app.config import get_settings

settings = get_settings()

_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        if settings.openrouter_api_key:
            # Use OpenRouter
            _client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        else:
            # Fall back to OpenAI
            _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def generate_completion(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 1000,
) -> Dict:
    """
    Generate completion from OpenAI.
    Returns dict with response, tokens_used, latency_ms.
    """
    client = get_openai_client()

    start_time = time.time()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "content": response.choices[0].message.content,
        "tokens_used": response.usage.total_tokens,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "latency_ms": latency_ms,
        "model": model,
    }


def generate_with_messages(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 1000,
) -> Dict:
    """Generate completion with full message history."""
    client = get_openai_client()

    start_time = time.time()

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "content": response.choices[0].message.content,
        "tokens_used": response.usage.total_tokens,
        "latency_ms": latency_ms,
        "model": model,
    }
