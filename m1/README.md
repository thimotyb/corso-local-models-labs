# M1 — Tokenization and encoding with DistilBERT

Open `01_bert_tokenization.ipynb` in Colab or Jupyter and run the cells in order. It shows WordPiece subwords, `input_ids`, special tokens, padding and `attention_mask` with the public `distilbert-base-uncased` tokenizer. The notebook installs `transformers` if needed. Its first run downloads tokenizer files from Hugging Face; it does not download model weights or need a GPU.

For a local environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r m1/requirements.txt jupyter
jupyter notebook m1/01_bert_tokenization.ipynb
```
