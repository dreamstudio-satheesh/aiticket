# AI Support Assistant: Backend API Documentation

**Application Name:** AI Support Assistant

**Version:** v1

**Base URL:** `/api/v1`

## 1. Application Setup & Configuration

### Configuration

**File:** `D:\aiagent\app\config.py`

The application uses a `Settings` class to manage environment variables.

- **`app_name`**: "AI Support Assistant"
    
- **`debug`**: Boolean (controls docs endpoint)
    
- **`secret_key`**: Required for JWT signing (from `.env`)
    
- **`database_url`**: PostgreSQL connection string
    
- **`jwt_algorithm`**: "HS256"
    
- **`access_token_expire_minutes`**: 30 (configurable)
    
- **`openai_api_key`**: For LLM completion
    
- **`openrouter_api_key`**: Alternative LLM provider
    

### Main Application

**File:** `D:\aiagent\app\main.py`

- **Framework:** FastAPI
    
- **Middleware:**
    
    - CORS (Allows all origins)
        
    - `TenantMiddleware` (Multi-tenant isolation)
        
- **Health Check:** `GET /health`
    
- **Router Mount:** `/api/v1`
    

## 2. Authentication System

**Routes:** `D:\aiagent\app\api\v1\auth.py` (Prefix: `/auth`)

|   |   |   |   |   |   |
|---|---|---|---|---|---|
|**Endpoint**|**Method**|**Auth**|**Description**|**Request**|**Response**|
|`/auth/login`|POST|None|Login with email/password|`username`, `password` (OAuth2 Form)|`{access_token: str, token_type: "bearer"}`|
|`/auth/register`|POST|None|Register new user for tenant|`email`, `password`, `full_name`, `tenant_slug`|`UserResponse`|
|`/auth/me`|GET|Required|Get current user info|N/A|`UserResponse`|

### Security Components

- **Hashing:** bcrypt (via `passlib`)
    
- **Token Format:** JWT
    
- **Payload:** `{sub: user_id, tenant_id: tenant_id, exp: datetime}`
    
- **Dependency:** `get_current_user` decodes JWT and validates the user exists and is active.
    

## 3. AI Replies & RAG Pipeline

**Routes:** `D:\aiagent\app\api\v1\replies.py` (Prefix: `/replies`)

|   |   |   |   |   |   |
|---|---|---|---|---|---|
|**Endpoint**|**Method**|**Auth**|**Description**|**Request**|**Response**|
|`/replies/generate`|POST|Yes|Generate AI draft reply|`ticket_id`, `use_reranking`|`AIReplyResponse`|
|`/replies/ticket/{id}`|GET|Yes|Get ticket with latest draft|N/A|`TicketWithDraftResponse`|
|`/replies/approve`|POST|Yes|Approve reply (w/ optional edits)|`ai_reply_id`, `final_reply`|Approval Status|
|`/replies/pending`|GET|Yes|Get tickets with drafts pending|`limit`|`List[TicketWithDraftResponse]`|

### RAG Pipeline Flow

1. **Retrieve Context:** Fetches data from 4 weighted sources (Global KB, Tenant KB, Examples, Corrections).
    
2. **Rerank:** Optional reranking of sources.
    
3. **Intent Detection:** Identifies customer intent.
    
4. **Prompt Building:** Constructs system and user prompts.
    
5. **Generation:** Calls LLM.
    
6. **Scoring:** Calculates confidence score based on similarity and safety.
    

**Confidence Formula:**

$$Score = 0.4 \times ExampleSim + 0.3 \times KBSim + 0.2 \times IntentCertainty + 0.1 \times CorrectionSafety$$

## 4. Knowledge Base (KB)

**Routes:** `D:\aiagent\app\api\v1\kb.py` (Prefix: `/kb`)

