"""Typed judge interface ("System One" style).

A judge receives a *state* (the text to judge) and typed *questions*, and returns typed *answers with
probabilities*. It never writes free text. Thresholds and routing stay in ordinary code (decide, cascade.py).
Any backend that implements `judge(state, questions) -> Verdict` can be swapped in by configuration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence


@dataclass(frozen=True)
class Choice:
    """Pick exactly one option. `descriptions` says what each option means, in observable terms."""
    id: str
    prompt: str
    options: list[str]
    descriptions: dict[str, str] | None = None
    kind: str = "choice"


@dataclass(frozen=True)
class YesNo:
    """Yes/no question; the answer carries P(yes). Phrase it so that yes means the condition holds."""
    id: str
    prompt: str
    kind: str = "yesno"


Question = Choice | YesNo


@dataclass(frozen=True)
class Answer:
    question_id: str
    value: str | bool
    probabilities: dict[str, float] = field(default_factory=dict)  # option -> p ; yes/no: {"true": p, "false": 1-p}

    @property
    def confidence(self) -> float:
        """Probability of the returned value."""
        key = ("true" if self.value else "false") if isinstance(self.value, bool) else str(self.value)
        return self.probabilities.get(key, 1.0)


@dataclass(frozen=True)
class Verdict:
    answers: dict[str, Answer]
    latency_s: float = 0.0
    cost_usd: float = 0.0
    backend: str = ""

    def __getitem__(self, question_id: str) -> Answer:
        return self.answers[question_id]


class Judge(Protocol):
    def judge(self, state: str, questions: Sequence[Question]) -> Verdict: ...


def decide(answer: Answer, accept: float = 0.7, reject: float = 0.3) -> str:
    """Map a yes/no answer to 'yes', 'no' or 'unsure' (the uncertain band goes to a larger model or a person)."""
    p = answer.probabilities.get("true", 0.5)
    return "yes" if p >= accept else "no" if p <= reject else "unsure"
