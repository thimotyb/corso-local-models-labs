# Lab: compact local judges and decision models

Measure and compare small local models that **judge, classify or route** instead of writing text. The case is support-ticket triage with three typed questions per ticket:

| Question | Type | Answers |
| --- | --- | --- |
| Which team should handle this ticket? | choice | billing, engineering, sales |
| Does the customer need a resolution within 24 hours? | yes/no | yes, no |
| Does the customer explicitly ask for a refund or a credit back? | yes/no | yes, no |

`data/tickets.jsonl` has 120 synthetic tickets (no personal data): 100 built from templates and 20 hand-written to be hard (negations such as "I do not want a refund", refunds that are implied, urgency without keywords). Each ticket stores its correct answers.

## Backends compared

| Backend | What it is | Runs on |
| --- | --- | --- |
| `opendecider` | [OpenDecider](https://github.com/manjunathshiva/opendecider): small open-weight **decision model** that reads option probabilities in one forward pass (nano ~0.4B, small 4B). Apache-2.0. | CPU for nano; GPU advised for small |
| `llm` | A general **chat model** prompted to answer in JSON with probabilities, through any OpenAI-compatible endpoint (Ollama, vLLM, LiteLLM). | Ollama / GPU |
| `xgboost` | A classical **classifier**: TF-IDF words + gradient-boosted trees, trained on the labels (5-fold, out-of-fold predictions). | CPU |

All of them implement one small interface (`judge.py`): `judge(state, questions) -> Verdict` with typed answers and probabilities. Thresholds and routing are ordinary code (`decide`, `cascade.py`).

## Setup

From the repository root, with the virtual environment active:

```bash
pip install -r judges/requirements.txt
cd judges
python -m pytest -q          # 11 tests, no model download or key needed
```

## Run

```bash
python run_bench.py --backend xgboost     --label xgboost-tfidf
python run_bench.py --backend opendecider --label opendecider-nano          # downloads ~0.8 GB on first use
OPENDECIDER_MODEL=manjunathshiva/opendecider-small \
  python run_bench.py --backend opendecider --label opendecider-small       # needs: pip install "opendecider[small]", GPU advised

# general chat model through Ollama (or a LiteLLM gateway: set JUDGE_BASE_URL and use a logical model name)
JUDGE_MODEL=gemma4:12b python run_bench.py --backend llm --label gemma-12b

python report.py                                  # comparison table on the tickets every backend answered
```

Results are stored in `results/<label>.json`, one row per ticket, so any analysis can be re-run without calling a model again. `results/` already contains reference runs (see below).

## Metrics

- **Accuracy**: share of correct top answers.
- **ECE** (expected calibration error, 10 bins): average gap between stated confidence and actual accuracy; 0 is perfect. A judge that says 0.9 should be right nine times in ten.
- **Brier score**: mean squared error of the probability vector; combines accuracy and calibration.
- **acc@c / cov@c**: accuracy and share of answers when confidence is at least `c` (0.7 by default). Coverage is how much work the judge can do alone; accuracy when confident says whether its confident answers can be trusted.

Accuracy alone hides the failure that matters in a routed system: a judge that is wrong *and certain* never triggers escalation.

## Exercises

1. Run the three backends and read `report.py`. Which one is best on accuracy? On calibration? On speed?
2. Open `data/tickets.jsonl` lines 101 to 120 (the hand-written tickets) and find which ones each backend gets wrong.
3. Tune a cascade offline: `cascade.replay([...], items, threshold)` on stored results shows, for each threshold, how accurate the automatic answers are and how many go to a person.
4. Rewrite a question in `run_bench.py` (for example make "urgent" compound) and measure the change.
5. Replace the tickets with 100 examples of your own domain and repeat. Keep the answers you stored, they are your evaluation set.

## Notes

- Calibration is a property of a model *on a task*: re-measure when the model, the quantization or the wording of a question changes.
- A failure of the backend raises an error and is recorded as an error row; it is never converted into a "no".
- Model weights are downloaded from Hugging Face on first use. Apache-2.0 for the OpenDecider package; check the model card of each model you use.