|   |   |   |   |
|---|---|---|---|
|**Endpoint**|**Method**|**Role**|**Description**|
|`/kb/articles`|POST|ADMIN|Create KB article|
|`/kb/articles`|GET|ANY|List all KB articles|
|`/kb/articles/{id}`|PUT|ADMIN|Update article|
|`/kb/index`|POST|ADMIN|Re-index KB into FAISS|
|`/kb/search`|GET|ANY|Search tenant KB (vector search)|

## 5. Search System

**Routes:** `D:\aiagent\app\api\v1\search.py` (Prefix: `/search`)

|   |   |   |   |
|---|---|---|---|
|**Endpoint**|**Method**|**Auth**|**Description**|
|`/search/global`|GET|None|Search global KB (Public)|
|`/search/tenant`|GET|Yes|Search tenant-specific KB|
|`/search/unified`|GET|Yes|Unified search with weighted merge|

### Unified Search Response

Returns a weighted merge of:

- **Global KB:** 20% weight
    
- **Tenant KB:** 30% weight
    
- **Examples:** 35% weight
    
- **Corrections:** 15% weight
    

## 6. Prompts Management

**Routes:** `D:\aiagent\app\api\v1\prompts.py` (Prefix: `/prompts`)

|   |   |   |   |
|---|---|---|---|
|**Endpoint**|**Method**|**Role**|**Description**|
|`/prompts/`|GET|ANY|List all prompts (global + tenant)|
|`/prompts/active`|POST|ADMIN|Set active prompt for tenant|
|`/prompts/`|POST|ADMIN|Create custom prompt|
|`/prompts/duplicate`|POST|ADMIN|Duplicate prompt for customization|

**Prompt Schema:** Includes `system_prompt`, `context_template`, `task_template`, `model` (e.g., gpt-4o-mini), `temperature`, and `max_tokens`.

## 7. Training & Learning

**Routes:** `D:\aiagent\app\api\v1\examples.py` (Prefix: `/examples`)

Allows the system to learn from human edits.

- **`/examples/`**: List approved replies (used as training/few-shot examples).
    
- **`/examples/stats`**: Statistics on training data.
    
- **`/examples/rebuild-index`**: Rebuilds the FAISS index for examples.
    
- **`/corrections/`**: Tracks significant edits (mistakes) to prevent recurrence.
    

## 8. Weights & Optimization

**Routes:** `D:\aiagent\app\api\v1\weights.py` (Prefix: `/weights`)

Manages the retrieval weights for the RAG pipeline.

- **GET /weights/**: View current weights.
    
- **PUT /weights/**: Update weights (Auto-normalized to 1.0).
    
- **GET /weights/recommend**: Get AI-recommended weights based on historical effectiveness.
    
- **POST /weights/apply-recommendation**: Apply the recommended weights.
    

## 9. Analytics & Audit

**Routes:** `D:\aiagent\app\api\v1\analytics.py` (Prefix: `/analytics`)

- **`/analytics/dashboard`**: Full dashboard metrics (confidence, intent, daily stats).
    
- **`/analytics/metrics`**: Edit rates, approval rates, correction rates.
    
- **`/analytics/history`**: Audit log of all actions.
    

## 10. WHMCS Integration

**Routes:** `D:\aiagent\app\api\v1\whmcs.py` (Prefix: `/whmcs`)

- **`/whmcs/config`**: Configure API credentials (stored encrypted).
    
- **`/whmcs/sync`**: Sync tickets from WHMCS to local DB.
    
- **`/whmcs/tickets`**: List synced tickets.
    

## 11. UI & Architecture

### UI Endpoint

- **`/ui/`**: Returns a simple HTML/JS UI for testing draft generation, ticket review, and approval flows.
    

### Multi-Tenant Architecture

- **Middleware:** `TenantMiddleware` extracts `tenant_id` from the JWT.
    
- **Isolation:** All service queries are filtered by `current_tenant_id` context variable.
    
- **Models:** `User`, `Ticket`, `AIReply`, `KBArticle`, etc., are all tenant-scoped.