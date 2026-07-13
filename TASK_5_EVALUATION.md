# Task 5: Evaluation Harness & Baseline

## Goal
Measure the quality of the Financial Advisor RAG with a repeatable harness, an
LLM-as-judge, and a baseline report — so Task 6 (advanced retrieval) can be
justified with evidence.

## What was built
- **`eval/dataset.json`** — 15 curated cases across three categories:
  - `general` (7) — grounded in `Were-Talking-Millions.pdf` (allocation, debt vs. invest, emergency fund, diversification, behavior, bonus, stock-picking)
  - `tax` (4) — grounded in `tax_slab_2025.xlsx` (marginal bracket, marginal vs. effective, progressive calc, top bracket)
  - `combo` (1) + `out_of_scope` (3) — Roth vs. taxable, and stock/crypto/unrelated refusals
  Each case carries an `expected_source` and an `expected` behavior.
- **`eval/run_eval.py`** — sends each question to `/chat`, records retrieval
  sources/scores and latency, then scores the answer with an LLM judge
  (`claude-opus-4-8`, structured output) on **groundedness, relevance,
  framework quality, citations**, plus a **scope-handling** verdict. Also
  computes **retrieval source-hit rate** (did the expected source appear).
- **`eval/results/`** — `eval_report.md` (human-readable) and
  `eval_results.json` (raw, per-question including answers + rationales).

### Run it
```bash
# backend must be running (local or prod)
python eval/run_eval.py                 # full run against http://localhost:8000
python eval/run_eval.py --limit 3       # quick smoke
python eval/run_eval.py --base-url https://financial-advisor-backend-sifv.onrender.com
```
Requires `ANTHROPIC_API_KEY` (for the judge).

## Baseline results (15 cases)

| Metric | Score |
|---|---|
| Relevance (1-5) | 5.0 |
| Framework quality (1-5) | 5.0 |
| Groundedness (1-5) | **3.6** |
| Citations (1-5) | **3.53** |
| Retrieval source-hit rate | 1.0 |
| Avg top retrieval score | ~0.5 |
| Out-of-scope handled correctly | 3/3 |
| Avg latency | ~13 s |

(See `eval/results/eval_report.md` for the per-question table and judge rationales.)

## Key findings
1. **Strong reasoning, weak grounding.** Relevance and framework quality are
   maxed out and out-of-scope refusals are perfect, but **groundedness (3.6)**
   and **citation accuracy (3.53)** lag: the model invents specific figures and
   quotes and cites `[Source N]` for claims the retrieved snippets don't
   contain (flagged on ~7/15 cases).
2. **Retrieval is mediocre.** Average top similarity ~0.5; on several tax
   questions the exact bracket rows weren't in the top-k, so the model inferred
   numbers instead of quoting them. Source-hit is 1.0 (the right *file* shows
   up) but the right *passage* often doesn't.
3. **The knowledge base is thin for some topics** (e.g., emergency funds), and
   the model correctly flags gaps — good behavior, but expands scope with
   external knowledge.

## Recommendations → Task 6 (advanced retrieval)
- **Improve retrieval precision:** hybrid (keyword + semantic) search and/or a
  cross-encoder re-ranker; consider raising `RETRIEVAL_K` and better PDF
  chunking so cited passages actually contain the claims.
- **Guarantee tax grounding:** for tax queries, always include the full
  `tax_slab_2025.xlsx` table (it's tiny) so bracket numbers are never inferred.
- **Faithfulness guardrail in the prompt:** instruct the model to not state
  specific figures unless present in the context, and to cite a source only for
  claims that source supports.
- **Re-run this harness after each change** and compare against this baseline
  (target: groundedness and citations > 4.5 with no regression elsewhere).
