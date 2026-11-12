"""Print the comparison table of all stored results, on the tickets that every backend answered.

    python report.py [--threshold 0.7]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from metrics import task_metrics
from run_bench import HERE, load_items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.7)
    parser.add_argument("--labels", default="", help="comma-separated result labels to compare (default: all)")
    args = parser.parse_args()
    items = {i["id"]: i for i in load_items()}
    wanted = [l for l in args.labels.split(",") if l]
    results = {p.stem: json.loads(p.read_text()) for p in sorted((HERE / "results").glob("*.json")) if not wanted or p.stem in wanted}
    if not results:
        raise SystemExit("no results yet: run run_bench.py first")
    common = set.intersection(*[{r["id"] for r in res["rows"] if not r["error"]} for res in results.values()])
    print(f"Tickets answered by every backend: {len(common)}  (confidence threshold {args.threshold})\n")
    for task in ("team", "urgent", "refund"):
        print(f"### {task}\n\n| backend | n | acc | ECE | Brier | conf | acc@c | cov@c |\n|---|---|---|---|---|---|---|---|")
        for label, res in results.items():
            m = task_metrics(task, [r for r in res["rows"] if r["id"] in common], items, args.threshold)
            print(f"| {label} | {m['n']} | {m['acc']:.2f} | {m['ece']:.3f} | {m['brier']:.3f} | {m['conf']:.2f} | {m['acc_conf']:.2f} | {m['cov_conf']:.2f} |")
        print()
    print("### speed (all three questions per ticket)\n\n| backend | errors | mean latency / ticket |\n|---|---|---|")
    for label, res in results.items():
        ok = [r for r in res["rows"] if not r["error"]]
        print(f"| {label} | {len(res['rows']) - len(ok)} | {1000 * sum(r['latency'] for r in ok) / max(1, len(ok)):.0f} ms |")


if __name__ == "__main__":
    main()
