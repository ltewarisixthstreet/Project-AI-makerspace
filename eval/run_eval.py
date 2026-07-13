#!/usr/bin/env python
"""Task 5 - Evaluation harness for the Financial Advisor RAG.

Runs a fixed test set through the /chat API, then scores each answer with an
LLM judge (claude-opus-4-8) on groundedness, relevance, framework quality, and
citation use. Also measures retrieval source-hit and out-of-scope handling.

Usage:
    # backend must be running (default http://localhost:8000)
    python eval/run_eval.py                       # full run against local
    python eval/run_eval.py --limit 3             # quick smoke run
    python eval/run_eval.py --base-url https://financial-advisor-backend-sifv.onrender.com

Outputs eval/results/eval_results.json and eval/results/eval_report.md.
Requires ANTHROPIC_API_KEY (for the judge) in the environment / .env.
"""
import os
import re
import json
import time
import argparse
import statistics
from pathlib import Path

import requests
from dotenv import load_dotenv
import anthropic

load_dotenv()

HERE = Path(__file__).parent
DATASET = HERE / "dataset.json"
RESULTS_DIR = HERE / "results"
JUDGE_MODEL = "claude-opus-4-8"

# 1-5 scale (5 = best) on four dimensions + a scope-handling verdict.
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "groundedness": {"type": "integer", "description": "1-5: answer supported by the retrieved sources, no hallucinated facts or numbers"},
        "relevance": {"type": "integer", "description": "1-5: directly and usefully addresses the question"},
        "framework_quality": {"type": "integer", "description": "1-5: teaches a decision framework rather than a bare yes/no"},
        "citations": {"type": "integer", "description": "1-5: cites sources like [Source N] appropriately for its claims"},
        "scope_handling": {"type": "string", "enum": ["correct", "incorrect", "na"], "description": "out-of-scope questions: 'correct' if it appropriately declined/redirected, else 'incorrect'; 'na' if the question is in scope"},
        "rationale": {"type": "string", "description": "one or two sentences justifying the scores"},
    },
    "required": ["groundedness", "relevance", "framework_quality", "citations", "scope_handling", "rationale"],
    "additionalProperties": False,
}

JUDGE_SYSTEM = (
    "You are a strict evaluator of a financial-advisor RAG assistant. "
    "Score each dimension 1-5 (5 = best). Be critical: penalize hallucinated "
    "numbers, claims not supported by the retrieved sources, missing citations, "
    "and yes/no answers that fail to teach a decision framework. For out-of-scope "
    "questions (specific stock/crypto picks, unrelated topics), a good answer "
    "declines or redirects; score scope_handling accordingly and set the numeric "
    "scores based on how well it handled the refusal."
)


def judge(client, item, answer, sources):
    src_txt = "\n".join(
        f"- {s['file']} ({s['page']}): {(s.get('preview') or '')[:160]}" for s in sources
    ) or "(no sources retrieved)"
    user = (
        f"Question category: {item['category']}\n"
        f"Question: {item['question']}\n"
        f"Expected behavior: {item.get('expected', 'answer helpfully, grounded in sources')}\n\n"
        f"Retrieved sources:\n{src_txt}\n\n"
        f"Assistant answer:\n{answer}\n\n"
        "Score it against the schema."
    )
    # Prefer structured outputs; fall back to plain JSON parsing if unavailable.
    try:
        resp = client.messages.create(
            model=JUDGE_MODEL,
            max_tokens=1024,
            system=JUDGE_SYSTEM,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": JUDGE_SCHEMA}},
        )
        text = next(b.text for b in resp.content if b.type == "text")
        return json.loads(text)
    except Exception as e:
        resp = client.messages.create(
            model=JUDGE_MODEL,
            max_tokens=1024,
            system=JUDGE_SYSTEM + " Respond with ONLY a JSON object matching the required keys.",
            messages=[{"role": "user", "content": user}],
        )
        text = next(b.text for b in resp.content if b.type == "text")
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise RuntimeError(f"Judge returned no JSON: {text[:200]}") from e
        return json.loads(m.group(0))


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.mean(xs), 2) if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=os.getenv("EVAL_BASE_URL", "http://localhost:8000"))
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    items = json.loads(DATASET.read_text())
    if args.limit:
        items = items[: args.limit]

    # Fail fast if the backend isn't reachable.
    try:
        h = requests.get(f"{args.base_url}/health", timeout=120)
        h.raise_for_status()
        assert h.json().get("rag_ready"), "backend reports rag_ready=false"
    except Exception as e:
        raise SystemExit(f"Backend not reachable at {args.base_url}: {e}")

    client = anthropic.Anthropic()
    RESULTS_DIR.mkdir(exist_ok=True)

    results = []
    for i, item in enumerate(items, 1):
        print(f"[{i}/{len(items)}] {item['id']}: {item['question'][:60]}...")
        t0 = time.time()
        r = requests.post(
            f"{args.base_url}/chat",
            json={"user_id": "eval", "message": item["question"], "session_id": f"eval_{item['id']}"},
            timeout=120,
        )
        r.raise_for_status()
        d = r.json()
        latency = time.time() - t0

        answer = d["assistant_response"]
        sources = d.get("sources", [])
        scores = d.get("retrieval_scores", [])
        files = [s.get("file") for s in sources]

        exp = item.get("expected_source")
        source_hit = True if exp is None else any(exp in (f or "") for f in files)

        j = judge(client, item, answer, sources)

        results.append({
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "latency_s": round(latency, 2),
            "top_score": round(scores[0], 3) if scores else None,
            "avg_retrieval_score": round(sum(scores) / len(scores), 3) if scores else None,
            "expected_source": exp,
            "retrieved_files": files,
            "source_hit": source_hit,
            "judge": j,
            "answer": answer,
        })

    _write_reports(results, args.base_url)


