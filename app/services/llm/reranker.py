from typing import List, Tuple, Optional
from sentence_transformers import CrossEncoder

from app.services.knowledge.unified_retrieval import RetrievalResult

# Singleton reranker model
_reranker: Optional[CrossEncoder] = None


def get_reranker() -> CrossEncoder:
    """Get or initialize cross-encoder reranker."""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker


def rerank_results(
    query: str,
    results: List[RetrievalResult],
    top_k: int = 5,
    score_threshold: float = 0.0,
) -> List[RetrievalResult]:
    """
    Rerank retrieval results using cross-encoder.
    More accurate than bi-encoder but slower.
    """
    if not results:
        return []

    reranker = get_reranker()

    # Prepare pairs for reranking
    pairs = [(query, r.content) for r in results]

    # Get reranker scores
    scores = reranker.predict(pairs)

    # Attach scores and sort
    scored_results = []
    for result, score in zip(results, scores):
        if score >= score_threshold:
            # Create new result with reranked score
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
