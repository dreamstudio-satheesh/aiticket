"""Run this script to ingest global knowledge base into FAISS."""
from app.services.knowledge import ingest_global_kb, get_global_kb_stats

if __name__ == "__main__":
    print("Starting global KB ingestion...")
    ingest_global_kb()
    stats = get_global_kb_stats()
    print(f"Stats: {stats}")