def _write_reports(results, base_url):
    (RESULTS_DIR / "eval_results.json").write_text(json.dumps(results, indent=2))

    in_scope = [r for r in results if r["category"] != "out_of_scope"]
    oos = [r for r in results if r["category"] == "out_of_scope"]
    source_checked = [r for r in results if r["expected_source"] is not None]

    agg = {
        "n": len(results),
        "groundedness": mean([r["judge"]["groundedness"] for r in results]),
        "relevance": mean([r["judge"]["relevance"] for r in results]),
        "framework_quality": mean([r["judge"]["framework_quality"] for r in in_scope]),
        "citations": mean([r["judge"]["citations"] for r in results]),
        "avg_retrieval_top_score": mean([r["top_score"] for r in results]),
        "avg_latency_s": mean([r["latency_s"] for r in results]),
        "source_hit_rate": (
            round(sum(r["source_hit"] for r in source_checked) / len(source_checked), 2)
            if source_checked else None
        ),
        "oos_correct": sum(1 for r in oos if r["judge"]["scope_handling"] == "correct"),
        "oos_total": len(oos),
    }

    lines = []
    lines.append("# Financial Advisor RAG - Evaluation Baseline\n")
    lines.append(f"- Target: `{base_url}`")
    lines.append(f"- Cases: **{agg['n']}**  |  Judge: `{JUDGE_MODEL}`")
    lines.append("")
    lines.append("## Aggregate metrics\n")
    lines.append("| Metric | Score |")
    lines.append("|---|---|")
    lines.append(f"| Groundedness (1-5) | {agg['groundedness']} |")
    lines.append(f"| Relevance (1-5) | {agg['relevance']} |")
    lines.append(f"| Framework quality (1-5, in-scope) | {agg['framework_quality']} |")
    lines.append(f"| Citations (1-5) | {agg['citations']} |")
    lines.append(f"| Retrieval source-hit rate | {agg['source_hit_rate']} |")
    lines.append(f"| Avg top retrieval score | {agg['avg_retrieval_top_score']} |")
    lines.append(f"| Out-of-scope handled correctly | {agg['oos_correct']}/{agg['oos_total']} |")
    lines.append(f"| Avg latency (s) | {agg['avg_latency_s']} |")
    lines.append("")
    lines.append("## Per-question results\n")
    lines.append("| ID | Cat | Ground | Rel | Frwk | Cite | Scope | Src hit | Top | Lat(s) |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        j = r["judge"]
        lines.append(
            f"| {r['id']} | {r['category']} | {j['groundedness']} | {j['relevance']} | "
            f"{j['framework_quality']} | {j['citations']} | {j['scope_handling']} | "
            f"{'Y' if r['source_hit'] else 'N'} | {r['top_score']} | {r['latency_s']} |"
        )
    lines.append("")
    lines.append("## Judge rationales\n")
    for r in results:
        lines.append(f"- **{r['id']}**: {r['judge']['rationale']}")
    lines.append("")

    (RESULTS_DIR / "eval_report.md").write_text("\n".join(lines))

    print("\n=== SUMMARY ===")
    for k, v in agg.items():
        print(f"  {k}: {v}")
    print(f"\nWrote {RESULTS_DIR / 'eval_report.md'} and eval_results.json")


if __name__ == "__main__":
    main()
