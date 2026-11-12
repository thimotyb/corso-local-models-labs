"""Judge backed by OpenDecider, a small open-weight decision model that runs locally (Apache-2.0).

OpenDecider is not a chat model. It reads the probability of each option directly (one forward pass,
no generated text), so it answers in milliseconds and its probabilities are meant to be read as such.
https://github.com/manjunathshiva/opendecider

    pip install opendecider                 # nano, ~0.4B parameters, runs on CPU
    pip install "opendecider[small]"        # also the 4B model (GPU advised)
    OPENDECIDER_MODEL=manjunathshiva/opendecider-nano      (default)
    OPENDECIDER_MODEL=manjunathshiva/opendecider-small
"""
from __future__ import annotations

import os
import time
from typing import Any, Sequence

from judge import Answer, Choice, Question, Verdict

DEFAULT_MODEL = "manjunathshiva/opendecider-nano"


def to_opendecider(q: Question) -> dict:
    if q.kind == "yesno":
        return {"type": "noul", "instructions": q.prompt}
    criteria = q.descriptions or {option: option for option in q.options}
    return {"type": "choice", "instructions": q.prompt, "criteria": criteria}


def from_opendecider(q: Question, raw: dict) -> Answer:
    if q.kind == "yesno":
        p = min(1.0, max(0.0, float(raw["noul"])))
        return Answer(q.id, p >= 0.5, {"true": p, "false": 1 - p})
    probs = {o: float(raw.get("probabilities", {}).get(o, 0.0)) for o in q.options}
    return Answer(q.id, raw["choice"], probs)


class OpenDeciderJudge:
    """Pass `model` (any object with `system_one(state, questions)`) to inject a fake in tests."""

    def __init__(self, model_id: str | None = None, model: Any = None):
        self.model_id = model_id or os.getenv("OPENDECIDER_MODEL", DEFAULT_MODEL)
        if model is None:
            try:
                from opendecider import load
            except ImportError as exc:
                raise RuntimeError('OpenDecider is not installed: pip install opendecider') from exc
            model = load(self.model_id)  # downloaded from Hugging Face on first use
        self.model = model

    def judge(self, state: str, questions: Sequence[Question]) -> Verdict:
        start = time.perf_counter()
        result = self.model.system_one(state, {q.id: to_opendecider(q) for q in questions})
        answers = {q.id: from_opendecider(q, result["answers"][q.id]) for q in questions}
        return Verdict(answers, time.perf_counter() - start, 0.0, self.model_id)
