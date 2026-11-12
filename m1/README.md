# M1 — BERT tokenization and text classification

Two runnable notebooks serve different lesson lengths:

| Notebook | Purpose | Requirements |
| --- | --- | --- |
| [`01_bert_tokenization.ipynb`](01_bert_tokenization.ipynb) | A short, focused exercise on WordPiece, special tokens, IDs, padding and attention masks. | `m1/requirements.txt`; downloads tokenizer files only. |
| [`02_bert_text_classification.ipynb`](02_bert_text_classification.ipynb) | The complete path: emotion dataset, exploratory plots, character/word/subword tokenization, frozen encoder, linear probe, fine-tuning, evaluation, error analysis and local save/reload. Six figures are embedded. | `m1/requirements-extended.txt`; downloads dataset and model weights. GPU recommended, CPU supported with a small sample. |

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r m1/requirements-extended.txt
jupyter notebook m1/
```

For the short exercise only, install `m1/requirements.txt` and Jupyter instead. Run each notebook from top to bottom. The extended notebook deliberately trains for just three steps on a small balanced sample; its metrics demonstrate the workflow and are not model-quality claims. It writes model artifacts to a temporary directory and never uploads them. See [NOTICE.md](NOTICE.md) for figure and dataset attribution.
