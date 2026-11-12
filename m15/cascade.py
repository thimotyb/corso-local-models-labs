"""Cascade: a cheap local judge answers what it is sure about; the rest goes to the next tier, then to a person.

`CascadeJudge` runs live. `replay` computes the same routing from stored results (no model calls), so the
threshold can be tuned on a measured set: accuracy of the automatic answers against the share sent to people.
"""
from __future__ import annotations

from typing import Sequence

from judge import Answer, Judge, Question, Verdict
from metrics import task_metrics, truth_index, vector


class CascadeJudge:
    def __init__(self, tiers: Sequence[Judge], threshold: float = 0.7):
        self.tiers, self.threshold = list(tiers), threshold
        self.needs_human: tuple[str, ...] = ()

    def judge(self, state: str, questions: Sequence[Question]) -> Verdict:
        answers: dict[str, Answer] = {}
        pending, latency, backends = list(questions), 0.0, []
        for tier in self.tiers:
            if not pending:
                break
            v = tier.judge(state, pending)
            latency += v.latency_s
            backends.append(v.backend)
            for q in pending:
                answers[q.id] = v[q.id]
            pending = [q for q in pending if v[q.id].confidence < self.threshold]
        self.needs_human = tuple(q.id for q in pending)  # still unsure after the last tier: a person decides
        return Verdict(answers, latency, 0.0, "+".join(backends))


def replay(tier_rows: list[list[dict]], items: dict[int, dict], threshold: float) -> dict:
    """tier_rows: stored rows of each tier, cheapest first. Returns per-question routing statistics."""
    by_id = [{r["id"]: r for r in rows if not r["error"]} for rows in tier_rows]
    ids = sorted(set.intersection(*[set(d) for d in by_id]))
    auto = correct = human = escalated = 0
    for i in ids:
        for task in ("team", "urgent", "refund"):
            for n, tier in enumerate(by_id):
                p = vector(task, tier[i][task])
                top = max(range(len(p)), key=p.__getitem__)
                if p[top] >= threshold:
                    auto += 1
                    correct += top == truth_index(task, items[i])
                    escalated += n > 0
                    break
            else:
                human += 1
    total = auto + human
    return {"questions": total, "auto_acc": correct / auto if auto else float("nan"),
            "human_share": human / total, "escalated_share": escalated / total}
