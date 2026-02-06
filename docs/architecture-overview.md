# Architecture Overview

Multi-tenant SaaS AI support assistant for hosting companies (WHMCS-first). Generates AI draft replies for support tickets using RAG with human-in-the-loop learning. **Does NOT auto-send replies.**

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11) |
| Frontend | React + TypeScript (Vite) |
| Database | PostgreSQL 15 |
| Vector Store | Custom numpy-based (cosine similarity) |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dim) |
| LLM | OpenAI GPT-4o-mini (or OpenRouter) |
| Auth | JWT (HS256) |
| Encryption | Fernet (symmetric, for WHMCS creds) |
| Container | Docker + Docker Compose |

---

## Project Structure

```
aiagent/
├── app/
│   ├── main.py                     # FastAPI app + middleware setup
│   ├── config.py                   # Settings (pydantic-settings, .env)
│   │
│   ├── api/v1/                     # REST API routes
│   │   ├── __init__.py             # Router aggregation + prefixes
│   │   ├── auth.py                 # Login, register, me
│   │   ├── replies.py              # Generate, approve, pending
│   │   ├── kb.py                   # KB articles CRUD + indexing
│   │   ├── search.py               # Global, tenant, unified search
│   │   ├── prompts.py              # Prompt version management
│   │   ├── whmcs.py                # WHMCS config, sync, tickets
│   │   ├── analytics.py            # Dashboard, metrics, history
│   │   ├── examples.py             # Training examples management
│   │   ├── corrections.py          # Corrections tracking
│   │   ├── weights.py              # Retrieval weight tuning
│   │   ├── playground.py           # Test RAG without real ticket
│   │   └── ui.py                   # Serves frontend HTML
│   │
│   ├── models/                     # SQLAlchemy ORM
│   │   ├── base.py                 # Base + TimestampMixin
│   │   ├── tenant.py               # Tenant (company)
│   │   ├── user.py                 # User + UserRole enum
│   │   ├── ticket.py               # Ticket + TicketStatus enum
│   │   ├── ai_reply.py             # AI-generated draft
│   │   ├── approved_reply.py       # Human-approved reply
│   │   ├── prompt_version.py       # System prompt configs
│   │   ├── reranking.py            # Reranking config + weights
│   │   ├── kb_article.py           # KB articles + KBCategory enum
│   │   └── audit_log.py            # Audit trail + AuditAction enum
│   │
│   ├── schemas/                    # Pydantic request/response models
│   │   ├── auth.py
│   │   ├── ai_reply.py
│   │   ├── confidence.py
│   │   ├── kb.py
│   │   ├── prompts.py
│   │   ├── analytics.py
│   │   ├── weights.py
│   │   ├── whmcs.py
│   │   └── playground.py
│   │
│   ├── services/                   # Business logic
│   │   ├── auth_service.py         # Password hashing, user lookup
│   │   ├── rag/
│   │   │   └── rag_pipeline.py     # Main generate_reply() orchestration
│   │   ├── knowledge/
│   │   │   ├── unified_retrieval.py     # 4-source weighted merge
│   │   │   ├── global_kb_service.py     # Global KB search
│   │   │   ├── tenant_kb_service.py     # Tenant KB search
│   │   │   ├── examples_service.py      # Approved examples search
│   │   │   └── corrections_service.py   # Corrections search
│   │   ├── embeddings/
│   │   │   ├── embedding_service.py     # OpenAI embeddings client
│   │   │   ├── faiss_store.py           # Numpy vector store
│   │   │   └── chunker.py              # Text chunking
│   │   ├── llm/
│   │   │   ├── llm_service.py           # OpenAI/OpenRouter client
│   │   │   └── reranker.py              # Cosine similarity reranker
│   │   ├── confidence/
│   │   │   └── confidence_engine.py     # Scoring + intent detection
│   │   ├── learning/
│   │   │   ├── approved_replies_service.py  # Index examples
│   │   │   ├── corrections_service.py       # Index corrections
│   │   │   └── weight_tuning_service.py     # Dynamic weight adjust
│   │   ├── prompts/
│   │   │   ├── prompt_service.py        # Prompt CRUD + activation
│   │   │   └── prompt_templates.py      # Default prompt library
│   │   ├── encryption/
│   │   │   └── encryption_service.py    # Fernet encrypt/decrypt
│   │   ├── whmcs/
│   │   │   ├── whmcs_client.py          # WHMCS API client
│   │   │   └── ticket_sync_service.py   # Ticket sync logic
│   │   └── tracking/
│   │       ├── edit_tracker.py          # Levenshtein edit analysis
│   │       └── analytics_service.py     # Metrics aggregation
│   │
│   ├── middleware/
│   │   └── tenant.py               # TenantMiddleware (ContextVar)
│   │
│   ├── core/
│   │   ├── security.py             # JWT create/decode
│   │   ├── deps.py                 # get_current_user, require_admin
│   │   └── tenant_deps.py          # Tenant context helpers
│   │
│   └── db/
│       ├── session.py              # SQLAlchemy engine + SessionLocal
│       └── tenant_query.py         # TenantQuery[T] auto-filter
│
├── frontend/
│   ├── App.tsx                     # Main app (dashboard, prompts, KB, playground)
│   ├── index.tsx                   # React entry
│   ├── types.ts                    # TypeScript interfaces
│   ├── components/
│   │   ├── LoginScreen.tsx
│   │   ├── Sidebar.tsx
│   │   └── GlassCard.tsx
│   ├── services/
│   │   └── apiService.ts           # API client wrapper
│   └── styles/
│       └── tailwind.css
│
├── data/
│   ├── indexes/
│   │   ├── global/                 # Global KB index (.npy + metadata.json)
│   │   └── tenant_{id}/           # Per-tenant indexes
│   └── kb/
│       └── global/                 # Global KB markdown source files
│
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh                   # DB init → seed → start server
├── requirements.txt
├── init_database.py
├── seed_prompts.py
├── seed_users.py
└── ingest_global_kb.py
```

