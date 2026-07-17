# Deliverables Traceability Matrix

This document maps every task deliverable (Tasks 1–7) to its **exact code or artifact location** in the repository. Line numbers were verified against the code at commit `ea26a02` on `master`.

> **Legend**
> - ✅ **Implemented** — realized in running code.
> - 📄 **Doc-only** — a written artifact (design/spec/reflection); no code counterpart expected.
> - ⚠️ **Partial** — specified but only partly wired into the running system.
> - ❌ **Not implemented** — specified in a doc but absent from code (future work).

**Key files:** `backend_main.py` (629 lines, FastAPI + RAG), `frontend/app/page.tsx` (= `frontend_app.tsx`, Next.js UI), `02_Financial_Advisor_RAG.ipynb` (prototype), `eval/` (evaluation harness), `render.yaml` (deploy).

---

## Task 1 — Problem Definition & Audience

| Deliverable | Location | Line/Section | Status |
|---|---|---|---|
| Problem statement (1 sentence) | `TASK_1_Problem_Definition.md` | "## Problem Statement" (L5) | 📄 |
| Why this is a problem (who/what/today/gap) | `TASK_1_Problem_Definition.md` | "## Why This Is a Problem" (L9–45) | 📄 |
| User persona | `TASK_1_Problem_Definition.md` | "### Who Has the Problem?" (L11–18) | 📄 |
| Current-workflow diagram | `TASK_1_Problem_Definition.md` | "## Current Workflow Diagram" (L49–81) | 📄 |
| Pain points table | `TASK_1_Problem_Definition.md` | "### Critical Pain Points" (L85–94) | 📄 |
| Evaluation questions / I-O pairs | `TASK_1_Problem_Definition.md` | "## Evaluation Questions" (L106–144) | ✅ realized in `eval/dataset.json` + notebook test cells 26–28 |
| Solution requirements / success metric | `TASK_1_Problem_Definition.md` | L158–177 | 📄 |
| Out-of-scope / guardrails list | `TASK_1_Problem_Definition.md` | "### Out of Scope" (L168–174) | ✅ enforced as system-prompt guardrails in `backend_main.py` L217–238 (esp. L237) |

## Task 2 — Solution Design & Architecture

| Deliverable | Location | Line/Section | Status |
|---|---|---|---|
| Solution statement (1 sentence) | `TASK_2_Solution_Design.md` | L5 | 📄 |
| Infrastructure / architecture diagram | `TASK_2_Solution_Design.md` | L11–63 (mirrored `README.md` L22–40) | 📄 |
| LLM choice + justification | `TASK_2_Solution_Design.md` | L71–72 | ✅ `backend_main.py` `LLM_MODEL` L56, `ChatAnthropic` L213 — ⚠️ *drift: doc says Claude 3.5 Sonnet, code uses `claude-sonnet-5`* |
| Agent orchestration (LangChain) | `TASK_2_Solution_Design.md` | L74–75 | ✅ `backend_main.py` imports L29–35, RAG chain L252 |
| Embedding model choice | `TASK_2_Solution_Design.md` | L77–78 | ✅ `backend_main.py` `EMBEDDING_MODEL` L55, `OpenAIEmbeddings` L148 |
| Vector DB choice (Qdrant) | `TASK_2_Solution_Design.md` | L80–81 | ✅ `backend_main.py` `QdrantVectorStore.from_documents(...)` L191–197 |
| Backend framework (FastAPI) | `TASK_2_Solution_Design.md` | L87–88 | ✅ `backend_main.py` `FastAPI(...)` L414–418 |
| Memory / session store (Redis) | `TASK_2_Solution_Design.md` | L90–91, L268–292 | ⚠️ redis imported optionally (`backend_main.py` L38–42, `REDIS_URL` L52) but **not wired in**; sessions use process-local dicts L433–434 |
| Deployment (Vercel + Render) | `TASK_2_Solution_Design.md` | L93–94 | ✅ `render.yaml` + `frontend/`; documented in `CLAUDE.md` / `README.md` L115–117 |
| Web search tool (Tavily) | `TASK_2_Solution_Design.md` | L100–101 | ❌ only `TAVILY_API_KEY` env read (`backend_main.py` L51); no client/call. README L124 confirms "not yet integrated" |
| Calculation engine (Python) | `TASK_2_Solution_Design.md` | L103–104 | ❌ no calculator code found |
| Context builder | `TASK_2_Solution_Design.md` | L106–107 | ✅ profile formatting `backend_main.py` L474–485, prepend L392–394 |
| Frontend framework (Next.js + React) | `TASK_2_Solution_Design.md` | L113–114 | ✅ `frontend/` app — ⚠️ *drift: doc says Next 14/React, build is Next 16/React 19* |
| Chat UI libs (Recharts + shadcn/ui) | `TASK_2_Solution_Design.md` | L116–117 | ❌ UI uses plain React + Tailwind + axios; no Recharts/shadcn |
| Eval framework (LLM-as-Judge) + metrics | `TASK_2_Solution_Design.md` | L121–133 | ✅ realized in Task 5 `eval/` |
| Agent workflow diagram | `TASK_2_Solution_Design.md` | L137–254 | 📄 (code is a simpler retrieve-then-answer chain, not a multi-tool agent loop) |
| Workflow explanation | `TASK_2_Solution_Design.md` | L258–264 | 📄 |
| Memory architecture spec | `TASK_2_Solution_Design.md` | L268–292 | ⚠️ per-session in-process only (`backend_main.py` L462–501); no decision log / Redis persistence |
| Data-flow example | `TASK_2_Solution_Design.md` | L296–310 | 📄 |

