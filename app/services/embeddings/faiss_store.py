import os
import json
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from app.services.embeddings.embedding_service import embed_texts, embed_query, get_embedding_dimension

DATA_DIR = Path("data/indexes")


class FAISSStore:
    """Simple numpy-based vector store with cosine similarity search."""

    def __init__(self, name: str, tenant_id: Optional[int] = None):
        self.name = name
        self.tenant_id = tenant_id
        self.dimension = get_embedding_dimension()

        # Create index directory
        self.index_dir = DATA_DIR / (f"tenant_{tenant_id}" if tenant_id else "global")
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.index_dir / f"{name}.npy"
        self.metadata_path = self.index_dir / f"{name}_metadata.json"

        # Initialize or load
        self.embeddings: np.ndarray = None
        self.metadata: List[Dict] = []
        self._load_or_create()

    def _load_or_create(self):
        """Load existing index or create new one."""
        if self.index_path.exists() and self.metadata_path.exists():
            self.embeddings = np.load(str(self.index_path))
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            self.embeddings = np.zeros((0, self.dimension), dtype=np.float32)
            self.metadata = []

    def add(self, texts: List[str], metadata_list: List[Dict] = None):
        """Add texts with optional metadata."""
        if not texts:
            return

        new_embeddings = embed_texts(texts)

        if self.embeddings.shape[0] == 0:
            self.embeddings = new_embeddings.astype(np.float32)
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings.astype(np.float32)])

        # Store metadata
        for i, text in enumerate(texts):
            meta = metadata_list[i] if metadata_list and i < len(metadata_list) else {}
            self.metadata.append({
                "content": text,
                **meta
            })

        self._save()

    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.0) -> List[Tuple[Dict, float]]:
        """Search for similar texts using cosine similarity. Returns list of (metadata, score) tuples."""
        if self.embeddings.shape[0] == 0:
            return []

        query_embedding = embed_query(query).astype(np.float32)

        # Normalize for cosine similarity
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
        embed_norms = self.embeddings / (np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-9)

        # Cosine similarity (dot product of normalized vectors)
        scores = np.dot(embed_norms, query_norm)

        # Get top-k indices
        top_k = min(top_k, len(scores))
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score >= score_threshold:
                results.append((self.metadata[idx], score))

        return results

    def _save(self):
        """Persist embeddings and metadata to disk."""
        np.save(str(self.index_path), self.embeddings)
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def clear(self):
        """Clear all data from the index."""
        self.embeddings = np.zeros((0, self.dimension), dtype=np.float32)
        self.metadata = []
        self._save()

    @property
    def count(self) -> int:
        return self.embeddings.shape[0]


# Global index singletons
_global_kb_store: Optional[FAISSStore] = None


def get_global_kb_store() -> FAISSStore:
    global _global_kb_store
    if _global_kb_store is None:
        _global_kb_store = FAISSStore("global_kb")
    return _global_kb_store


def get_tenant_store(tenant_id: int, store_type: str) -> FAISSStore:
    """Get tenant-specific store. store_type: 'kb', 'examples', 'corrections'"""
    return FAISSStore(f"tenant_{store_type}", tenant_id=tenant_id)
