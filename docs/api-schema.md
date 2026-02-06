# API Schema

**Base URL:** `http://localhost:8000/api/v1`

**Authentication:** JWT Bearer Token (via `Authorization: Bearer <token>` header)

---

## 1. Authentication (`/auth`)

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | POST | `/auth/login` | Login with email & password | No |
| 2 | POST | `/auth/register` | Register new user for a tenant | No |
| 3 | GET | `/auth/me` | Get current authenticated user | Required |

### POST `/auth/login`

**Request:** `application/x-www-form-urlencoded` (OAuth2 form)

| Field | Type | Required |
|-------|------|----------|
| `username` | string (email) | Yes |
| `password` | string | Yes |

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### POST `/auth/register`

**Request Body:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `email` | string | Yes | |
| `password` | string | Yes | |
| `full_name` | string | No | |
| `tenant_slug` | string | Yes | Must match existing tenant |

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "support_agent",
  "tenant_id": 1,
  "is_active": true
}
```

### GET `/auth/me`

**Response:** Same as register response (`UserResponse`)

---

## 2. Knowledge Base (`/kb`)

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | POST | `/kb/articles` | Create KB article | Admin |
| 2 | GET | `/kb/articles` | List all KB articles | Required |
| 3 | GET | `/kb/articles/{article_id}` | Get specific article | Required |
| 4 | PUT | `/kb/articles/{article_id}` | Update article | Admin |
| 5 | DELETE | `/kb/articles/{article_id}` | Delete article | Admin |
| 6 | POST | `/kb/articles/bulk` | Bulk create articles | Admin |
| 7 | POST | `/kb/index` | Re-index all articles into FAISS | Admin |
| 8 | GET | `/kb/search` | Search tenant KB | Required |
| 9 | GET | `/kb/stats` | Get KB index stats | Required |

### POST `/kb/articles`

**Request Body:**

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `title` | string | Yes | |
| `content` | string | Yes | |
| `category` | KBCategory enum | No | `custom` |
| `tags` | string | No | Comma-separated |

**Response:** `KBArticleResponse` — all fields from request + `id`, `tenant_id`, `is_active`, `is_indexed`, `created_at`, `updated_at`

### PUT `/kb/articles/{article_id}`

**Request Body:** All fields optional — `title`, `content`, `category`, `tags`, `is_active`

### POST `/kb/articles/bulk`

**Request Body:**
```json
{
  "articles": [
    { "title": "...", "content": "...", "category": "faq" },
    { "title": "...", "content": "..." }
  ]
}
```

**Response:** `{ "created": 5 }`

### POST `/kb/index`

**Response:** `{ "indexed_chunks": 42 }`

### GET `/kb/search`

| Query Param | Type | Required | Default |
|-------------|------|----------|---------|
| `q` | string | Yes | |
| `top_k` | int | No | 5 |

**Response:** `List[KBSearchResult]` — `content`, `score`, `source`, `source_type`

### GET `/kb/stats`

**Response:** KB index statistics (chunk count, article count, etc.)

---

## 3. Search (`/search`)

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | GET | `/search/global` | Search global knowledge base | No |
| 2 | GET | `/search/tenant` | Search tenant KB | Required |
| 3 | GET | `/search/examples` | Search approved examples | Required |
| 4 | GET | `/search/unified` | Search all sources (weighted merge) | Required |

**Common Query Params:**

| Query Param | Type | Required | Default |
|-------------|------|----------|---------|
| `q` | string | Yes | |
| `top_k` | int | No | 5 |

### GET `/search/global`

**Response:**
```json
[
  { "content": "...", "score": 0.85, "source": "global_kb", "source_type": "global_kb" }
]
```

### GET `/search/unified`

**Response:**
```json
{
  "global_kb": [ { "content": "...", "score": 0.85 } ],
  "tenant_kb": [ ... ],
  "examples": [ ... ],
  "corrections": [ ... ],
  "merged": [ ... ],
  "formatted_context": "Formatted string for LLM prompt"
}
```

---

## 4. Prompt Versions (`/prompts`)

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | GET | `/prompts/` | List all prompts (global + tenant) | Required |
| 2 | GET | `/prompts/active` | Get active prompt for tenant | Required |
| 3 | POST | `/prompts/active` | Set active prompt | Admin |
| 4 | POST | `/prompts/` | Create custom prompt | Admin |
| 5 | GET | `/prompts/{prompt_id}` | Get specific prompt | Required |
| 6 | PUT | `/prompts/{prompt_id}` | Update tenant prompt | Admin |
| 7 | DELETE | `/prompts/{prompt_id}` | Delete tenant prompt | Admin |
| 8 | POST | `/prompts/duplicate` | Duplicate prompt for customization | Admin |

### POST `/prompts/`

**Request Body:**

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `name` | string | Yes | |
| `version` | string | No | |
| `description` | string | No | |
| `system_prompt` | string | Yes | |
| `context_template` | string | Yes | |
| `task_template` | string | Yes | |
| `model` | string | No | `gpt-4o-mini` |
| `temperature` | int | No | `0.3` |
| `max_tokens` | int | No | `1000` |

### POST `/prompts/active`

**Request Body:** `{ "prompt_id": 3 }`

### POST `/prompts/duplicate`

**Request Body:** `{ "prompt_id": 1, "new_name": "My Custom Prompt" }`

**Response:** `PromptVersionResponse` — all fields + `id`, `tenant_id`, `is_active`, `is_default`, `performance_metrics`, `created_at`, `updated_at`

---

## 5. WHMCS Integration (`/whmcs`)

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | POST | `/whmcs/config` | Configure WHMCS credentials | Admin |
| 2 | GET | `/whmcs/config` | Get WHMCS config status | Required |
| 3 | GET | `/whmcs/departments` | Get WHMCS departments | Required |
| 4 | POST | `/whmcs/sync` | Sync tickets from WHMCS | Required |
| 5 | GET | `/whmcs/tickets` | List synced tickets | Required |
| 6 | GET | `/whmcs/tickets/pending` | Get tickets needing AI response | Required |
| 7 | GET | `/whmcs/tickets/{ticket_id}` | Get specific ticket | Required |

### POST `/whmcs/config`

**Request Body:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `whmcs_url` | string | Yes | e.g. `https://billing.example.com` |
| `api_identifier` | string | Yes | Encrypted at rest |
| `api_secret` | string | Yes | Encrypted at rest |

