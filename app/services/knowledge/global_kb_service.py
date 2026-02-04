import os
from pathlib import Path
from typing import List, Dict

from app.services.embeddings import chunk_markdown, chunk_text, get_global_kb_store

KB_DIR = Path("data/kb/global")


def ingest_global_kb():
    """
    Ingest all markdown files from data/kb/global into global FAISS index.
    Run once at setup or when KB is updated.
    """
    store = get_global_kb_store()
    store.clear()  # Fresh ingest

    total_chunks = 0

    for file_path in KB_DIR.glob("**/*.md"):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Get relative path for source tracking
        rel_path = file_path.relative_to(KB_DIR)
        category = rel_path.parts[0] if len(rel_path.parts) > 1 else "general"

        chunks = chunk_markdown(content, metadata={
            "source": str(rel_path),
            "category": category,
            "type": "global_kb"
        })

        if chunks:
            texts = [c["content"] for c in chunks]
            metadata = [c["metadata"] for c in chunks]
            store.add(texts, metadata)
            total_chunks += len(chunks)
            print(f"Ingested {file_path.name}: {len(chunks)} chunks")

    print(f"Global KB ingestion complete: {total_chunks} total chunks")
    return total_chunks


def search_global_kb(query: str, top_k: int = 5) -> List[Dict]:
    """Search global knowledge base."""
    store = get_global_kb_store()
    results = store.search(query, top_k=top_k)
    return [{"content": r[0]["content"], "score": r[1], **r[0]} for r in results]


def get_global_kb_stats() -> Dict:
    """Get stats about global KB index."""
    store = get_global_kb_store()
    return {
        "total_chunks": store.count,
        "index_path": str(store.index_path),
    }
