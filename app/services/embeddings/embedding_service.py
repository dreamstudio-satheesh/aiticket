from typing import List
import numpy as np
from openai import OpenAI
import os

# OpenAI client singleton
_client: OpenAI = None

# Using text-embedding-3-small (1536 dims, good quality, cost-effective)
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def embed_texts(texts: List[str]) -> np.ndarray:
    """Generate embeddings for a list of texts using OpenAI."""
    if not texts:
        return np.array([])

    client = get_openai_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )

    embeddings = [item.embedding for item in response.data]
    return np.array(embeddings, dtype=np.float32)


def embed_query(query: str) -> np.ndarray:
    """Generate embedding for a single query."""
    client = get_openai_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query]
    )
    return np.array(response.data[0].embedding, dtype=np.float32)


def get_embedding_dimension() -> int:
    return EMBEDDING_DIMENSION
