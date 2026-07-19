# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- `backend/`: FastAPI service turning natural-language questions into SQL against a local
  SQLite inventory database, using Gemini via LangChain.
  - Explicit pipeline: `plan → generate SQL → validate → execute → synthesize answer`,
    replacing the notebook's opaque `SQLDatabaseChain`.
  - SQL guardrails (`app/core/guardrails.py`): SELECT-only, single-statement, schema-checked
    table/column allowlist, enforced row cap, read-only DB connection.
  - Schema introspection (`app/core/schema_introspection.py`) so prompts and guardrails always
    match the live database.
  - Few-shot example bank (`app/core/few_shot.py`): ChromaDB + HuggingFace sentence-transformer
    embeddings, ported from `experiment/intelligent_query_engine.ipynb`.
  - Built-in observability (`app/core/tracing.py`): in-memory per-request traces with per-stage
    timings, exposed via `GET /api/traces` and `GET /api/traces/{id}`.
  - Validation dataset + eval runner (`app/eval/`): held-out question/gold-SQL pairs scored by
    execution accuracy, via `POST /api/eval/run` or `make eval`.
  - API routes: `POST /api/query`, `GET /api/schema`, `GET /api/traces[/:id]`, `POST /api/eval/run`.
  - SQLite-based seed script replacing the notebooks' MySQL setup, so the app runs with zero
    external services.
- `frontend/`: React + TypeScript (Vite) UI with a query form, example prompts, and tabs for
  Answer / Pipeline trace / Validation, wired to the backend API.
- Root `Makefile`: `install`, `seed`, `backend`, `frontend`, `dev`, `eval`, `build-frontend`,
  `clean`, `help`.
- `backend/.env.example` and `frontend/.env.example` (Gemini API key, model, embedding model,
  CORS origins, `VITE_API_BASE_URL`, etc.).
- `backend/README.md` and rewritten `frontend/README.md` documenting each app.

### Removed
- ...

### Unchanged
- `experiment/*.ipynb` — the original MySQL-based notebook prototype, kept as reference.
