# Demo Guide

A short path through the system: run it, load the sample knowledge base, and see grounded answers with citations in a few minutes.

## 5-Minute Code Tour

1. Start with the README and confirm the system shape: FastAPI backend, React admin/chat UI, Telegram bot, PostgreSQL, Redis, ChromaDB, and background workers.
2. Open `ARCHITECTURE.md` for the deeper architecture overview.
3. Inspect `app/domain/policies/answer_policy.py` and `app/domain/policies/retrieval_policy.py` to see how the app avoids unsupported LLM answers.
4. Inspect `app/domain/services/query_service.py` and `app/domain/services/ingestion_service.py` to see the main RAG and ingestion flows.
5. Inspect `frontend/src/features/chat/` and `frontend/src/features/documents/` to see the user-facing workflows.

## Demo Flow

1. Start the stack:

```bash
uv sync --extra dev
docker compose up -d postgres redis chroma
uv run alembic upgrade head
uv run python run.py
```

2. Open the app:

| View | URL |
|------|-----|
| Chat | `http://localhost:5173/chat` |
| Admin | `http://localhost:5173/admin` |
| API docs | `http://localhost:8000/docs` |
| Health | `http://localhost:8000/api/v1/health/live` |

3. Upload the sample documents from `test_docs/`:

| File | What it demonstrates |
|------|----------------------|
| `test_docs/company_policy.txt` | Returns, shipping, warranty, subscriptions, support contacts, payments, loyalty |
| `test_docs/hr_handbook.txt` | Working hours, remote work, PTO, sick leave, parental leave, performance, benefits |

4. Ask grounded questions:

```text
What is the return window and when are refunds processed?
```

```text
How many PTO days do full-time employees get?
```

```text
What shipping options are available?
```

5. Check the answer quality:

- The answer should be based on retrieved chunks.
- Citations should identify source documents and metadata.
- Weak or unsupported retrieval should not become a confident invented answer.
- Feedback should be captured for later review.

## Verification Commands

```bash
uv run pytest -q
uv run ruff check .
uv run bandit -q -r app -f json
uv run pip-audit
cd frontend
npm run lint
npm run test
npx playwright install chromium
npm run test:e2e
npm run build
npm audit --audit-level=moderate
```