**Response:**
```json
{
  "whmcs_url": "https://billing.example.com",
  "is_configured": true,
  "connection_valid": true
}
```

### POST `/whmcs/sync`

**Request Body:**

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `status` | string | No | |
| `limit` | int | No | |

**Response:**
```json
{
  "synced_count": 10,
  "tickets": [ { "id": 1, "subject": "...", ... } ]
}
```

### GET `/whmcs/tickets`

| Query Param | Type | Required | Default |
|-------------|------|----------|---------|
| `status` | string | No | |
| `page` | int | No | 0 |
| `limit` | int | No | 25 |

**Response:**
```json
{
  "tickets": [ ... ],
  "total": 50,
  "page": 0,
  "limit": 25
}
```

### GET `/whmcs/tickets/pending`

| Query Param | Type | Required | Default |
|-------------|------|----------|---------|
| `limit` | int | No | 10 |

**Response:** `List[TicketResponse]` — tickets with status `open` or `customer_reply`

---

## 6. AI Replies (`/replies`)

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | POST | `/replies/generate` | Generate AI draft reply | Required |
| 2 | GET | `/replies/ticket/{ticket_id}` | Get ticket with latest draft | Required |
| 3 | GET | `/replies/ticket/{ticket_id}/history` | Get all AI replies for ticket | Required |
| 4 | POST | `/replies/approve` | Approve reply with optional edits | Required |
| 5 | GET | `/replies/pending` | Get drafts pending approval | Required |

