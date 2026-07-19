# IQE Frontend

React + TypeScript + Vite UI for the Intelligent Query Engine. Lets you ask natural-language
questions about the t-shirt inventory and see the answer, the generated SQL, and a live trace
of the backend's plan → generate SQL → validate → execute → answer pipeline.

## Run

From the repo root, prefer `make frontend` (or `make dev` to run backend + frontend together).
To run directly:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The backend must be running (see `backend/README.md`) and
`VITE_API_BASE_URL` in `.env` must point at it (defaults to `http://localhost:8000`).

## Structure

- `src/api/client.ts` — typed fetch client for the backend API
- `src/types/api.ts` — request/response types mirrored from the backend's Pydantic schemas
- `src/components/`
  - `QueryForm` — question input + example prompts
  - `ResultPanel` — answer, generated SQL, plan, and result rows
  - `TracePanel` — per-stage pipeline trace with timings
  - `SchemaSidebar` — live DB schema from `/api/schema`
  - `EvalPanel` — runs the backend's validation dataset and shows pass/fail per case

## Build

```bash
npm run build   # tsc -b && vite build
```
