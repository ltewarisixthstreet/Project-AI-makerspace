# Financial Advisor AI

An **agentic RAG** web application that gives high-income earners personalized, framework-based financial guidance — grounded in a curated knowledge base (`Were-Talking-Millions.pdf`) rather than generic advice. Instead of yes/no answers, it teaches decision frameworks, cites its sources, and adapts to the user's financial profile.

**Live demo**
- Frontend: https://project-ai-makerspace.vercel.app
- Backend health: https://financial-advisor-backend-sifv.onrender.com/health

> First request after idle time may take ~15s while the free-tier backend wakes.

---

## What it does

- **Conversational RAG** — retrieves relevant passages from the knowledge base and answers with inline `[Source N]` citations (file + page + relevance score).
- **Personalized** — a profile form (salary, assets, debt, years to retirement, risk tolerance) is passed into each request so advice is tailored.
- **Framework-first** — the system prompt steers Claude to teach decision logic, acknowledge trade-offs and behavioral biases, and stay in scope (no specific stock picks, no tax advice — explains principles instead).
- **Session memory** — conversation history and profile persist per session (in-memory).

## Architecture

```
Browser (Next.js / React, Tailwind)
        │  HTTP (axios) — NEXT_PUBLIC_API_URL
        ▼
FastAPI backend (backend_main.py)
        │  LangChain RAG chain
        ├── OpenAI  text-embedding-3-small   (embeddings)
        ├── Qdrant  (in-memory vector store, built at startup)
        └── Anthropic  claude-sonnet-5        (generation)
                 ▲
      Knowledge base:
        • Were-Talking-Millions.pdf   (financial guidance — chunked)
        • tax_slab_2025.xlsx          (2025 US federal tax brackets — structured)
```

- The entire RAG pipeline is built **at startup** (`FinancialAdvisorRAG._initialize()`): load PDF → chunk (1000/150) → embed → build Qdrant (`location=":memory:"`).
- **Multiple data sources:** the PDF is chunked, while spreadsheets (`tax_slab_2025.xlsx`) are loaded whole via `_load_excel_documents()` — one full-table document plus one per row — since tabular data doesn't chunk well. Add more via the `EXCEL_SOURCES` list in `backend_main.py`.
- Retrieval uses `similarity_search_with_score` (k=4); the user profile is prepended to the retrieved context before generation.
- Sessions/users are held in **process-local dicts** (Redis is imported but not yet wired in).

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind v4, axios |
| Backend | FastAPI, Uvicorn, LangChain |
| Embeddings | OpenAI `text-embedding-3-small` |
| LLM | Anthropic `claude-sonnet-5` |
| Vector store | Qdrant (in-memory) |
| Tooling | `uv` (Python env), Python 3.11 |
| Hosting | Render (backend) + Vercel (frontend) |

## Project structure

```
├── backend_main.py            # FastAPI app + RAG pipeline
├── frontend/                  # Next.js app (app/page.tsx = chat UI)
├── Were-Talking-Millions.pdf  # Knowledge base (financial guidance, PDF)
├── tax_slab_2025.xlsx         # Knowledge base (2025 US federal tax brackets)
├── 02_Financial_Advisor_RAG.ipynb  # Dev/experimentation notebook
├── pyproject.toml / uv.lock   # Python deps (uv)
├── requirements.txt           # Exported from the lock (Render build)
├── render.yaml                # Render blueprint (backend)
├── frontend/vercel.json       # Vercel config (frontend)
├── .env.example               # Env var template
├── CLAUDE.md                  # Architecture + deployment notes
└── TASK_1..4_*.md             # Project write-ups (problem → build)
```

## Local development

Requires Python 3.10+ (`uv` recommended), Node 18+, and API keys.

### Backend
```bash
cp .env.example .env         # fill in OPENAI_API_KEY and ANTHROPIC_API_KEY
uv sync --extra dev          # create .venv and install deps
uv run python backend_main.py   # serves http://localhost:8000
```
Smoke test:
```bash
curl http://localhost:8000/health
```

### Frontend
```bash
cd frontend
npm install
# .env.local -> NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                  # serves http://localhost:3000
```

## Environment variables

| Var | Where | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | backend | embeddings (required) |
| `ANTHROPIC_API_KEY` | backend | generation (required) |
| `TAVILY_API_KEY` | backend | optional web search (not yet wired in) |
| `REDIS_URL` | backend | optional session store (not yet wired in) |
| `NEXT_PUBLIC_API_URL` | frontend | backend base URL (**inlined at build time**) |

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health + `rag_ready` |
| `POST` | `/chat` | Ask a question (message + optional user_context) |
| `GET` | `/session/{id}` | Conversation history for a session |
| `POST` | `/session/{id}/context` | Update a session's profile |
| `DELETE` | `/session/{id}` | Delete a session |
| `WS` | `/ws/chat/{id}` | WebSocket chat (REST is the primary path) |

## Deployment

Backend on **Render** (persistent process), frontend on **Vercel**. See the **Deployment** section of [`CLAUDE.md`](CLAUDE.md) for step-by-step instructions and gotchas (Vercel Root Directory, `NEXT_PUBLIC_API_URL` build-time inlining, Vercel Auth, `$PORT`).

## Known limitations

- **Cold-start cost** — the vector store is in-memory and re-embeds the whole PDF on every backend start; on free tiers this means slow cold starts and repeated embedding cost.
- **Session persistence** — sessions live in process memory and are lost on restart (Redis not yet wired in).
- **CORS** — currently allows all origins; tighten to the frontend domain for production.
- **Tavily / real-time data** — planned but not yet integrated.

## Project tasks

All seven tasks are complete (see the `TASK_*.md` write-ups):
- **Tasks 1–3** — problem definition, solution design, data strategy
- **Task 4** — end-to-end prototype, deployed to Render + Vercel
- **Task 5** — evaluation harness + baseline (`eval/`, `TASK_5_EVALUATION.md`)
- **Task 6** — hybrid retrieval (BM25 + dense) + faithfulness guardrail, A/B'd (`TASK_6_ADVANCED_RETRIEVAL.md`)
- **Task 7** — reflection, demo script, finalization (`TASK_7_REFLECTION.md`)

Next features (from Task 7): persist the vector store, add a re-ranker, Redis-backed
sessions, social login, and streaming responses.