---

## Multi-Tenant Isolation

Three layers ensure no cross-tenant data leakage:

### 1. Middleware (ContextVar)

```
Request → TenantMiddleware → Extract tenant_id from JWT → Set ContextVar → Route Handler
```

Every request automatically sets the current tenant from the JWT token. No tenant_id needs to be passed explicitly through function calls.

### 2. TenantQuery Helper

All database queries use `TenantQuery[T]` which auto-appends `.filter(model.tenant_id == current_tenant_id)`. Methods: `all()`, `get()`, `create()` (auto-sets tenant_id), `delete()`.

### 3. Isolated FAISS Indexes

Each tenant has its own vector index directory:

```
data/indexes/
├── global/
│   ├── global_kb.npy
│   └── global_kb_metadata.json
├── tenant_1/
│   ├── tenant_kb.npy + metadata
│   ├── tenant_examples.npy + metadata
│   └── tenant_corrections.npy + metadata
└── tenant_2/
    └── ... (completely separate)
```

---

## RAG Pipeline

### Complete Flow

```
Ticket
  │
  ▼
┌─────────────────────────────────────────┐
│  1. RETRIEVE CONTEXT (4 sources)        │
│  ┌────────────┐  ┌────────────────┐     │
│  │ Global KB  │  │  Tenant KB     │     │
│  │  (20%)     │  │   (30%)        │     │
│  └────────────┘  └────────────────┘     │
│  ┌────────────┐  ┌────────────────┐     │
│  │ Examples   │  │  Corrections   │     │
│  │  (35%)     │  │   (15%)        │     │
│  └────────────┘  └────────────────┘     │
│         │                               │
│         ▼                               │
│  Weighted merge → sorted top-k          │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  2. RERANK (optional)                   │
│  Re-embed query + docs → cosine sim     │
│  Filter by score_threshold → top-k      │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  3. INTENT DETECTION                    │
│  12 categories: billing, email, ssl,    │
│  malware, dns, migration, etc.          │
│  Keyword matching + count boosting      │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  4. CONFIDENCE SCORING                  │
│  0.4 × example_similarity              │
│  0.3 × kb_similarity                   │
│  0.2 × intent_certainty                │
│  0.1 × correction_safety               │
│  ────────────────────────               │
│  Score: 0–100                           │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  5. BUILD PROMPT                        │
│  system_prompt  → persona/guidelines    │
│  context_template → retrieved docs      │
│  task_template  → ticket + instructions │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  6. LLM GENERATION                      │
│  OpenAI GPT-4o-mini (or OpenRouter)     │
│  Temperature: 0.3, Max tokens: 1000    │
└─────────────────────────────────────────┘
  │
  ▼
AI Draft Reply + Confidence Score + Metadata
```

### Retrieval Weights

| Source | Default Weight | Purpose |
|--------|---------------|---------|
| Global KB | 0.20 | Shared hosting knowledge (cPanel, DNS, etc.) |
| Tenant KB | 0.30 | Company-specific articles, policies, pricing |
| Approved Examples | 0.35 | Past good replies (highest signal) |
| Corrections | 0.15 | Past mistakes to avoid repeating |