### POST `/replies/generate`

**Request Body:**

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `ticket_id` | int | Yes | |
| `use_reranking` | bool | No | |

**Response:**
```json
{
  "id": 1,
  "ticket_id": 5,
  "ai_reply": "Dear customer, ...",
  "confidence_score": 78.5,
  "confidence_level": "medium",
  "confidence_breakdown": {
    "example_similarity": 0.82,
    "kb_similarity": 0.75,
    "intent_certainty": 0.70,
    "correction_safety": 0.90
  },
  "recommendations": ["Review KB match", "..."],
  "should_escalate": false,
  "intent_detected": "billing_inquiry",
  "tokens_used": 450,
  "latency_ms": 1200,
  "prompt_version_id": 1,
  "created_at": "2025-01-01T00:00:00"
}
```

### POST `/replies/approve`

**Request Body:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `ai_reply_id` | int | Yes | |
| `final_reply` | string | Yes | Can be edited version |

**Response:**
```json
{
  "message": "Reply approved",
  "approved_reply_id": 1,
  "edited": true,
  "is_correction": false,
  "indexed_for_learning": true
}
```

### GET `/replies/ticket/{ticket_id}`

**Response:**
```json
{
  "id": 5,
  "subject": "...",
  "content": "...",
  "status": "open",
  "draft": { /* AIReplyResponse or null */ },
  "has_approved_reply": false
}
```

### GET `/replies/pending`

| Query Param | Type | Required | Default |
|-------------|------|----------|---------|
| `limit` | int | No | 10 |

**Response:** `List[TicketWithDraftResponse]`

---

## 7. Analytics (`/analytics`)

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | GET | `/analytics/dashboard` | Full dashboard data | Required |
| 2 | GET | `/analytics/metrics` | Edit metrics for period | Required |
| 3 | GET | `/analytics/confidence` | Confidence accuracy analysis | Required |
| 4 | GET | `/analytics/history` | Edit history audit log | Required |
| 5 | GET | `/analytics/corrections` | Correction history | Required |

**Common Query Param:** `days` (int, default: 30, range: 1–365)

### GET `/analytics/dashboard`

**Response:**
```json
{
  "metrics": {
    "total_drafts": 100,
    "total_approved": 80,
    "approval_rate": 80.0,
    "edited_count": 30,
    "edit_rate": 37.5,
    "correction_count": 5,
    "correction_rate": 6.25,
    "avg_confidence": 72.5,
    "avg_similarity": 0.85,
    "avg_latency_ms": 1100
  },
  "confidence_accuracy": {
    "high_confidence_edit_rate": 15.0,
    "medium_confidence_edit_rate": 40.0,
    "low_confidence_edit_rate": 70.0,
    "avg_confidence_edited": 55.0,
    "avg_confidence_unedited": 82.0
  },
  "intent_performance": { ... },
  "daily_stats": [
    { "date": "2025-01-01", "drafts": 5, "approved": 4, "edited": 1 }
  ]
}
```

### GET `/analytics/history`

| Query Param | Type | Required | Default |
|-------------|------|----------|---------|
| `ticket_id` | int | No | |
| `limit` | int | No | 50 (max: 200) |

**Response:**
```json
[
  {
    "id": 1,
    "action": "reply_approved",
    "entity_type": "approved_reply",
    "entity_id": 1,
    "ticket_id": 5,
    "details": { ... },
    "created_at": "2025-01-01T00:00:00"
  }
]
```

---

