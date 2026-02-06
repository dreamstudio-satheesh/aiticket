# Database Schema

## Enums

### UserRole
| Value | Description |
|-------|-------------|
| `admin` | Tenant administrator |
| `support_agent` | Support staff |

### TicketStatus
| Value |
|-------|
| `open` |
| `answered` |
| `customer_reply` |
| `closed` |
| `on_hold` |

### KBCategory
| Value |
|-------|
| `product` |
| `pricing` |
| `policy` |
| `sla` |
| `faq` |
| `custom` |

### AuditAction
| Value |
|-------|
| `ticket_synced` |
| `draft_generated` |
| `draft_regenerated` |
| `reply_approved` |
| `reply_edited` |
| `correction_flagged` |
| `kb_indexed` |
| `prompt_changed` |

---

## Tables

### 1. `tenants`

| Column | Type | Nullable | Default | Key | Notes |
|--------|------|----------|---------|-----|-------|
| `id` | Integer | No | auto | PK | |
| `name` | String(255) | No | — | | |
| `slug` | String(100) | No | — | UNIQUE, INDEX | |
| `settings` | JSON | Yes | `{}` | | |
| `is_active` | Boolean | Yes | `true` | | |
| `whmcs_url` | String(500) | Yes | — | | |
| `whmcs_api_identifier` | Text | Yes | — | | Encrypted |
| `whmcs_api_secret` | Text | Yes | — | | Encrypted |
| `created_at` | DateTime | No | `utcnow` | | |
| `updated_at` | DateTime | No | `utcnow` | | Auto-updates |

---

### 2. `users`

| Column | Type | Nullable | Default | Key | Notes |
|--------|------|----------|---------|-----|-------|
| `id` | Integer | No | auto | PK | |
| `tenant_id` | Integer | No | — | FK → `tenants.id` (CASCADE) | |
| `email` | String(255) | No | — | INDEX | |
| `hashed_password` | String(255) | No | — | | |
| `full_name` | String(255) | Yes | — | | |
| `role` | Enum(UserRole) | No | `support_agent` | | |
| `is_active` | Boolean | Yes | `true` | | |
| `created_at` | DateTime | No | `utcnow` | | |
| `updated_at` | DateTime | No | `utcnow` | | Auto-updates |

---

### 3. `tickets`

| Column | Type | Nullable | Default | Key | Notes |
|--------|------|----------|---------|-----|-------|
| `id` | Integer | No | auto | PK | |
| `tenant_id` | Integer | No | — | FK → `tenants.id` (CASCADE) | |
| `whmcs_ticket_id` | Integer | No | — | INDEX | External WHMCS ID |
| `subject` | String(500) | No | — | | |
| `content` | Text | No | — | | |
| `department` | String(100) | Yes | — | | |
| `priority` | String(50) | Yes | — | | |
| `status` | Enum(TicketStatus) | Yes | `open` | | |
| `client_email` | String(255) | Yes | — | | |
| `created_at` | DateTime | No | `utcnow` | | |
| `updated_at` | DateTime | No | `utcnow` | | Auto-updates |

---

### 4. `ai_replies`

| Column | Type | Nullable | Default | Key | Notes |
|--------|------|----------|---------|-----|-------|
| `id` | Integer | No | auto | PK | |
| `ticket_id` | Integer | No | — | FK → `tickets.id` (CASCADE) | |
| `prompt_version_id` | Integer | Yes | — | FK → `prompt_versions.id` (SET NULL) | |
| `ai_reply` | Text | No | — | | Generated content |
| `confidence_score` | Float | No | — | | 0–100 |
| `confidence_breakdown` | JSON | Yes | `{}` | | Component scores |
| `context_sources` | JSON | Yes | `[]` | | Retrieved chunks |
| `reranked_sources` | JSON | Yes | `[]` | | After reranking |
| `intent_detected` | Text | Yes | — | | |
| `tokens_used` | Integer | Yes | — | | |
| `latency_ms` | Integer | Yes | — | | |
| `created_at` | DateTime | No | `utcnow` | | |
| `updated_at` | DateTime | No | `utcnow` | | Auto-updates |

---

### 5. `approved_replies`

| Column | Type | Nullable | Default | Key | Notes |
|--------|------|----------|---------|-----|-------|
| `id` | Integer | No | auto | PK | |
| `ticket_id` | Integer | No | — | FK → `tickets.id` (CASCADE), UNIQUE | One per ticket |
| `ai_reply_id` | Integer | Yes | — | FK → `ai_replies.id` (SET NULL) | |
| `final_reply` | Text | No | — | | Human-approved text |
| `edited` | Boolean | Yes | `false` | | Was AI reply edited? |
| `edit_distance` | Float | Yes | — | | Levenshtein ratio 0–1 |
| `edit_summary` | Text | Yes | — | | AI summary of edits |
| `used_for_training` | Boolean | Yes | `false` | | Indexed as example? |
| `is_correction` | Boolean | Yes | `false` | | Indexed as correction? |
| `created_at` | DateTime | No | `utcnow` | | |
| `updated_at` | DateTime | No | `utcnow` | | Auto-updates |

---

### 6. `prompt_versions`

