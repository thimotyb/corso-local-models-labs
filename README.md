# Local LLM labs: companion repository

Hands-on notebooks and data for the course on local language models. This repository is self-contained: clone it, set up the environment below and run the labs. Nothing else is required.

## Contents

| Folder | What it contains |
| --- | --- |
| `m1/` | Three M1 notebooks: focused BERT tokenization, extended text classification, and Hugging Face Hub model search with memory estimates. |
| `m5/` | A weather tool built step by step (mock, FastAPI over OpenWeather, MCP) and a tool-calling loop for a local model. |
| `m8/` | Five notebooks on Retrieval-Augmented Generation with Chroma, LangChain and local models, plus all the data they use; a LiteLLM gateway example. Fully offline once the models are downloaded. |
| `m15/` | Compact local judges and decision models (OpenDecider, a chat model as judge, a classical classifier): typed questions, calibration metrics, cascades. Runs on CPU. |
| `scripts/` | Data preparation scripts (only needed to refresh the saved web pages). |

More labs (quantization, fine-tuning, serving) will be added in their own folders.

## Prerequisites

- Python 3.11 or newer
- [Ollama](https://ollama.com) running locally (default `http://localhost:11434`)
- A GPU is recommended; the default models also run on CPU, more slowly

## Setup

```bash
git clone <this repository>
cd corso-local-models-labs

python3 -m venv .venv
source .venv/bin/activate
pip install -r m8/requirements.txt

ollama pull gemma4:e2b          # chat model
ollama pull nomic-embed-text    # embedding model

cp .env.example .env            # LLM_PROVIDER=ollama is the default
jupyter notebook m8/
```

Open the RAG notebooks from inside `m8/` so that relative paths (`data/...`) resolve. The notebooks read settings from the `.env` file in the repository root. `.env` is ignored by git: never commit API keys. M1 has its own small setup in `m1/README.md`.

### Choosing the models

Chat model and embedding model are always separate choices:

- `OLLAMA_MODEL` and `OLLAMA_EMBEDDING_MODEL` in `.env` select the local models.
- `LLM_PROVIDER` can switch to `openai`, `gemini` or `deepseek` (their API keys are then required), to compare a local model with a hosted one.
- Alternatively, run a LiteLLM gateway with `m8/litellm/config.yaml` (`pip install "litellm[proxy]"`) and address models by logical name.

**If you change the embedding model, delete and rebuild the collections**: vectors from different models are not comparable.

## M1 lab

`m1/01_bert_tokenization.ipynb` is the short WordPiece exercise; `m1/02_bert_text_classification.ipynb` covers dataset-to-classifier; `m1/03_hub_wildcard_memory_estimator.ipynb` searches models with wildcards and estimates memory. See `m1/README.md`.

## M8 RAG labs

| Notebook | Topic | Data |
| --- | --- | --- |
| `m8/01_chroma_from_scratch.ipynb` | Ingestion, semantic search and a RAG chatbot built from three functions; a safe prompt that refuses to invent answers. | Text chunks inside the notebook |
| `m8/02_qa_across_documents.ipynb` | Loaders for DOCX, PDF and TXT, a folder ingestion loop, a LangChain RAG chain, stateless versus conversational follow-up questions. | `m8/data/Paestum`, `m8/data/CilentoTouristInfo` |
| `m8/03_advanced_indexing.ipynb` | Granular versus coarse chunks, parent-document, multi-vector, summary and hypothetical-question indexing. | `m8/data/wikivoyage` |
| `m8/04_question_transformations.ipynb` | Rewrite-retrieve-read, multi-query, step-back and HyDE. | `m8/data/wikivoyage` |
| `m8/05_query_generation.ipynb` | Metadata filters, self-querying, text-to-SQL, routing between sources and RAG fusion. | `m8/data/wikivoyage`, `m8/*.sql` |

Suggested way of working: keep a table with one row per run (chat model, embedding model, parameters, question, answer, whether it is correct and grounded in the retrieved text).

Notes:

- Outputs are cleared in the notebooks; run the cells to see results.
- `m8/02_` skips the Wikipedia download of the original exercise: ingestion uses only the local files.
- `m8/05_` creates a SQLite database (`UkBooking.db`) from the two SQL scripts the first time it runs.
- Web pages are read through `m8/local_html.py`, which mimics the web loader on saved copies.

## Data and licences

- `m8/data/wikivoyage/`: raw HTML of 21 pages of English Wikivoyage, saved once by `scripts/fetch_wikivoyage_pages.py`. The text is available under a Creative Commons Attribution-ShareAlike licence; authors and licence version are listed on each source page (see `m8/data/wikivoyage/README.md`).
- `m8/data/Paestum` and `m8/data/CilentoTouristInfo`: sample tourist documents collected for the original exercises, used here as a teaching corpus.
- The code is for teaching purposes.
