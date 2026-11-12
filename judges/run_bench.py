"""Run one backend over the labelled tickets and store per-ticket probabilities.

    python run_bench.py --backend opendecider --label opendecider-nano
    OPENDECIDER_MODEL=manjunathshiva/opendecider-small python run_bench.py --backend opendecider --label opendecider-small
    JUDGE_MODEL=gemma4:12b python run_bench.py --backend llm --label gemma-12b
    python run_bench.py --backend xgboost --label xgboost-tfidf

Results go to results/<label>.json; build the comparison table with report.py.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from judge import Choice, YesNo
from metrics import TEAMS

HERE = Path(__file__).resolve().parent
QUESTIONS = [
    Choice("team", "Which team should handle this ticket?", TEAMS, {
        "billing": "Charges, refunds, invoices, subscriptions",
        "engineering": "Errors, crashes, outages, access problems, bugs",
        "sales": "Quotes, plans, upgrades, discounts, contracts"}),
    YesNo("urgent", "Does the customer need a resolution within 24 hours?"),
    YesNo("refund", "Does the customer explicitly ask for a refund or a credit back?"),
]


def load_items(limit: int = 0) -> list[dict]:
    items = [json.loads(line) for line in (HERE / "data" / "tickets.jsonl").read_text().splitlines() if line.strip()]
    return items[:limit] if limit else items


def run_judge(judge, items: list[dict]) -> list[dict]:
    rows = []
    for n, item in enumerate(items, 1):
        try:
            v = judge.judge(item["text"], QUESTIONS)
            rows.append({"id": item["id"], "latency": v.latency_s, "cost": v.cost_usd, "error": None,
                         "team": v["team"].probabilities, "urgent": v["urgent"].probabilities["true"],
                         "refund": v["refund"].probabilities["true"]})
        except Exception as exc:  # recorded as an error row and excluded from the metrics, never as a wrong answer
            rows.append({"id": item["id"], "latency": 0.0, "cost": 0.0, "error": str(exc)[:200]})
        if n % 20 == 0:
            print(f"  {n}/{len(items)}", flush=True)
    return rows


def main() -> None:
    load_dotenv(find_dotenv(usecwd=True))
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["opendecider", "llm", "xgboost"], required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--limit", type=int, default=0, help="only the first N tickets")
    args = parser.parse_args()
    items = load_items(args.limit)
    start = time.perf_counter()
    if args.backend == "xgboost":
        from baseline_xgboost import run_xgboost
        rows = run_xgboost(items)
    else:
        if args.backend == "opendecider":
            from opendecider_judge import OpenDeciderJudge
            judge = OpenDeciderJudge()
        else:
            from llm_judge import LLMJudge
            judge = LLMJudge()
        rows = run_judge(judge, items)
    out = {"label": args.label, "backend": args.backend, "n": len(items), "wall_s": time.perf_counter() - start, "rows": rows}
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / f"{args.label}.json").write_text(json.dumps(out, indent=1))
    errors = sum(1 for r in rows if r["error"])
    print(f"{args.label}: {len(rows)} tickets, {errors} errors, {out['wall_s']:.1f} s")


if __name__ == "__main__":
    main()
