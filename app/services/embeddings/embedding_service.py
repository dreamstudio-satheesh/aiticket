from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

# Singleton model instance
_model: SentenceTransformer = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")  # Fast, good quality, 384 dims
    return _model


def embed_texts(texts: List[str]) -> np.ndarray:
    """Generate embeddings for a list of texts."""
    model = get_embedding_model()
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)


def embed_query(query: str) -> np.ndarray:
    """Generate embedding for a single query."""
    model = get_embedding_model()
    return model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]


def get_embedding_dimension() -> int:
    return 384  # all-MiniLM-L6-v2 dimension