Weights are configurable per-tenant and auto-normalized to sum to 1.0. The `/weights/recommend` endpoint suggests optimal weights based on historical effectiveness.

### Vector Store (FAISSStore)

Custom numpy-based implementation (not the official FAISS library):

- **Storage:** `.npy` files for embeddings + `.json` for metadata
- **Search:** Cosine similarity via normalized dot product
- **Embedding model:** `text-embedding-3-small` (1536 dimensions)
- **Operations:** `add()`, `search()`, `clear()`, `delete()`, `save()`, `load()`

---

## Confidence Scoring

### Formula

```
score = 0.4 × example_similarity
      + 0.3 × kb_similarity
      + 0.2 × intent_certainty
      + 0.1 × correction_safety
```

### Components

| Component | Weight | Description |
|-----------|--------|-------------|
| Example Similarity | 0.40 | Best match score from approved examples. Boosted if 2+ good matches (>0.5) |
| KB Similarity | 0.30 | Weighted blend of tenant KB (60%) and global KB (40%). Penalized if intent requires tenant KB but none found |
| Intent Certainty | 0.20 | Base confidence per intent category + boost for multiple keyword matches |
| Correction Safety | 0.10 | 1.0 if no past corrections found. Degrades to 0.4 if very similar correction exists (>0.8 match) |

### Confidence Levels

| Level | Score Range | Meaning |
|-------|------------|---------|
| `high` | 75–100 | Strong draft, minimal review needed |
| `medium` | 50–74 | Good draft, some review recommended |
| `low` | 25–49 | Needs careful review |
| `very_low` | 0–24 | Consider escalation |

---

## Auto-Learning System

When a support agent approves a reply, the system automatically learns:

```
Agent approves reply
        │
        ▼
  Edit Analysis
  (Levenshtein distance)
        │
        ├── similarity ≥ 70%
        │   └── Index as EXAMPLE
        │       (good for future reference)
        │
        └── similarity < 70%
            └── Index as CORRECTION
                (avoid repeating this mistake)
```

### Example Indexing

Approved replies with minor/no edits are indexed as examples:

```
Content indexed:
  "Customer Issue: {subject}\n{content}\n\nApproved Response:\n{final_reply}"
```

Future similar tickets will retrieve this example, boosting confidence and draft quality.

### Correction Indexing

Heavily edited replies are indexed as corrections:

```
Content indexed:
  "Customer Issue: {subject}\n{content}\n\n
   INCORRECT Response (Do Not Use):\n{ai_reply}\n\n
   CORRECT Response:\n{final_reply}\n\n
   Edit Notes: {edit_summary}"
```

Future similar tickets trigger `correction_safety` penalty, alerting the agent.

---

## Authentication & Authorization

### JWT Flow

```
POST /auth/login (email + password)
        │
        ▼
  Verify password (bcrypt)
        │
        ▼
  Create JWT token
  Payload: { sub: user_id, tenant_id: 42, exp: ..., iat: ... }
        │
        ▼
  Client stores token
  Sends as: Authorization: Bearer <token>
        │
        ▼
  TenantMiddleware decodes token
  Sets tenant_id in ContextVar
```

### Role-Based Access

| Role | Can Do |
|------|--------|
| `support_agent` | View tickets, generate/approve drafts, search, view analytics |
| `admin` | Everything above + manage KB, prompts, weights, WHMCS config, rebuild indexes |

Enforced via `get_current_user` and `require_admin` dependency injection.

---

## WHMCS Integration

### Credential Security

WHMCS API credentials are encrypted at rest using Fernet (symmetric encryption derived from `SECRET_KEY`):

```
Input: "real_api_secret"
  → Fernet.encrypt() → stored in DB as ciphertext
  → Fernet.decrypt() → used only at request time
```

### Ticket Sync Flow

```
POST /whmcs/sync
  │
  ▼
Decrypt WHMCS credentials
  │
  ▼
Call WHMCS API (GetTickets)
  │
  ▼
For each ticket:
  ├── Already exists? → Update status
  └── New? → Create Ticket record
  │
  ▼
Return synced count + ticket list
```

---

## Prompt Management

### Hierarchy

```
Global Prompts (tenant_id = NULL)
  │
  ├── "Default Support Prompt" (is_default=true)
  └── Other global templates
  │
  ▼
Tenant Prompts (tenant_id = N)
  │
  ├── Duplicated from global (customized)
  └── Created from scratch
```

