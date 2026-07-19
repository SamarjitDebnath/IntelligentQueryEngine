# IQE Backend

FastAPI backend for the Intelligent Query Engine: turns natural-language questions
into SQL against a local SQLite inventory database, using Google Gemini via LangChain.
A small few-shot example bank (ChromaDB + HuggingFace embeddings) is used to steer the
SQL generation toward known-good query patterns.

## Run

From the repo root, prefer `make backend` (see the top-level Makefile). To run directly:

```bash
cd backend
uv sync
uv run python -m app.db.seed   # create + seed the SQLite database
uv run uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs
