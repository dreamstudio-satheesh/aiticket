# Software Requirements Specification (SRS)
## AI Support Assistant for Hosting Companies (WHMCS-first)

---

## 1. Purpose & Scope

### 1.1 Purpose
Build a **multi-tenant SaaS AI support assistant** that helps hosting companies draft accurate support ticket replies using:
- Hosting industry common knowledge
- Company-specific products & policies
- Human-in-the-loop corrections

The system **does NOT auto-send replies** in the MVP.

---

### 1.2 Target Users
- Hosting company owners
- Support staff using WHMCS
- Small to medium hosting providers (India-first, global-ready)

---

### 1.3 Out of Scope (MVP)
- Fully autonomous replies
- WhatsApp automation
- Fine-tuning LLM models
- Voice or phone support

---

## 2. Product Overview

### 2.1 Core Value Proposition
- Reduce first-response time
- Maintain full human control
- Improve reply quality over time
- Zero trust and legal risk

---

### 2.2 High-Level Features
1. AI-generated ticket reply drafts
2. Human review and edit
3. Self-improving via corrections
4. Company-specific knowledge isolation
5. Confidence scoring per reply

---

## 3. Functional Requirements

### 3.1 Authentication & Tenancy
- Multi-tenant SaaS architecture
- Each hosting company is a tenant
- Strict tenant-level data isolation

**User Roles**
- Admin
- Support Agent

---

### 3.2 WHMCS Integration
- Fetch support tickets via WHMCS API
- Read-only ticket access (MVP)
- Display AI draft replies per ticket

---

### 3.3 Knowledge Management

#### Global Knowledge Base (Shared)
- WHMCS basics
- cPanel, DirectAdmin, Roundcube
- Hosting concepts (DNS, SSL, email, disk usage)

#### Tenant Knowledge Base (Isolated)
- Products and packages
- Pricing and limits
- Policies and SLAs
- Custom KB articles

---

### 3.4 AI Reply Generation
- Context-aware drafting using RAG
- Uses:
  - Global KB
  - Tenant KB
  - Past approved replies
  - Past corrections

---

### 3.5 Confidence Scoring
- Each AI reply gets a confidence score (0–100)
- Used to decide human review vs future automation

---

### 3.6 Human-in-the-loop Learning
- Capture edited replies
- Store original AI reply and final human reply
- Improve future responses automatically

---

### 3.7 Logging & Audit
- Store prompts, context sources, AI output
- Track confidence score and edits

---

## 4. Non-Functional Requirements

### 4.1 Security
- Tenant-isolated data access
- Encrypted API keys
- No cross-tenant vector retrieval

### 4.2 Performance
- AI draft generation under 5 seconds
- Vector search under 500 ms

### 4.3 Scalability
- Support 1 to 1000 tenants
- Onboard new tenants without redeploy

### 4.4 Cost Control
- RAG-first architecture
- Shared global embeddings
- Small per-tenant vector stores

---

## 5. System Architecture

WHMCS → Addon/Webhook → FastAPI Backend → Intent & Confidence Engine →
- Global Vector Index
- Tenant Vector Index
- Corrections Index → LLM Provider

---

## 6. Data Architecture

### 6.1 Relational Database (PostgreSQL)

**tenants**
- id
- name
- settings
- created_at

**users**
- id
- tenant_id
- role
- email

**tickets**
- id
- tenant_id
- whmcs_ticket_id
- subject
- content

**ai_replies**
- id
- ticket_id
- ai_reply
- confidence_score

**approved_replies**
- id
- ticket_id
- final_reply
- edited (boolean)

---

### 6.2 Vector Stores (FAISS)
- global_kb_index (shared)
- tenant_kb_index (per tenant)
- tenant_examples_index
- tenant_corrections_index

---

## 7. AI & RAG Design

### 7.1 Retrieval Strategy
For each ticket:
1. Search global KB
2. Search tenant KB
3. Search tenant-approved examples
4. Search tenant corrections

Weighted merge produces final context.

---

### 7.2 Prompt Structure

SYSTEM:
You are a hosting support assistant. Never guess.

CONTEXT:
- Global knowledge
- Tenant knowledge
- Approved examples
- Corrections to avoid

TASK:
Draft a professional support reply. Escalate if unsure.

---

### 7.3 Confidence Score Logic

confidence =
- 0.4 × example similarity
- 0.3 × KB similarity
- 0.2 × intent certainty
- 0.1 × correction safety

---

## 8. End-to-End Application Flow

1. Ticket arrives in WHMCS
2. SaaS fetches ticket
3. Intent classified
4. Context retrieved
5. AI drafts reply
6. Admin reviews and edits
7. Final reply saved
8. System learns automatically

---

## 9. MVP Build Plan (Solo Developer)

### Phase 1 – Foundation (Week 1)
- FastAPI setup
- PostgreSQL schema
- Authentication
- Tenant isolation

### Phase 2 – Knowledge System (Week 2)
- Global KB ingestion
- Tenant KB ingestion
- FAISS vector indexes

### Phase 3 – AI Engine (Week 3)
- RAG pipeline
- Prompt templates
- Confidence scoring

### Phase 4 – WHMCS Integration (Week 4)
- Ticket fetch
- Draft reply UI
- Edit tracking

### Phase 5 – Feedback Loop (Week 5)
- Store approved replies
- Store corrections
- Retrieval weighting improvements

---

## 10. Future Phases
- WhatsApp support channel
- Auto-reply above confidence threshold
- Multilingual support
- Analytics dashboard

---

## 11. Core Design Principles

1. Human control first
2. Corrections over documents
3. Tenant isolation above all
4. Confidence before automation
5. SaaS reliability over model hype

---

## 12. Final Notes

This system is:
- Buildable by a solo developer
- Safe for early paying customers
- Scalable to many tenants
- Designed for real-world hosting support

The product is not the AI model.
The product is **knowledge orchestration + safety + learning loops**.