- Only **one prompt active per tenant** at a time
- If no tenant prompt is active, falls back to global default
- Tenants can duplicate global prompts to customize
- Cannot edit global prompts directly

### Prompt Components

| Component | Template Variables | Purpose |
|-----------|-------------------|---------|
| `system_prompt` | None | Persona, guidelines, tone |
| `context_template` | `{context}` | Retrieved RAG context injection |
| `task_template` | `{subject}`, `{content}`, `{department}` | Ticket details + instructions |

---

## Frontend Architecture

### Views

| View | Description |
|------|-------------|
| Dashboard | System metrics, daily stats, alerts |
| Prompts | Create/edit/activate system prompts |
| Knowledge Base | Upload/manage KB articles, trigger indexing |
| Playground | Test RAG pipeline with custom input |
| Login | JWT authentication |

### API Client

`apiService.ts` wraps all API calls with:
- Automatic `Authorization: Bearer` header injection
- Token storage in localStorage
- Typed request/response interfaces

---

## Docker Deployment

### Services

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   frontend   │     │     app      │     │      db      │
│  React/Vite  │────▶│   FastAPI    │────▶│  PostgreSQL  │
│  port: 3000  │     │  port: 8000  │     │  port: 5432  │
└──────────────┘     └──────────────┘     └──────────────┘
                           │
                     ┌─────┴─────┐
                     │  data/    │
                     │  indexes/ │  (volume mount)
                     └───────────┘
```

### Startup Sequence (entrypoint.sh)

```
1. python init_database.py        → Create all tables
2. Check if DB is fresh (0 tenants)
   ├── Yes → python seed_prompts.py   → Default prompts
   │       → python seed_users.py     → Demo tenant + users
   └── No  → Skip seeding
3. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | — | JWT signing + Fernet encryption key |
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `OPENAI_API_KEY` | Yes | — | OpenAI API key for embeddings + LLM |
| `OPENROUTER_API_KEY` | No | — | Alternative LLM provider |
| `DEBUG` | No | `false` | Enable Swagger docs at `/docs` |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Token TTL |

---

## Performance

### Typical Latency (per draft generation)

| Step | Time |
|------|------|
| Embedding (query) | ~100ms |
| Vector search (4 sources) | ~200ms |
| Reranking (optional) | ~200ms |
| Intent detection | ~5ms |
| Confidence scoring | ~5ms |
| Prompt building | ~5ms |
| LLM generation | 2–5s |
| **Total** | **~3–6s** |

### Storage

| Data | Storage |
|------|---------|
| Tickets, replies, metadata | PostgreSQL |
| Vector indexes | `.npy` files (~1.5GB per 100K docs) |
| WHMCS credentials | PostgreSQL (encrypted) |

---

## Data Flow: Complete Ticket Lifecycle

```
 ┌──────────┐
 │  WHMCS   │
 └────┬─────┘
      │ POST /whmcs/sync
      ▼
 ┌──────────┐
 │  Ticket  │ stored in DB
 │  (open)  │
 └────┬─────┘
      │ POST /replies/generate
      ▼
 ┌──────────────────────────────────┐
 │         RAG Pipeline             │
 │  Retrieve → Rerank → Score      │
 │  → Build Prompt → LLM Generate  │
 └────────────┬─────────────────────┘
              │
              ▼
 ┌──────────────────┐
 │    AI Draft       │ stored in DB
 │  + confidence     │ with full metadata
 │  + intent         │
 └────────┬─────────┘
          │ Agent reviews in UI
          ▼
 ┌──────────────────┐
 │  Human Review     │
 │  Edit if needed   │
 └────────┬─────────┘
          │ POST /replies/approve
          ▼
 ┌──────────────────┐
 │ Edit Analysis     │ Levenshtein distance
 │ similarity ≥ 70%? │
 └───┬──────────┬───┘
     │          │
     ▼          ▼
 ┌────────┐ ┌────────────┐
 │Example │ │ Correction │
 │ Index  │ │   Index    │
 └────────┘ └────────────┘
     │          │
     └────┬─────┘
          ▼
 ┌──────────────────┐
 │ Future tickets    │
 │ get better drafts │
 │ + safety warnings │
 └──────────────────┘
```

---

## Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Human control first** | No auto-send. All drafts require approval. |
| **Corrections over documents** | Learn from mistakes, not just static KB. |
| **Tenant isolation above all** | ContextVar + TenantQuery + separate FAISS indexes. |
| **Confidence before automation** | Every reply scored 0–100 with breakdown. |
| **Transparency** | Full context sources, intent, and scoring visible to agent. |
