from app.services.knowledge.global_kb_service import (
    ingest_global_kb,
    search_global_kb,
    get_global_kb_stats,
)
from app.services.knowledge import tenant_kb_service
from app.services.knowledge.examples_service import (
    index_approved_examples,
    search_examples,
    get_examples_stats,
)
from app.services.knowledge.corrections_service import (
    index_corrections,
    search_corrections,
    get_corrections_stats,
)
from app.services.knowledge.unified_retrieval import (
    retrieve_context,
    format_context_for_prompt,
    RetrievalContext,
    RetrievalResult,
)

__all__ = [
    # Global KB
    "ingest_global_kb",
    "search_global_kb",
    "get_global_kb_stats",
    # Tenant KB
    "tenant_kb_service",
    # Examples
    "index_approved_examples",
    "search_examples",
    "get_examples_stats",
    # Corrections
    "index_corrections",
    "search_corrections",
    "get_corrections_stats",
    # Unified retrieval
    "retrieve_context",
    "format_context_for_prompt",
    "RetrievalContext",
    "RetrievalResult",
]