## 8. Training Examples (`/examples`)

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | GET | `/examples/` | List approved replies for training | Required |
| 2 | GET | `/examples/stats` | Training example statistics | Required |
| 3 | GET | `/examples/{approved_id}` | Detailed view with diff | Required |
| 4 | POST | `/examples/rebuild-index` | Rebuild examples FAISS index | Admin |
| 5 | POST | `/examples/{approved_id}/remove-from-training` | Remove from training | Admin |
| 6 | POST | `/examples/{approved_id}/mark-correction` | Mark as correction | Admin |

### GET `/examples/`

| Query Param | Type | Required | Default |
|-------------|------|----------|---------|
| `include_corrections` | bool | No | false |
| `limit` | int | No | 50 (max: 200) |
| `offset` | int | No | 0 |

**Response:**
```json
[
  {
    "id": 1,
    "ticket_id": 5,
    "ticket_subject": "...",
    "ticket_content": "...",
    "ai_reply": "...",
    "final_reply": "...",
    "edited": true,
    "edit_distance": 0.15,
    "is_correction": false,
    "used_for_training": true,
    "ai_confidence": 78.5,
    "created_at": "2025-01-01T00:00:00"
  }
]
```

### GET `/examples/stats`

**Response:**
```json
{
  "total_approved": 80,
  "indexed_examples": 65,
  "corrections": 5,
  "edited_replies": 30,
  "edit_rate": 37.5,
  "index_chunks": 130
}
```

### GET `/examples/{approved_id}`

**Response:** Includes full ticket detail, AI reply detail, final reply, diff lines, edit distance

### POST `/examples/rebuild-index`

**Response:** `{ "indexed_count": 65, "message": "..." }`

---

## 9. Corrections Learning (`/corrections`)

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | GET | `/corrections/` | List corrections | Required |
| 2 | GET | `/corrections/stats` | Correction statistics | Required |
| 3 | GET | `/corrections/search` | Search past corrections | Required |
| 4 | GET | `/corrections/{correction_id}` | Detailed view with diff | Required |
| 5 | POST | `/corrections/rebuild-index` | Rebuild corrections FAISS index | Admin |

### GET `/corrections/`

| Query Param | Type | Required | Default |
|-------------|------|----------|---------|
| `intent` | string | No | |
| `limit` | int | No | 50 (max: 200) |
| `offset` | int | No | 0 |

**Response:**
```json
[
  {
    "id": 1,
    "ticket_id": 5,
    "ticket_subject": "...",
    "ai_reply_preview": "...",
    "final_reply_preview": "...",
    "edit_summary": "Changed pricing info",
    "edit_distance": 0.45,
    "ai_confidence": 65.0,
    "intent": "billing_inquiry",
    "created_at": "2025-01-01T00:00:00"
  }
]
```

### GET `/corrections/stats`

**Response:**
```json
{
  "total_corrections": 5,
  "avg_original_confidence": 58.0,
  "avg_edit_distance": 0.42,
  "by_intent": { "billing_inquiry": 2, "technical_issue": 3 },
  "index_chunks": 10
}
```

### GET `/corrections/search`

| Query Param | Type | Required | Default |
|-------------|------|----------|---------|
| `q` | string | Yes | |
| `top_k` | int | No | 3 (max: 10) |

**Response:**
```json
[
  {
    "content": "...",
    "score": 0.82,
    "source": "corrections",
    "edit_summary": "...",
    "original_confidence": 55.0,
    "intent": "billing_inquiry"
  }
]
```

---

## 10. Retrieval Weights (`/weights`)

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | GET | `/weights/` | Get current weights | Required |
| 2 | PUT | `/weights/` | Update weights | Admin |
| 3 | GET | `/weights/effectiveness` | Source effectiveness analysis | Required |
| 4 | GET | `/weights/recommend` | Get recommended weights | Required |
| 5 | POST | `/weights/apply-recommendation` | Apply recommended weights | Admin |
| 6 | GET | `/weights/presets` | List weight presets | No |
| 7 | POST | `/weights/apply-preset` | Apply a preset | Admin |

### GET `/weights/`

