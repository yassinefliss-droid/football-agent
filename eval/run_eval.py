"""Evaluate the agent and the retriever, and write eval/results.md.

Two evaluations:
1. Retrieval (no LLM, fast): for each RAG question, is an expected article in the top-k
   passages? Compares dense vs sparse (BM25) vs hybrid search -> hit rate@k.
2. Agent (end to end, uses the LLM): answer accuracy per question type, tool routing
   accuracy (did it call the right tool?), and latency.

Usage:
  python eval/run_eval.py                 # both
  python eval/run_eval.py --retrieval     # retrieval only (no LLM needed)
  python eval/run_eval.py --limit 5       # quick smoke test on 5 questions
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings  # noqa: E402
from eval.checks import check_keywords, check_sql, gold_values  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent


def load_questions(limit: int | None = None) -> list[dict]:
    rows = [json.loads(line) for line in (EVAL_DIR / "questions.jsonl").read_text().splitlines() if line.strip()]
    return rows[:limit] if limit else rows


def eval_retrieval(questions: list[dict], k: int) -> list[str]:
    from app.agent import get_knowledge_base

    kb = get_knowledge_base()
    rag_qs = [q for q in questions if q["type"] == "rag"]
    lines = [f"## Retrieval: hit rate@{k} on {len(rag_qs)} questions", "", "| Mode | Hit rate | Avg latency |", "|---|---|---|"]
    for mode in ["dense", "sparse", "hybrid"]:
        hits, times = 0, []
        for q in rag_qs:
            start = time.perf_counter()
            titles = {r["title"] for r in kb.search(q["question"], k=k, mode=mode)}
            times.append(time.perf_counter() - start)
            hits += bool(titles & set(q["expected_titles"]))
        lines.append(f"| {mode} | {hits}/{len(rag_qs)} ({100 * hits / len(rag_qs):.0f}%) | {1000 * statistics.mean(times):.0f} ms |")
    return lines


def eval_agent(questions: list[dict]) -> tuple[list[str], list[dict]]:
    from app.agent import ask

    details = []
    for q in questions:
        try:
            result = ask(q["question"])
        except Exception as exc:
            result = {"answer": f"AGENT ERROR: {exc}", "tool_calls": [], "latency_s": 0.0}
        answer = result["answer"]

        correct = True
        if "gold_sql" in q:
            correct &= check_sql(answer, gold_values(q["gold_sql"], settings.db_path))
        if "keywords" in q:
            correct &= check_keywords(answer, q["keywords"])
        called = {c["tool"] for c in result["tool_calls"]}
        routed = set(q["expected_tools"]) <= called

        details.append({**q, "answer": answer, "correct": correct, "routed": routed,
                        "tools": sorted(called), "latency_s": result["latency_s"]})
        print(f"{'OK ' if correct else 'KO '} {q['id']}  {result['latency_s']:>5}s  {q['question'][:70]}")

    lines = ["## Agent: end-to-end accuracy", "",
             f"LLM: `{settings.llm_provider}` "
             f"(`{settings.groq_model if settings.llm_provider == 'groq' else settings.ollama_model}`)", "",
             "| Question type | Correct answers | Correct tool routing | Median latency |", "|---|---|---|---|"]
    for qtype in ["sql", "rag", "mixed", "all"]:
        subset = [d for d in details if qtype == "all" or d["type"] == qtype]
        if not subset:
            continue
        acc = sum(d["correct"] for d in subset)
        route = sum(d["routed"] for d in subset)
        lat = statistics.median(d["latency_s"] for d in subset)
        lines.append(f"| {qtype} | {acc}/{len(subset)} ({100 * acc / len(subset):.0f}%) "
                     f"| {route}/{len(subset)} ({100 * route / len(subset):.0f}%) | {lat:.1f} s |")

    failures = [d for d in details if not d["correct"]]
    if failures:
        lines += ["", "### Failed questions (to analyse)", ""]
        lines += [f"- **{d['id']}** {d['question']} — tools: {d['tools']} — answer: {d['answer'][:200]!r}" for d in failures]
    return lines, details


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retrieval", action="store_true", help="only evaluate retrieval (no LLM)")
    parser.add_argument("--limit", type=int, help="evaluate only the first N questions")
    parser.add_argument("--k", type=int, default=settings.top_k)
    args = parser.parse_args()

    questions = load_questions(args.limit)
    report = ["# Evaluation results", "", f"_Generated on {time.strftime('%Y-%m-%d %H:%M')}_", ""]
    report += eval_retrieval(questions, args.k) + [""]
    if not args.retrieval:
        agent_lines, details = eval_agent(questions)
        report += agent_lines
        (EVAL_DIR / "results.json").write_text(json.dumps(details, indent=2, ensure_ascii=False))

    (EVAL_DIR / "results.md").write_text("\n".join(report) + "\n")
    print("\n" + "\n".join(report))


if __name__ == "__main__":
    main()
