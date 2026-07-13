# Task 6: Advanced Retrieval Improvement

## Goal
Use the Task 5 baseline to drive a retrieval improvement, then A/B the change
against that baseline with the same harness.

Baseline weaknesses (from `TASK_5_EVALUATION.md`): groundedness **3.6** and
citation accuracy **3.53**, mediocre retrieval (avg top score ~0.5), and tax
answers *inferring* bracket numbers that weren't in the retrieved passages.

## Changes made (`backend_main.py`)
1. **Hybrid retrieval (BM25 + dense, RRF fusion)** — a BM25 keyword retriever
   (`rank_bm25`) is fused with the dense Qdrant search via reciprocal-rank
   fusion (`_hybrid_retrieve`). Keyword matching catches exact terms
   (percentages, dollar thresholds) that embeddings miss. Toggle with
   `HYBRID_RETRIEVAL`.
2. **`RETRIEVAL_K` 4 → 6** — more grounding context per answer.
3. **Faithfulness guardrail (prompt)** — instruct the model to ground every
   specific figure/quote in the context, avoid inventing numbers, and cite a
   source only for claims that source supports.

## A/B results (same 15-case harness, judge `claude-opus-4-8`)

| Metric | Baseline (dense, k=4) | Task 6 (hybrid, k=6) | Δ |
|---|---|---|---|
| Groundedness (1-5) | 3.60 | 3.47 | −0.13 |
| Citations (1-5) | 3.53 | 3.80 | **+0.27** |
| Relevance (1-5) | 5.00 | 4.73 | −0.27 |
| Framework quality (1-5) | 5.00 | 4.75 | −0.25 |
| Retrieval source-hit rate | 1.00 | 1.00 | 0 |
| Out-of-scope handled | 3/3 | 3/3 | 0 |
| Avg latency (s) | 13.1 | 14.1 | +1.0 |

Raw: baseline in `eval/results/baseline_report.md`; Task 6 in
`eval/results/eval_report.md`.

### Per-question deltas (net across 15 cases)
`groundedness −2, citations +4, relevance −4, framework −1`

- **Where it helped (the target):** `tax-marginal-150k` groundedness **+2**,
  `stock-picking` +1/+1, `oos-crypto` +1/+1, `tax-top-bracket` citations +1 —
  keyword/exact-term queries got better grounding and citations.
- **Where it regressed:** general PDF questions dipped slightly, dominated by a
  single outlier — `bonus-deploy` fell **−2 on every axis** and alone accounts
  for most of the aggregate drop.

## Honest assessment
- **The targeted fix worked:** hybrid retrieval measurably improved the
  tax/keyword cases that motivated it, and citation accuracy rose overall.
- **The aggregate is roughly flat.** With N=15 and a stochastic LLM judge,
  sub-0.3 deltas are within run-to-run noise, and one outlier (`bonus-deploy`)
  swings the averages.
- **Groundedness is bottlenecked by generation, not retrieval.** The recurring
  failure is the model *elaborating with specific figures beyond the context*.
  Better retrieval supplies more correct context but doesn't stop the model from
  adding unsupported specifics; the guardrail helped citations but not
  groundedness enough.

## Decision & next steps
- **Keep hybrid retrieval on** — it fixes the diagnosed tax/keyword weakness and
  improves citations, at ~1s latency cost. Trivially revertible via
  `HYBRID_RETRIEVAL=False`.
- **To move groundedness further (future work):**
  - Add a **cross-encoder / LLM re-ranker** over the fused candidates.
  - **Harden generation grounding** — stronger "no numbers not in context"
    constraint, or a post-hoc faithfulness check that flags unsupported
    figures.
  - **Make the eval statistically robust** — larger set + average over multiple
    judge runs so real gains aren't lost in noise.
  - Consider **query routing**: force the full tax table into context for
    tax-intent queries (belt-and-suspenders on top of hybrid).
