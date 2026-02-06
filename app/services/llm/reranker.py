from typing import List, Tuple, Optional
import numpy as np

from app.services.embeddings.embedding_service import embed_texts, embed_query
from app.services.knowledge.unified_retrieval import RetrievalResult


def _cosine_similarities(query_embedding: np.ndarray, doc_embeddings: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between query and each document."""
    query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
    doc_norms = doc_embeddings / (np.linalg.norm(doc_embeddings, axis=1, keepdims=True) + 1e-9)
    return np.dot(doc_norms, query_norm)


def rerank_results(
    query: str,
    results: List[RetrievalResult],
    top_k: int = 5,
    score_threshold: float = 0.0,
) -> List[RetrievalResult]:
    """
    Rerank retrieval results using OpenAI embeddings cosine similarity.
    Re-embeds query and documents for a fresh similarity comparison.
    """
    if not results:
        return []

    # Embed query and all result contents via OpenAI
    query_embedding = embed_query(query)
    doc_embeddings = embed_texts([r.content for r in results])

    # Compute cosine similarity scores
    scores = _cosine_similarities(query_embedding, doc_embeddings)

    # Attach scores and filter
    scored_results = []
    for result, score in zip(results, scores):
        if score >= score_threshold:
            scored_results.append(RetrievalResult(
                content=result.content,
                score=float(score),
                source=result.source,
                source_type=result.source_type,
                metadata={**result.metadata, "original_score": result.score}
            ))

    # Sort by reranker score
    scored_results.sort(key=lambda x: x.score, reverse=True)

    return scored_results[:top_k]


def rerank_with_diversity(
    query: str,
    results: List[RetrievalResult],
    top_k: int = 5,
    diversity_threshold: float = 0.7,
) -> List[RetrievalResult]:
    """
    Rerank with diversity: avoid too similar results.
    Uses MMR-like approach.
    """
    if not results:
        return []

    reranked = rerank_results(query, results, top_k=len(results))

    if len(reranked) <= top_k:
        return reranked

    # Simple diversity: prefer different source types
    selected = []
    source_types_seen = set()

    for result in reranked:
        # Always add if we haven't reached top_k
        if len(selected) < top_k:
            # Prefer diverse source types first
            if result.source_type not in source_types_seen or len(selected) >= top_k - 2:
                selected.append(result)
                source_types_seen.add(result.source_type)

    return selected[:top_k]
