# AI Support Assistant

Multi-tenant SaaS AI support assistant for hosting companies (WHMCS-first). Generates AI draft replies for support tickets using RAG with human-in-the-loop learning.

**Note:** This system does NOT auto-send replies. All AI-generated responses require human approval.

## Features

- **Multi-Tenant Architecture** - Complete data isolation between tenants with separate FAISS indexes
- **RAG Pipeline** - 4-source retrieval with weighted merge (global KB, tenant KB, examples, corrections)
- **Confidence Scoring** - Every reply includes a confidence score to guide human review
- **Auto-Learning** - System learns from approved replies and corrections automatically
- **WHMCS Integration** - Built for hosting company support workflows

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, OPENAI_API_KEY, SECRET_KEY

# Initialize database
python init_database.py

# Seed default prompts
python seed_prompts.py

# Ingest global knowledge base
python ingest_global_kb.py
```

### Run Development Server

```bash
uvicorn app.main:app --reload
```

### Access Points

| Endpoint | URL |
|----------|-----|
| API | http://localhost:8000/api/v1/ |
| Swagger Docs | http://localhost:8000/docs (DEBUG=True) |
| UI | http://localhost:8000/api/v1/ui/ |

## Architecture

### RAG Pipeline Flow

```
Ticket → Retrieve (4 sources) → Rerank (optional) → Detect Intent → Build Prompt → LLM → Confidence Score
```

### Vector Sources (Weighted Merge)

| Source | Weight | Purpose |
|--------|--------|---------|
| Global KB | 20% | Shared hosting knowledge |
| Tenant KB | 30% | Company-specific articles |
| Tenant Examples | 35% | Approved replies |
| Tenant Corrections | 15% | Past mistakes to avoid |

### Confidence Scoring

```
score = 0.4 × example_similarity + 0.3 × KB_similarity + 0.2 × intent_certainty + 0.1 × correction_safety
```

### Auto-Learning

When a reply is approved:
- **Similar to draft (≥70%)** → Indexed as example for future reference
- **Significant edits (<70%)** → Indexed as correction to avoid repeating

## Project Structure

```
app/
├── api/v1/           # API routes (auth, kb, search, prompts, whmcs, replies, analytics)
├── models/           # Database models (Tenant, User, Ticket, AIReply, etc.)
├── services/
│   ├── rag/          # RAG pipeline orchestration
│   ├── knowledge/    # Multi-source retrieval
│   ├── confidence/   # Intent detection and scoring
│   └── learning/     # Examples, corrections, weight tuning
data/
└── indexes/
    └── tenant_{id}/  # Per-tenant FAISS indexes
```

## Design Principles

1. **Human control first** - No auto-send in MVP
2. **Corrections over documents** - Learn from mistakes
3. **Tenant isolation above all** - No cross-tenant data leakage
4. **Confidence before automation** - Score every reply

## License

Proprietary
