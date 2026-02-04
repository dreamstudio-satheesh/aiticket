# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-tenant SaaS AI support assistant for hosting companies (WHMCS-first). Generates AI draft replies for support tickets using RAG with human-in-the-loop learning. Does NOT auto-send replies.

## Commands

### Setup
```bash
pip install -r requirements.txt
cp .env.example .env  # Configure DATABASE_URL, OPENAI_API_KEY, SECRET_KEY
python init_database.py
python seed_prompts.py
python ingest_global_kb.py
```

### Run Development Server
```bash
uvicorn app.main:app --reload
```

### Access Points
- API: `http://localhost:8000/api/v1/`
- Docs: `http://localhost:8000/docs` (when DEBUG=True)
- UI: `http://localhost:8000/api/v1/ui/`

## Architecture

### Multi-Tenant Isolation
- `TenantMiddleware` extracts `tenant_id` from JWT and stores in ContextVar
- `TenantQuery[T]` helper auto-filters all DB queries by tenant
- Each tenant has isolated FAISS indexes at `data/indexes/tenant_{id}/`

### RAG Pipeline Flow
```
Ticket → Retrieve (4 sources) → Rerank (optional) → Detect Intent → Build Prompt → LLM → Confidence Score
```

**4 Vector Sources (weighted merge):**
1. `global_kb_index` - Shared hosting knowledge (20%)
2. `tenant_kb_index` - Company-specific articles (30%)
3. `tenant_examples_index` - Approved replies (35%)
4. `tenant_corrections_index` - Past mistakes to avoid (15%)

### Confidence Scoring Formula
```
score = 0.4 × example_similarity + 0.3 × KB_similarity + 0.2 × intent_certainty + 0.1 × correction_safety
```

### Auto-Learning Flow
```
Approve Reply → Analyze Edit
  → If similar (≥70%) → Index to examples (good for future reference)
  → If correction (<70%) → Index to corrections (avoid repeating)
```

### Key Services
- `app/services/rag/rag_pipeline.py` - Main `generate_reply()` orchestration
- `app/services/knowledge/unified_retrieval.py` - Multi-source retrieval with weighted merge
- `app/services/confidence/confidence_engine.py` - Intent detection and scoring
- `app/services/learning/` - Examples, corrections, and weight tuning

### Database Models
Core models in `app/models/`: Tenant, User, Ticket, AIReply, ApprovedReply, PromptVersion, RerankingConfig, KBArticle, AuditLog

### API Structure
All routes in `app/api/v1/`: auth, kb, search, prompts, whmcs, replies, analytics, examples, corrections, weights

## Design Principles

1. Human control first - No auto-send in MVP
2. Corrections over documents - Learn from mistakes
3. Tenant isolation above all - No cross-tenant data leakage
4. Confidence before automation - Score every reply
