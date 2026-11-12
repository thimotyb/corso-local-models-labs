"""Tests that need no model download, network or API key."""
import json
from types import SimpleNamespace

import pytest

import cascade
import judge as J
import metrics
from llm_judge import LLMJudge
from opendecider_judge import OpenDeciderJudge
from run_bench import QUESTIONS, load_items


def test_ece_worked_example():
    # 5 answers at 0.9 (4 correct) and 5 at 0.6 (3 correct): 5/10*0.10 + 5/10*0.00 = 0.05
    conf = [0.9] * 5 + [0.6] * 5
    ok = [True] * 4 + [False] + [True] * 3 + [False] * 2
    assert metrics.ece(conf, ok) == pytest.approx(0.05)


def test_overconfident_judge_has_high_ece():
    assert metrics.ece([0.9] * 10, [True] * 6 + [False] * 4) == pytest.approx(0.30)


def test_dataset_is_the_expected_size():
    items = load_items()
    assert len(items) == 120 and {i["team"] for i in items} == set(metrics.TEAMS)


def test_decide_has_an_uncertain_band():
    yes = J.Answer("q", True, {"true": 0.9, "false": 0.1})
    unsure = J.Answer("q", True, {"true": 0.5, "false": 0.5})
    assert J.decide(yes) == "yes" and J.decide(unsure) == "unsure"


class FakeOpenDecider:
    def system_one(self, state, questions):
        assert questions["team"]["type"] == "choice" and questions["urgent"]["type"] == "noul"
        return {"answers": {"team": {"choice": "billing", "probabilities": {"billing": 0.8, "engineering": 0.15, "sales": 0.05}},
                            "urgent": {"noul": 0.9}, "refund": {"noul": 0.2}}}


def test_opendecider_adapter_maps_answers():
    v = OpenDeciderJudge(model_id="fake", model=FakeOpenDecider()).judge("text", QUESTIONS)
    assert v["team"].value == "billing" and v["team"].confidence == 0.8
    assert v["urgent"].value is True and v["refund"].value is False and v["refund"].confidence == pytest.approx(0.8)


class FakeChat:
    """Skips the 'refund' question on the first call, as small models sometimes do."""
    def __init__(self):
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kw):
        self.calls += 1
        answers = {"team": {"option": "sales", "probabilities": {"sales": 0.6, "billing": 0.3, "engineering": 0.1}}, "urgent": {"p_true": 0.1}}
        if self.calls > 1:
            answers = {"refund": {"p_true": 0.95}}
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"answers": answers})))])


def test_llm_judge_asks_again_for_missing_questions():
    client = FakeChat()
    v = LLMJudge(client=client, model="fake").judge("text", QUESTIONS)
    assert client.calls == 2 and v["refund"].value is True and v["team"].value == "sales"


def test_llm_judge_raises_instead_of_answering_no():
    client = FakeChat()
    client.create = lambda **kw: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))])
    client.chat.completions.create = client.create
    with pytest.raises(ValueError):
        LLMJudge(client=client, model="fake").judge("text", QUESTIONS)


class Fixed:
    def __init__(self, team_p, p, name):
        self.v = J.Verdict({"team": J.Answer("team", "billing", {"billing": team_p, "engineering": 1 - team_p, "sales": 0.0}),
                            "urgent": J.Answer("urgent", True, {"true": p, "false": 1 - p}),
                            "refund": J.Answer("refund", False, {"true": 1 - p, "false": p})}, 0.1, 0.0, name)

    def judge(self, state, questions):
        return J.Verdict({q.id: self.v[q.id] for q in questions}, 0.1, 0.0, self.v.backend)


def test_cascade_escalates_only_unsure_questions():
    cheap, strong = Fixed(0.95, 0.55, "cheap"), Fixed(0.99, 0.9, "strong")
    casc = cascade.CascadeJudge([cheap, strong], threshold=0.7)
    v = casc.judge("text", QUESTIONS)
    assert v["urgent"].confidence == 0.9          # unsure at the cheap tier, answered by the strong one
    assert v["team"].confidence == 0.95            # confident at the cheap tier: not escalated
    assert casc.needs_human == ()


def test_cascade_sends_remaining_doubt_to_a_person():
    casc = cascade.CascadeJudge([Fixed(0.95, 0.55, "a"), Fixed(0.95, 0.6, "b")], threshold=0.7)
    casc.judge("text", QUESTIONS)
    assert casc.needs_human == ("urgent", "refund")


def test_replay_trades_automation_for_accuracy():
    items = {i["id"]: i for i in load_items(20)}
    perfect = [{"id": i, "latency": 0, "cost": 0, "error": None, "team": {t: 1.0 if t == items[i]["team"] else 0.0 for t in metrics.TEAMS},
                "urgent": float(items[i]["urgent"]), "refund": float(items[i]["refund"])} for i in items]
    stats = cascade.replay([perfect], items, 0.7)
    assert stats["auto_acc"] == 1.0 and stats["human_share"] == 0.0


def test_xgboost_baseline_runs():
    pytest.importorskip("xgboost")
    from baseline_xgboost import run_xgboost
    items = load_items()
    rows = run_xgboost(items)
    stats = metrics.task_metrics("refund", rows, {i["id"]: i for i in items})
    assert stats["n"] == 120 and stats["acc"] > 0.8
