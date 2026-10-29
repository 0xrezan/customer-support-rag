Customer Support RAG Bot — Architecture & Feature Overview
==========================================================

Tech Stack
----------
Backend:   Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Alembic
Frontend:  React 19, TypeScript, Vite, TailwindCSS 4, React Query
Database:  PostgreSQL 16, Redis 7, ChromaDB 0.6
LLM:       OpenAI API (GPT + text-embedding-3-small), Anthropic API (Claude)
Queue:     Dramatiq + Redis broker
Bot:       aiogram 3 (Telegram)
DevOps:    Docker Compose, structlog, pydantic-settings


Codebase
--------
- Python backend:   ~7,800 lines across 133 files
- React frontend:   ~4,600 lines across 117 files
- Total:            ~12,400 lines of handwritten code


Architecture Patterns
---------------------
- Layered DDD: api → schemas → domain (entities, value objects, policies, services) → infrastructure
- Poor-man's DI container: single Container class holds all repos, adapters, services
- Repository pattern for all DB access (async SQLAlchemy)
- Adapter pattern for external integrations (LLM, vector DB, cache)
- Policy objects for pure business rules (chunking, retrieval gating, reranking, answer)
- Application factory: create_app() with lazy router imports
- Async-first: all I/O paths use async/await


RAG Pipeline
------------
Ingestion:
  1. Upload → SHA-256 dedup → store file → create Document row → enqueue Dramatiq task
  2. Parse: PDF (pypdf + optional OCR), Markdown (heading-aware), plain text
  3. Normalize: Unicode NFC, collapse whitespace, preserve paragraphs
  4. Chunk: sliding window (512 chars, 64 overlap, min 50), page-aware
  5. Embed: OpenAI text-embedding-3-small, 1536 dims, batch size 64
  6. Index: ChromaDB upsert with deterministic chunk IDs ({doc_id}:{version}:{page}:{chunk_idx})
  7. BM25 rebuild (if hybrid retrieval enabled)
  8. Version activation: deactivate old versions for same content_hash
  9. Row locking: SELECT ... FOR UPDATE during entire pipeline (prevents concurrent processing)

Query:
  1. Rate limit check (Redis sliding-window per IP)
  2. Cache lookup (Redis, key = SHA-256 of normalized question, TTL 300s)
  3. Embed question via OpenAI
  4. Dense retrieval from ChromaDB (top-K, active chunks only)
  5. Hybrid merge (optional): BM25 keyword search + Reciprocal Rank Fusion
  6. Reranking: 70% semantic similarity + 30% keyword overlap
  7. Answer policy gate: min score 0.25, min hit count 1 → insufficient_context without LLM call
  8. Prompt resolution: try SQL prompt_versions table, fallback to Jinja2 file templates
  9. LLM generation (OpenAI or Anthropic, configurable)
  10. Citation extraction: deduplicated {document_name, page, chunk_id} from chunk metadata
  11. Cache + persist: store in Redis cache and PostgreSQL (question, answer, retrieval trace)


API Endpoints (17)
------------------
Health:
  GET  /api/v1/health/live               Liveness probe
  GET  /api/v1/health/ready              Readiness probe (DB, Redis, Chroma checks)

Chat:
  POST /api/v1/chat/ask                  Submit question → RAG answer + citations

Feedback:
  POST /api/v1/feedback/submit           Thumbs up/down + optional comment

Admin - Documents:
  POST /api/v1/admin/documents/upload    Upload document for ingestion
  GET  /api/v1/admin/documents           List all documents
  GET  /api/v1/admin/documents/{id}      Single document status
  POST /api/v1/admin/documents/{id}/reindex  Re-index document
  DELETE /api/v1/admin/documents/{id}    Soft-delete (default) or hard-delete (?hard=true)

Admin - Bulk:
  POST /api/v1/admin/bulk/upload         Bulk upload multiple documents
  POST /api/v1/admin/bulk/reindex        Reindex all active documents

Dashboard (HTMX):
  GET  /api/v1/dashboard/documents       HTML admin dashboard
  GET  /api/v1/dashboard/documents-table HTMX table fragment
  GET  /api/v1/dashboard/metrics         HTML metrics page

Telegram:
  POST /api/v1/telegram/webhook          Receive Telegram updates
  POST /api/v1/telegram/set-webhook      Register webhook URL
  POST /api/v1/telegram/delete-webhook   Remove webhook


Database Schema (8 tables)
--------------------------
documents          — uploaded files with status, version, content_hash, chunk counts
ingestion_jobs     — background job tracking (status, attempts, errors)
chat_questions     — stored questions with hash, source, user_id
chat_answers       — LLM answers with retrieval_scores, chunk_ids, citations (JSONB), latency
feedback_events    — thumbs up/down ratings with optional comment
prompt_versions    — dynamic prompt template registry (Phase 2)
knowledge_bases    — multi-tenant document isolation (Phase 2)
admin_users        — RBAC with roles (super_admin, admin, operator, viewer)


