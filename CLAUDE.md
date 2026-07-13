# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A **Financial Advisor AI** — an agentic RAG application that gives high-income earners personalized, framework-based financial guidance grounded in the `Were-Talking-Millions.pdf` knowledge base. This is a mid-year makerspace challenge project structured around 7 tasks (see `TASK_*.md` and `IMPLEMENTATION_SUMMARY.md`). Tasks 1–4 (problem definition through end-to-end prototype) are complete; Tasks 5–7 (evaluation harness, advanced retrieval, finalization) are planned but not yet built.

## Architecture

Three layers, each in a single flat top-level file (no package/module hierarchy):

- **`backend_main.py`** — FastAPI server. The `FinancialAdvisorRAG` class builds the entire RAG pipeline **at import/startup time** in `_initialize()`: loads and chunks the PDF, embeds with OpenAI, and builds a Qdrant vector store **in-memory** (`location=":memory:"`, `force_recreate=True`). This means the PDF is re-embedded on every server start and the vector store does not persist. The RAG chain is `ChatPromptTemplate | ChatAnthropic | StrOutputParser`; retrieval uses `similarity_search_with_score` (k=4) and injects formatted user context ahead of retrieved chunks.
- **`frontend_app.tsx`** — Single Next.js client component (drop into `app/page.tsx`). Sidebar collects a financial profile (salary/assets/debt/timeline/risk); the profile is sent with **every** `/chat` POST rather than persisted server-side by the client. Talks to the backend via `axios` at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).
- **`02_Financial_Advisor_RAG.ipynb`** — Development/experimentation notebook where the RAG pipeline was prototyped before being wrapped into the backend.

### Session & state model
Sessions and user context are held in **process-local dicts** (`sessions`, `users`) in `backend_main.py` — they do not survive a restart and don't scale across workers. Redis (`REDIS_URL`) is imported optionally and intended for production memory but is **not yet wired in**. Both a REST `/chat` and a `/ws/chat/{session_id}` WebSocket path exist and duplicate the retrieve→answer→store logic.

### Key config constants (top of `backend_main.py`)
`EMBEDDING_MODEL` = `text-embedding-3-small`, `LLM_MODEL` = `claude-3-5-sonnet-20241022`, `CHUNK_SIZE`=1000, `CHUNK_OVERLAP`=150, `RETRIEVAL_K`=4. Note: the embeddings/LLM come from different providers (OpenAI for embeddings, Anthropic for generation), so **both `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` are required** for the backend to start. `TAVILY_API_KEY` and `REDIS_URL` are optional.

## Commands

### Backend
```bash
# Install deps (pip path — requirements.txt is pinned with hashes)
pip install -r requirements.txt

# Alternative: uv (sync-deps.sh / sync-deps.bat run `uv sync`)
# Note: there is currently NO pyproject.toml/uv.lock committed, so `uv sync`
# will not work as-is; use pip or generate a pyproject first.

# Run the server (RAG pipeline builds on startup — requires API keys + the PDF present)
python backend_main.py     # serves on http://0.0.0.0:8000
```

API keys are read from environment variables (see `.gitignore` — `.env` is git-ignored). Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and optionally `TAVILY_API_KEY`, `REDIS_URL`.

### Smoke-test the API
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","message":"What is a realistic asset allocation?"}'
```

### Frontend
The `.tsx` and `package.json` are templates, not a scaffolded app. To run:
```bash
# Scaffold a Next.js app, then copy frontend_app.tsx -> app/page.tsx
# and frontend_package.json -> package.json
npm install
npm run dev     # http://localhost:3000
npm run build
npm run lint
```
Set `NEXT_PUBLIC_API_URL` to the backend URL.

### Tests
`pytest` and `httpx`/`black` are listed as dev dependencies, but **no test files exist yet**. `TASK_4_BUILD.md` and `IMPLEMENTATION_SUMMARY.md` contain manual test checklists and curl-based validation only.

## Deployment

Live deployment: **backend on Render, frontend on Vercel** (the FastAPI backend is a persistent process that builds the vector store at startup, so it is *not* a fit for Vercel serverless).

- Frontend (Vercel): https://project-ai-makerspace.vercel.app
- Backend (Render): https://financial-advisor-backend-sifv.onrender.com (health: `/health`)

### Backend → Render
1. render.com → **New → Blueprint** → select this repo. Render reads `render.yaml` (service `financial-advisor-backend`, `startCommand: python backend_main.py`, health check `/health`, Python pinned via `PYTHON_VERSION`).
2. Set the `sync: false` secrets in the dashboard: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` (and optionally `TAVILY_API_KEY`).
3. Deploy, then verify `https://<backend>/health` returns `rag_ready: true`.
4. The app binds `$PORT` (Render-provided) via `os.getenv("PORT")` in `backend_main.py`.

Free-tier caveat: the instance spins down when idle and **re-embeds the entire PDF on every cold start** (slow first request + repeated OpenAI embedding cost). In-process session dicts are also wiped on restart.

### Frontend → Vercel
1. vercel.com → import this repo → **set Root Directory = `frontend`** (critical — otherwise Vercel scans the repo root, detects `backend_main.py`, and fails with "No FastAPI entrypoint found").
2. Add env var **`NEXT_PUBLIC_API_URL`** = the Render backend URL (no trailing slash). This is a `NEXT_PUBLIC_*` var, so it is **inlined at build time** — changing it requires a **redeploy** (uncheck "Use existing Build Cache").
3. For a public URL: **Settings → Deployment Protection → Vercel Authentication → Disabled** (otherwise the site 302-redirects to Vercel SSO), and use the stable production domain, not the per-deployment hash URL.

CORS: the backend currently allows all origins (`allow_origins=["*"]` in `backend_main.py`); tighten to the Vercel domain for production.

## Working notes

- **`requirements.txt` vs `requirements_no_hash.txt`**: the former is the pinned install target; the latter is an unpinned convenience list that also adds `jupyter`/`notebook`.
- Changing chunking, retrieval count, or models means editing the constants block in `backend_main.py`; there is no external config file.
- The system prompt (in `_initialize()`) encodes hard product guardrails: cite sources as `[Source N]`, refuse to give tax advice or recommend specific securities, and answer with decision frameworks rather than yes/no. Preserve these when editing generation logic.
- Deployment target (per docs) is Render for the backend and Vercel for the frontend; no deploy config is committed.
