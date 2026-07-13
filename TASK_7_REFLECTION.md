# Task 7: Reflection & Finalization

## Executive summary
A complete, deployed **agentic RAG** financial-advisor app: a Next.js chat UI on
Vercel talking to a FastAPI + LangChain backend on Render, grounded in two data
sources (a financial-guidance PDF and a 2025 tax-bracket spreadsheet), generated
by `claude-sonnet-5`, with an LLM-judge evaluation harness and hybrid retrieval.

**Live:**
- Frontend: https://project-ai-makerspace.vercel.app
- Backend: https://financial-advisor-backend-sifv.onrender.com/health

## What was built (by task)
| Task | Outcome |
|---|---|
| 1 — Problem | High-income earners lack decision frameworks; analysis paralysis |
| 2 — Solution | Conversational agentic RAG that teaches frameworks, not yes/no |
| 3 — Data | PDF (chunked) + tax xlsx (structured); Qdrant vector store |
| 4 — Prototype | FastAPI backend + Next.js frontend, deployed end-to-end |
| 5 — Evaluation | 15-case harness, LLM judge, baseline report |
| 6 — Retrieval | Hybrid BM25 + dense (RRF), faithfulness guardrail, A/B'd |
| 7 — Finalize | This document |

## What worked well (keep)
- **Framework-quality answers.** Relevance 5.0 and framework quality 5.0 in eval —
  the core value prop (teach decision-making) lands.
- **Out-of-scope discipline.** 3/3 refusals handled; declines stock/crypto picks
  and unrelated questions cleanly.
- **Grounded, cited responses** with page/sheet-level source attribution.
- **Multi-source RAG.** PDF + spreadsheet in one store; tax questions compute
  progressive tax from the real 2025 brackets.
- **Hybrid retrieval** measurably improved tax/keyword grounding and citations.
- **Repeatable evaluation** — every future change can be A/B'd against a saved
  baseline.
- **Clean deploy story** — Render (persistent backend) + Vercel (frontend), all
  config in-repo (`render.yaml`, `vercel.json`), documented in `CLAUDE.md`.

## What to improve (with evidence)
1. **Groundedness (~3.5/5).** The model elaborates with specific figures/quotes
   beyond the retrieved context. Retrieval + a prompt guardrail helped citations
   but not groundedness enough — this is the #1 quality gap.
2. **Retrieval precision (~0.5 top score).** The right *file* is always found,
   but not always the right *passage*; PDF chunking is coarse.
3. **Cold-start cost/latency.** The in-memory Qdrant re-embeds the whole PDF on
   every backend start — slow first request + repeated OpenAI cost on free tier.
4. **No session persistence.** Sessions live in process memory (Redis imported,
   not wired) — lost on restart / not multi-worker safe.
5. **No authentication.** Anyone can use the app; no per-user history.
6. **Eval is small + noisy.** 15 cases and a single stochastic judge run mean
   sub-0.3 deltas aren't reliable signal.

## Next features (prioritized roadmap)
1. **Persist the vector store** (Qdrant Cloud or on-disk) — kills cold-start
   re-embedding; biggest ops win.
2. **Re-ranker** (cross-encoder or LLM) over hybrid candidates — target
   groundedness/citations > 4.5.
3. **Redis-backed sessions** (Upstash) — durable, multi-worker memory.
4. **Social login** (Google/Microsoft/Facebook via Auth.js) — gate the app,
   enable per-user history. (Design already scoped; pending provider OAuth apps.)
5. **Streaming responses** — the `/chat` answer streams token-by-token for UX.
6. **Grow the eval set** to 40-60 cases, average multiple judge runs.
7. **Wire in Tavily** for real-time data (rates, limits) alongside the static KB.
8. **Tighten CORS** to the Vercel origin for production.

## Demo script (~10 minutes)
1. **(1m) Problem & pitch.** Who it's for (high-income non-finance pros) and why
   (frameworks over answers). Show the live URL.
2. **(1m) Profile.** Fill salary/assets/debt/retirement-timeline/risk in the
   sidebar; explain it personalizes retrieval.
3. **(2m) General question** — "What's a realistic asset allocation?" Show the
   framework answer + cited PDF sources with page numbers.
4. **(2m) Tax question** — "Single filer, $150k taxable in 2025, marginal
   bracket and rough tax?" Show it pulls the tax spreadsheet and computes
   progressive tax bracket-by-bracket.
5. **(1m) Out-of-scope** — "What stock should I buy?" Show the graceful decline
   + redirect to a framework.
6. **(1m) Memory** — a follow-up that references the prior turn/profile.
7. **(1.5m) Under the hood.** Architecture diagram (README), two data sources,
   hybrid retrieval, and the evaluation harness + baseline vs Task 6 A/B.
8. **(0.5m) Roadmap** — name the top 2-3 next features and close.

## Final submission checklist
- [x] Public GitHub repo with all code
- [x] Deployed to public URLs (Render + Vercel)
- [x] Written documentation for all 7 tasks (`TASK_1..7_*.md`, `README.md`, `CLAUDE.md`)
- [x] Evaluation harness + baseline + A/B results in-repo (`eval/`)
- [ ] 10-minute demo video (record using the script above)

## Key learnings
- **RAG grounding is a generation problem as much as a retrieval one** — better
  context doesn't stop a capable model from over-elaborating; you need explicit
  faithfulness constraints and/or verification.
- **Evaluation first pays off** — the Task 5 harness turned "it feels good" into
  measurable, comparable numbers and directly justified the Task 6 work.
- **Structured data needs structured handling** — chunking a spreadsheet fails;
  loading it whole + keyword (BM25) retrieval is what made tax answers reliable.
- **Deploy caveats are architectural** — in-memory vector store + in-process
  sessions are fine for a demo but define the first real production tasks.
