"""Judge backed by a general chat model, through any OpenAI-compatible endpoint.

Works with Ollama (default), vLLM or a LiteLLM gateway: choose the model with JUDGE_MODEL and the endpoint
with JUDGE_BASE_URL, exactly as for the other labs. The model is prompted to return JSON with
probabilities. These probabilities are the model's own statements: they MUST be measured (see metrics.py)
before any threshold is trusted. Small local chat models are typically over-confident.
"""
from __future__ import annotations

import json
import os
import time
from typing import Sequence

from judge import Answer, Question, Verdict

SYSTEM = (
    "You are a calibrated judge, not an assistant. Answer ONLY the typed questions about the STATE. "
    "Never write explanations. Return JSON: {\"answers\": {<question id>: <answer>}} where "
    "choice -> {\"option\": <one of the options>, \"probabilities\": {<option>: p, ...}} (p sum to 1); "
    "yesno -> {\"p_true\": p}. Probabilities must reflect real uncertainty: do not output 0 or 1 unless certain."
)


def render(questions: Sequence[Question]) -> str:
    lines = []
    for q in questions:
        if q.kind == "choice":
            lines.append(f"- {q.id} (choice): {q.prompt} Options: {q.options}")
        else:
            lines.append(f"- {q.id} (yesno): {q.prompt}")
    return "\n".join(lines)


def parse(q: Question, raw) -> Answer:
    clamp = lambda p: min(1.0, max(0.0, float(p)))
    if q.kind == "yesno":
        p = clamp(raw.get("p_true", 0.5) if isinstance(raw, dict) else raw)
        return Answer(q.id, p >= 0.5, {"true": p, "false": 1 - p})
    option = raw.get("option") if isinstance(raw, dict) else raw
    if option not in q.options:
        raise ValueError(f"'{option}' is not a valid option for {q.id}: {q.options}")
    probs = {o: clamp((raw.get("probabilities", {}) if isinstance(raw, dict) else {}).get(o, 0.0)) for o in q.options}
    total = sum(probs.values())
    return Answer(q.id, option, {o: p / total for o, p in probs.items()} if total > 0 else {option: 1.0})


class LLMJudge:
    def __init__(self, client=None, model: str | None = None):
        if client is None:
            from openai import OpenAI
            client = OpenAI(base_url=os.getenv("JUDGE_BASE_URL", "http://localhost:11434/v1"),
                            api_key=os.getenv("LLM_API_KEY", "not-needed-locally"))
        self.client, self.model = client, model or os.getenv("JUDGE_MODEL", "gemma4:12b")

    def _ask(self, state: str, questions: Sequence[Question]) -> dict:
        reply = self.client.chat.completions.create(
            model=self.model, temperature=0, response_format={"type": "json_object"},
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": f"STATE:\n{state}\n\nQUESTIONS:\n{render(questions)}"}])
        return json.loads(reply.choices[0].message.content or "{}").get("answers", {})

    def judge(self, state: str, questions: Sequence[Question]) -> Verdict:
        start = time.perf_counter()
        answers = self._ask(state, questions)
        for _ in range(2):  # small models sometimes skip a question: ask again for the missing ones only
            missing = [q for q in questions if q.id not in answers]
            if not missing:
                break
            answers = {**answers, **self._ask(state, missing)}
        missing = [q.id for q in questions if q.id not in answers]
        if missing:  # a backend failure must raise, never become a silent "no"
            raise ValueError(f"the judge returned no answer for {missing}")
        return Verdict({q.id: parse(q, answers[q.id]) for q in questions}, time.perf_counter() - start, 0.0, self.model)