**Response:**
```json
{
  "global_kb": 0.2,
  "tenant_kb": 0.3,
  "examples": 0.35,
  "corrections": 0.15
}
```

### PUT `/weights/`

**Request Body:** All values 0–1, auto-normalized to sum to 1.0

| Field | Type | Required |
|-------|------|----------|
| `global_kb` | float | Yes |
| `tenant_kb` | float | Yes |
| `examples` | float | Yes |
| `corrections` | float | Yes |

### GET `/weights/effectiveness`

| Query Param | Type | Required | Default |
|-------------|------|----------|---------|
| `days` | int | No | 30 |

**Response:**
```json
{
  "global_kb": { "total": 50, "unedited": 40, "effectiveness": 0.8, "avg_score": 0.72 },
  "tenant_kb": { "total": 50, "unedited": 45, "effectiveness": 0.9, "avg_score": 0.85 },
  "example": { "total": 50, "unedited": 42, "effectiveness": 0.84, "avg_score": 0.78 },
  "correction": { "total": 20, "unedited": 18, "effectiveness": 0.9, "avg_score": 0.65 }
}
```

### GET `/weights/recommend`

**Response:**
```json
{
  "weights": { "global_kb": 0.15, "tenant_kb": 0.35, "examples": 0.35, "corrections": 0.15 },
  "reasoning": { "global_kb": "Lower: below average effectiveness", "..." },
  "confidence": 0.75
}
```

### GET `/weights/presets`

**Response:**
```json
{
  "balanced": { "description": "Equal weights", "weights": { ... } },
  "kb_heavy": { "description": "Prioritize knowledge base", "weights": { ... } },
  "examples_heavy": { "description": "Prioritize examples", "weights": { ... } }
}
```

### POST `/weights/apply-preset`

**Request Body:** `{ "preset": "balanced" }`

---

## 11. Playground (`/playground`)

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | POST | `/playground/generate` | Test RAG pipeline without a real ticket | Required |

### POST `/playground/generate`

**Request Body:**

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `subject` | string | No | |
| `content` | string | Yes | |
| `use_reranking` | bool | No | |

**Response:**
```json
{
  "id": "playground_abc123",
  "role": "assistant",
  "content": "Dear customer, ...",
  "confidence": 72.5,
  "timestamp": "2025-01-01T00:00:00",
  "intent_detected": "billing_inquiry",
  "confidence_breakdown": { ... },
  "recommendations": [ ... ],
  "context_sources": [ ... ],
  "latency_ms": 1100
}
```

---

## 12. UI (`/ui`)

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | GET | `/ui/` | HTML interface for reviewing AI drafts | No |

> Not included in OpenAPI schema. Serves a simple HTML page.

---

## 13. Root

| # | Method | Path | Description | Auth |
|---|--------|------|-------------|------|
| 1 | GET | `/` | Health check | No |

**Response:** `{ "message": "AI Support Assistant API v1" }`

---

## Summary

| Module | Endpoints | Auth Required |
|--------|-----------|---------------|
| Authentication | 3 | Mixed |
| Knowledge Base | 9 | Mixed (Admin for writes) |
| Search | 4 | Mixed (global is public) |
| Prompt Versions | 8 | Mixed (Admin for writes) |
| WHMCS Integration | 7 | Mixed (Admin for config) |
| AI Replies | 5 | All |
| Analytics | 5 | All |
| Training Examples | 6 | Mixed (Admin for writes) |
| Corrections | 5 | Mixed (Admin for writes) |
| Retrieval Weights | 7 | Mixed (Admin for writes) |
| Playground | 1 | Required |
| UI | 1 | None |
| Root | 1 | None |
| **Total** | **62** | |

## Confidence Levels

| Level | Score Range |
|-------|------------|
| `high` | 75–100 |
| `medium` | 50–74 |
| `low` | 25–49 |
| `very_low` | 0–24 |