| Column | Type | Nullable | Default | Key | Notes |
|--------|------|----------|---------|-----|-------|
| `id` | Integer | No | auto | PK | |
| `tenant_id` | Integer | Yes | — | FK → `tenants.id` (CASCADE) | NULL = global prompt |
| `version` | String(50) | No | — | | e.g. "1.0.0" |
| `name` | String(255) | No | — | | |
| `description` | Text | Yes | — | | |
| `system_prompt` | Text | No | — | | |
| `context_template` | Text | No | — | | RAG context injection |
| `task_template` | Text | No | — | | Instruction template |
| `model` | String(100) | Yes | `gpt-4o-mini` | | LLM model name |
| `temperature` | Integer | Yes | `0.3` | | Stored as int ÷ 10 |
| `max_tokens` | Integer | Yes | `1000` | | |
| `is_active` | Boolean | Yes | `false` | | One active per tenant |
| `is_default` | Boolean | Yes | `false` | | Default for new tenants |
| `performance_metrics` | JSON | Yes | `{}` | | Avg confidence, etc. |
| `created_at` | DateTime | No | `utcnow` | | |
| `updated_at` | DateTime | No | `utcnow` | | Auto-updates |

---

### 7. `reranking_configs`

| Column | Type | Nullable | Default | Key | Notes |
|--------|------|----------|---------|-----|-------|
| `id` | Integer | No | auto | PK | |
| `tenant_id` | Integer | Yes | — | FK → `tenants.id` (CASCADE), UNIQUE | NULL = global default |
| `is_enabled` | Boolean | Yes | `true` | | |
| `model_name` | String(255) | Yes | `cross-encoder/ms-marco-MiniLM-L-6-v2` | | |
| `weight_global_kb` | Float | Yes | `0.2` | | 20% weight |
| `weight_tenant_kb` | Float | Yes | `0.3` | | 30% weight |
| `weight_approved_examples` | Float | Yes | `0.35` | | 35% weight |
| `weight_corrections` | Float | Yes | `0.15` | | 15% weight |
| `top_k_initial` | Integer | Yes | `20` | | Initial retrieval count |
| `top_k_rerank` | Integer | Yes | `5` | | After reranking |
| `score_threshold` | Float | Yes | `0.5` | | Min rerank score |
| `settings` | JSON | Yes | `{}` | | |
| `created_at` | DateTime | No | `utcnow` | | |
| `updated_at` | DateTime | No | `utcnow` | | Auto-updates |

---

### 8. `kb_articles`

| Column | Type | Nullable | Default | Key | Notes |
|--------|------|----------|---------|-----|-------|
| `id` | Integer | No | auto | PK | |
| `tenant_id` | Integer | No | — | FK → `tenants.id` (CASCADE) | |
| `title` | String(500) | No | — | | |
| `content` | Text | No | — | | |
| `category` | Enum(KBCategory) | Yes | `custom` | | |
| `tags` | String(500) | Yes | — | | Comma-separated |
| `is_active` | Boolean | Yes | `true` | | |
| `is_indexed` | Boolean | Yes | `false` | | Synced to FAISS? |
| `created_at` | DateTime | No | `utcnow` | | |
| `updated_at` | DateTime | No | `utcnow` | | Auto-updates |

---

### 9. `audit_logs`

| Column | Type | Nullable | Default | Key | Notes |
|--------|------|----------|---------|-----|-------|
| `id` | Integer | No | auto | PK | |
| `tenant_id` | Integer | No | — | FK → `tenants.id` (CASCADE) | |
| `user_id` | Integer | Yes | — | FK → `users.id` (SET NULL) | |
| `action` | Enum(AuditAction) | No | — | INDEX | |
| `entity_type` | String(50) | No | — | | e.g. "ticket", "ai_reply" |
| `entity_id` | Integer | Yes | — | | |
| `details` | JSON | Yes | `{}` | | Action metadata |
| `ticket_id` | Integer | Yes | — | FK → `tickets.id` (SET NULL) | |
| `ai_reply_id` | Integer | Yes | — | FK → `ai_replies.id` (SET NULL) | |
| `created_at` | DateTime | No | `utcnow` | | |
| `updated_at` | DateTime | No | `utcnow` | | Auto-updates |

---

## Relationships Diagram

```
tenants
  ├── 1:N → users
  ├── 1:N → tickets
  │            ├── 1:N → ai_replies
  │            └── 1:1 → approved_replies
  ├── 1:N → prompt_versions ←── ai_replies (N:1)
  ├── 1:1 → reranking_configs
  ├── 1:N → kb_articles
  └── 1:N → audit_logs
```

## Key Design Patterns

- **Every table** has `tenant_id` for multi-tenant isolation (CASCADE delete)
- `approved_replies.ticket_id` is **UNIQUE** — only one approval per ticket
- `reranking_configs.tenant_id` is **UNIQUE** — one config per tenant
- `prompt_versions` and `reranking_configs` allow **NULL tenant_id** for global defaults
- Foreign keys use **SET NULL** for soft references (prompt_version, user in audit) and **CASCADE** for ownership
- All tables include `created_at` and `updated_at` timestamps via `TimestampMixin`