## Task 3 — Data Strategy & Chunking

| Deliverable | Location | Line/Section | Status |
|---|---|---|---|
| Chunk size + rationale | `TASK_3_Data_Strategy.md` | L15–25 | ✅ `backend_main.py` `CHUNK_SIZE = 1000` L57 |
| Chunk overlap + rationale | `TASK_3_Data_Strategy.md` | L27–33 | ✅ `backend_main.py` `CHUNK_OVERLAP = 150` L58 |
| Chunking strategy (RecursiveCharacterTextSplitter + separators) | `TASK_3_Data_Strategy.md` | L35–72 | ✅ `backend_main.py` `RecursiveCharacterTextSplitter(...)` L169–174 |
| Data source 1: `Were-Talking-Millions.pdf` | `TASK_3_Data_Strategy.md` | L78–108 | ✅ loaded via `PyPDFLoader` `backend_main.py` L152–157 |
| Data source 2: Tavily real-time | `TASK_3_Data_Strategy.md` | L111–158 | ❌ not wired in (env key only, L51); README L124 confirms |
| Data-source interaction (PDF + search hybrid) | `TASK_3_Data_Strategy.md` | L161–210, L253–269 | 📄 (routing logic not implemented; a *different* hybrid — BM25+dense — is added in Task 6) |
| Embedding model (for PDF chunks) | `TASK_3_Data_Strategy.md` | Part 1 / Step 2 | ✅ `backend_main.py` `EMBEDDING_MODEL` L55 |
| Metadata strategy / schema | `TASK_3_Data_Strategy.md` | "## Part 6" L273–302 | ⚠️ code sets only `source`, `document_type` (`backend_main.py` L160–162) + `start_index` (L173); rich section/topic/keyword schema not implemented |
| Good/bad chunk examples (validation) | `TASK_3_Data_Strategy.md` | "## Part 4" L214–249 | 📄 + notebook cell 11 chunk preview |
| Chunking implementation plan | `TASK_3_Data_Strategy.md` | "## Part 7" L306–359 | ✅ notebook cells 6–16 + `backend_main.py` `_initialize()` L143–253 |
| *(Beyond spec)* Excel tax-slab source | — | `tax_slab_2025.xlsx`; `backend_main.py` `EXCEL_SOURCES` L69, `_load_excel_documents()` L255–316 | ✅ added in Task 6; not an original Task 3 deliverable |

## Task 4 — End-to-End Prototype

