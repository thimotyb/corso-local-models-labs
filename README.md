# Local LLM labs: companion repository

Hands-on notebooks and data for the course on local language models. This repository is self-contained: clone it, set up the environment below and run the labs. Nothing else is required.

## Contents

| Folder | What it contains |
| --- | --- |
| `rag/` | Five notebooks on Retrieval-Augmented Generation with Chroma, LangChain and local models, plus all the data they use. Fully offline once the models are downloaded. |
| `litellm/` | Example LiteLLM gateway configuration to choose the chat model and the embedding model by logical name. |
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
pip install -r rag/requirements.txt

ollama pull gemma4:e2b          # chat model
ollama pull nomic-embed-text    # embedding model

cp .env.example .env            # LLM_PROVIDER=ollama is the default
jupyter notebook rag/
```

Open the notebooks from inside `rag/` so that relative paths (`data/...`) resolve. The notebooks read settings from the `.env` file in the repository root. `.env` is ignored by git: never commit API keys.

### Choosing the models

Chat model and embedding model are always separate choices:

- `OLLAMA_MODEL` and `OLLAMA_EMBEDDING_MODEL` in `.env` select the local models.
- `LLM_PROVIDER` can switch to `openai`, `gemini` or `deepseek` (their API keys are then required), to compare a local model with a hosted one.
- Alternatively, run a LiteLLM gateway with `litellm/config.yaml` (`pip install "litellm[proxy]"`) and address models by logical name.

**If you change the embedding model, delete and rebuild the collections**: vectors from different models are not comparable.

## RAG labs

| Notebook | Topic | Data |
| --- | --- | --- |
| `rag/01_chroma_from_scratch.ipynb` | Ingestion, semantic search and a RAG chatbot built from three functions; a safe prompt that refuses to invent answers. | Text chunks inside the notebook |
| `rag/02_qa_across_documents.ipynb` | Loaders for DOCX, PDF and TXT, a folder ingestion loop, a LangChain RAG chain, stateless versus conversational follow-up questions. | `rag/data/Paestum`, `rag/data/CilentoTouristInfo` |
| `rag/03_advanced_indexing.ipynb` | Granular versus coarse chunks, parent-document, multi-vector, summary and hypothetical-question indexing. | `rag/data/wikivoyage` |
| `rag/04_question_transformations.ipynb` | Rewrite-retrieve-read, multi-query, step-back and HyDE. | `rag/data/wikivoyage` |
| `rag/05_query_generation.ipynb` | Metadata filters, self-querying, text-to-SQL, routing between sources and RAG fusion. | `rag/data/wikivoyage`, `rag/*.sql` |

Suggested way of working: keep a table with one row per run (chat model, embedding model, parameters, question, answer, whether it is correct and grounded in the retrieved text).

Notes:

- Outputs are cleared in the notebooks; run the cells to see results.
- `02_` skips the Wikipedia download of the original exercise: ingestion uses only the local files.
- `05_` creates a SQLite database (`UkBooking.db`) from the two SQL scripts the first time it runs.
- Web pages are read through `rag/local_html.py`, which mimics the web loader on saved copies.

## Data and licences

- `rag/data/wikivoyage/`: raw HTML of 21 pages of English Wikivoyage, saved once by `scripts/fetch_wikivoyage_pages.py`. The text is available under a Creative Commons Attribution-ShareAlike licence; authors and licence version are listed on each source page (see `rag/data/wikivoyage/README.md`).
- `rag/data/Paestum` and `rag/data/CilentoTouristInfo`: sample tourist documents collected for the original exercises, used here as a teaching corpus.
- The code is for teaching purposes.