Dramatiq Background Tasks (5)
------------------------------
ingest_document_task   — full parse-chunk-embed-index pipeline (3 retries, 5-60s backoff)
reindex_document_task  — re-index single document (1 retry)
delete_document_task   — soft-delete + Chroma cleanup (1 retry)
reconcile_task         — SQL/Chroma consistency check
cleanup_old_chats_task — purge old chat logs per retention policy


Security
--------
- Bearer token auth for admin endpoints (hmac.compare_digest, constant-time)
- RBAC: super_admin, admin, operator, viewer roles
- Telegram admin allowlist by user ID
- Webhook secret verification (X-Telegram-Bot-Api-Secret-Token header)
- HMAC-SHA256 webhook signature verification
- Redis sliding-window rate limiter (20 req/60s per IP)
- Security headers middleware (nosniff, DENY framing, XSS protection, referrer policy)
- CORS with configurable origins
- Pydantic input validation (min/max length, regex patterns)
- Secrets via pydantic SecretStr (never logged)
- Insecure defaults blocked in production
- Frontend: XSS sanitization, admin token stored in memory only (not localStorage)


Caching
-------
- Answer cache: Redis, key = answer:{sha256(normalized_question)}, TTL 300s
- Cache bypass on insufficient_context or error results
- BM25 index: in-memory, rebuilt after each ingestion
- Implicit invalidation via TTL (no manual cache-bust on document changes)


Telegram Bot
------------
- aiogram 3 with router-based handlers
- Commands: /start, /help, /ask, /upload, /reindex, /delete, /status
- Admin commands restricted to configured Telegram user IDs
- Supports both polling and webhook modes
- Structured response formatting with citations
- Middleware: rate limiting, logging, error handling


Frontend (React SPA)
--------------------
Architecture: Feature-Sliced Design (app → pages → features → shared)

Chat page:
  - Real-time conversation timeline with user/bot bubbles
  - Source selector (All sources / Documentation / FAQ)
  - Typing indicator during LLM generation
  - Citation list with document name + page number
  - Feedback bar (thumbs up/down) with optimistic updates
  - Feedback comment modal on thumbs-down (optional comment)
  - Retry button on failed messages
  - Auto-scroll to latest message
  - Input validation (1-2000 chars)

Admin dashboard:
  - Token-based login form with validation
  - Health badge (live polling)
  - Metrics cards (total docs, indexed count, total chunks, storage used, system health)
  - Document table with sortable columns (filename, status, version, size, created)
  - Search filter by filename
  - Status dropdown filter (pending, processing, indexed, failed, deleted)
  - URL-driven filters (synced with ?q=...&status=... search params)
  - File upload dropzone with progress indicator
  - Document actions: reindex, delete (with confirmation dialog)
  - Toast notifications for all mutations (success/error)

Cross-cutting:
  - Dark mode (light / dark / system) with CSS variables, persisted in localStorage
  - Theme toggle button (3-state: sun → moon → monitor)
  - ResponseEnvelope auto-unwrapping (Axios interceptor)
  - Zod schema validation on API responses
  - Structured error mapping (401, 403, 404, 413, 422, 500, timeout, network)
  - Auth header injection for admin routes only
  - React Query for server state (caching, refetching, invalidation)
  - Accessible: ARIA labels, roles, keyboard navigation


Testing
-------
Backend:
  - pytest with async support
  - Unit tests for policies, services, utilities
  - Integration tests with test database

Frontend:
  - Vitest + React Testing Library + MSW (Mock Service Worker)
  - 41 tests: unit (API adapters, hooks, utilities) + integration (full page renders)
  - MSW handlers simulate backend ResponseEnvelope format
  - jsdom environment with matchMedia mock for dark mode


Observability
-------------
- structlog with JSON output, correlation/request IDs
- Every LLM answer persisted with: retrieval_scores, chunk_ids, citations, latency_ms,
  llm_provider, llm_model, prompt_version
- Feedback events linked to answers for quality analysis
- Ingestion jobs tracked with status, attempts, error messages
- Health probes: liveness (fast) + readiness (checks all dependencies)


Configuration
-------------
- pydantic-settings with .env file
- Configurable: LLM provider, models, temperatures, chunk sizes, retrieval params,
  reranking weights, rate limits, cache TTL, retention days
- Phase 2 toggles: RERANKING_ENABLED, HYBRID_RETRIEVAL_ENABLED
- Production safety: validation rejects insecure defaults in non-dev environments


DevOps
------
- Docker Compose: 6 services (api, worker, bot, postgres, redis, chroma)
- Alembic migrations (8 migration files)
- run.py: single-command launcher for all services including frontend
- Health checks on all infrastructure containers
- Stale message recovery on startup (Dramatiq dead-letter handling)
