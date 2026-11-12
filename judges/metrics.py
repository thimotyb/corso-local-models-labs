"""Measure a judge: accuracy, calibration (ECE), Brier score, and accuracy/coverage when confident."""
from __future__ import annotations

TEAMS = ["billing", "engineering", "sales"]


def vector(task: str, value) -> list[float]:
    """Probability vector of a stored row: team -> one entry per team; yes/no -> [P(no), P(yes)]."""
    if task == "team":
        return [float(value.get(t, 0.0)) for t in TEAMS]
    return [1.0 - float(value), float(value)]


def truth_index(task: str, item: dict) -> int:
    return TEAMS.index(item["team"]) if task == "team" else int(bool(item[task]))


def ece(confidences: list[float], correct: list[bool], bins: int = 10) -> float:
    """Expected calibration error: gap between stated confidence and actual accuracy, per confidence bin."""
    n, total = len(confidences), 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, c in enumerate(confidences) if (lo <= c < hi) or (b == bins - 1 and c == 1.0)]
        if idx:
            total += len(idx) / n * abs(sum(confidences[i] for i in idx) / len(idx) - sum(correct[i] for i in idx) / len(idx))
    return total


def task_metrics(task: str, rows: list[dict], items: dict[int, dict], threshold: float = 0.7) -> dict:
    conf, ok, brier = [], [], []
    for row in rows:
        if row.get("error"):
            continue
        p = vector(task, row[task])
        truth = truth_index(task, items[row["id"]])
        top = max(range(len(p)), key=p.__getitem__)
        conf.append(p[top])
        ok.append(top == truth)
        brier.append(sum((p[k] - (1.0 if k == truth else 0.0)) ** 2 for k in range(len(p))))
    n = len(conf)
    sure = [i for i, c in enumerate(conf) if c >= threshold]
    return {
        "n": n,
        "acc": sum(ok) / n,
        "ece": ece(conf, ok),
        "brier": sum(brier) / n,
        "conf": sum(conf) / n,
        "acc_conf": (sum(ok[i] for i in sure) / len(sure)) if sure else float("nan"),
        "cov_conf": len(sure) / n,
    }