| Deliverable | File | Line/Symbol | Status |
|---|---|---|---|
| RAG development notebook | `02_Financial_Advisor_RAG.ipynb` | whole notebook | ✅ pipeline prototyped before backend |
| FastAPI backend app | `backend_main.py` | L414–427 `app = FastAPI(...)` | ✅ |
| RAG pipeline class | `backend_main.py` | L131–407 `class FinancialAdvisorRAG` | ✅ |
| RAG initialization (embed + chunk + vector store) | `backend_main.py` | L143–253 `_initialize()`; Qdrant L191–197 (`location=":memory:"`, `force_recreate=True`) | ✅ rebuilds on every startup |
| RAG chain (prompt → LLM → parser) | `backend_main.py` | L247–252; LLM `ChatAnthropic` L213 | ✅ |
| Retrieval + answer generation | `backend_main.py` | L354–407 `retrieve_and_answer()` | ✅ formats `[Source N]`, injects user context L393–394 |
| Health check endpoint | `backend_main.py` | L441–448 `GET /health` | ✅ returns `rag_ready` |
| Chat REST endpoint | `backend_main.py` | L451–514 `POST /chat` | ✅ core request flow |
| WebSocket real-time chat | `backend_main.py` | L552–605 `/ws/chat/{session_id}` | ⚠️ sends full response per message, not token streaming |
| Session management | `backend_main.py` | dicts L432–434; create/update L462–472; routes L517–545 | ⚠️ process-local, not persisted |
| User context model & handling | `backend_main.py` | `UserContext` L75–92; format L474–485; route L526–535 | ✅ profile sent per request |
| System prompt / guardrails | `backend_main.py` | `system_prompt` L217–238 | ✅ cite `[Source N]`, no specific securities, ground figures, framework-not-yes/no, CPA-for-tax |
| CORS config | `backend_main.py` | `CORSMiddleware` L420–427 | ⚠️ `allow_origins=["*"]` (tighten for prod) |
| Server entry / PORT binding | `backend_main.py` | L612–629; `PORT` env L623 | ✅ Render-compatible |
| Frontend chat interface | `frontend/app/page.tsx` | `FinancialAdvisorApp` L125–435; messages L349–390; input L408–425 | ✅ |
| User profile / context form | `frontend/app/page.tsx` | form L208–320; `handleContextSubmit` L146–150 | ✅ sent with every `/chat` POST (L171–176) |
| Source citations display | `frontend/app/page.tsx` | L368–383 | ✅ label, file, page, relevance % |
| Markdown rendering | `frontend/app/page.tsx` | `FormattedResponse` L20–90 (ReactMarkdown + remark-gfm) | ✅ styled headings/lists/tables/code |
| API base URL config | `frontend/app/page.tsx` | L123 `NEXT_PUBLIC_API_URL` | ✅ |
| Frontend dependencies | `frontend/package.json` (deployed) | whole file | ✅ Next 16, React 19, react-markdown, remark-gfm (`frontend_package.json` template is stale) |
| Backend deploy config | `render.yaml` | L5–23 | ✅ blueprint, `startCommand`, `/health`, `PYTHON_VERSION 3.11.9` |
| Frontend deploy config | `frontend/vercel.json`, `frontend/.env.local` | whole files | ✅ `framework: nextjs`, `NEXT_PUBLIC_API_URL` |
| Deployment notes / live URLs | `CLAUDE.md` Deployment; `IMPLEMENTATION_SUMMARY.md` L230–259 | — | 📄 live: [frontend](https://project-ai-makerspace.vercel.app), [backend](https://financial-advisor-backend-sifv.onrender.com) |

## Task 5 — Evaluation Harness & Baseline

| Deliverable | Location | Line/Section | Status |
|---|---|---|---|
| Evaluation harness (runner) | `eval/run_eval.py` | `main()` L104–162; `_write_reports()` L165–226; entry L229–230 | ✅ sends each case to `/chat`, records scores/latency, runs judge |
| Golden / synthetic test set | `eval/dataset.json` | full file (15 cases) | ✅ 15 cases; categories general/tax/combo/out_of_scope |
| LLM-as-judge (metrics) | `eval/run_eval.py` | `JUDGE_SCHEMA` L37–49; `JUDGE_SYSTEM` L51–59; `judge()` L62–96 | ✅ judge `claude-opus-4-8` (L34); scores groundedness/relevance/framework/citations + scope |
| RAGAS metrics | — | — | ❌ not used; custom LLM-judge rubric instead |
| Retrieval source-hit-rate metric | `eval/run_eval.py` | `source_hit` L143–144; agg L180–183 | ✅ |
| Aggregate metric computation | `eval/run_eval.py` | `agg` L172–186; `mean()` L99–101 | ✅ |
| Baseline report (human-readable) | `eval/results/baseline_report.md` | full file | ✅ dense/k=4: groundedness 3.6, citations 3.53, source-hit 1.0, latency 13.09s |
| Baseline raw results | `eval/results/baseline_results.json` | full file | ✅ per-question answers + rationales |
| Baseline summary + findings | `TASK_5_EVALUATION.md` | L31–58 | 📄 |
| Recommendations → Task 6 | `TASK_5_EVALUATION.md` | L60–70 | 📄 motivates hybrid + faithfulness + reranking |

## Task 6 — Advanced Retrieval Improvement

| Deliverable | Location | Line/Section | Status |
|---|---|---|---|
| Hybrid retrieval (BM25 + dense, RRF fusion) | `backend_main.py` | `_hybrid_retrieve()` L318–352; wired L356–360 | ✅ RRF fusion L342–350 |
| BM25 keyword retriever build | `backend_main.py` | `_initialize()` L200–208 | ✅ falls back to dense-only on failure |
| Hybrid config constants | `backend_main.py` | `HYBRID_RETRIEVAL=True` L65; `RRF_CONSTANT=60` L66; `RETRIEVAL_K=6` L59 | ✅ k raised 4→6 |
| Structured (spreadsheet) source loading | `backend_main.py` | `EXCEL_SOURCES` L69; `_load_excel_documents()` L255–316; merge L178–188 | ✅ tax_slab_2025.xlsx whole + per-row docs |
| Faithfulness guardrail | `backend_main.py` | `system_prompt` L229 (don't invent figures), L231 (cite only supported claims) | ⚠️ prompt-level only; no post-hoc verifier |
| Reranking / cross-encoder | — | — | ❌ future work only (`TASK_6` L64, `TASK_7` L54–55, `README` L135) |
| Multi-query retrieval | — | — | ❌ listed in `IMPLEMENTATION_SUMMARY.md` L281; not implemented |
| A/B baseline vs improved comparison | `TASK_6_ADVANCED_RETRIEVAL.md` | table L22–35; deltas L37–45; assessment L47–57 | 📄 |
| Improved (Task 6) report | `eval/results/eval_report.md` | full file | ✅ hybrid/k=6: groundedness 3.47, citations 3.80, latency 14.06s |
| Improved (Task 6) raw results | `eval/results/eval_results.json` | full file | ✅ |
| Decision & next steps | `TASK_6_ADVANCED_RETRIEVAL.md` | L59–71 | 📄 revert via `HYBRID_RETRIEVAL=False` |

## Task 7 — Reflection & Finalization

| Deliverable | Location | Line/Section | Status |
|---|---|---|---|
| Reflection writeup | `TASK_7_REFLECTION.md` | full file | 📄 |
| What worked / to improve (with evidence) | `TASK_7_REFLECTION.md` | L24–50 | 📄 cites eval numbers |
| Prioritized roadmap / next features | `TASK_7_REFLECTION.md` | L52–63 | 📄 |
| Demo script (~10 min) | `TASK_7_REFLECTION.md` | L65–80 (also `IMPLEMENTATION_SUMMARY.md` L299–313) | 📄 |
| Demo video | — | — | ❌ unchecked (`TASK_7` L87, `IMPLEMENTATION_SUMMARY.md` L378) |
| Final submission checklist | `TASK_7_REFLECTION.md` | L82–88 | 📄 |
| Final README | `README.md` | whole file; index L131–135 | ✅ ⚠️ *L39 stale: says k=4, code is `RETRIEVAL_K=6`* |
| Cross-task finalization index | `IMPLEMENTATION_SUMMARY.md` | Task 5 L265–272; Task 6 L274–286; Task 7 L289–313 | 📄 |
| Key learnings | `TASK_7_REFLECTION.md` | L89–98 | 📄 |

---

## Cross-Cutting Findings (Doc ↔ Code Drift)

These are places where the specification docs and the running code disagree — useful for reviewers and future maintenance:

1. **LLM model** — docs reference Claude 3.5 Sonnet / `claude-3-5-sonnet-20241022`; code uses `claude-sonnet-5` (`backend_main.py` L56). Code is newer.
2. **Tavily web search** — specified in Tasks 2 & 3; only the env key is read. No client or routing logic. (README L124 acknowledges this.)
3. **Reranking / RAGAS / multi-query** — appear only as recommendations in Task 5/6/7 docs; absent from `backend_main.py` and `eval/` (grep-confirmed).
4. **Redis memory** — imported optionally but not wired; sessions live in process-local dicts (`sessions`, `users`) and are wiped on restart.
5. **Faithfulness guardrail** is prompt-only (`backend_main.py` L229/L231); there is no post-hoc faithfulness verifier.
6. **Metadata schema** — Task 3's rich schema is aspirational; code sets only `source`, `document_type`, `start_index`.
7. **Frontend stack** — docs say Next 14 + Recharts + shadcn/ui; actual build is Next 16 + React 19 + plain Tailwind + react-markdown. Cite `frontend/package.json` (not the stale `frontend_package.json` template).
8. **WebSocket** — exists but returns one full JSON response per turn; no token-level streaming despite the "streaming" framing.
9. **`tax_slab_2025.xlsx`** structured source is implemented (Task 6) but was not an original Task 3 data deliverable.

*Note: the `README.md` "k=4" line was corrected to hybrid/k=6 as part of generating this document.*

*Generated at commit `ea26a02`. Line numbers reflect that revision and may shift as the code evolves.*
