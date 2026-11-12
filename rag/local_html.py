"""Load Wikivoyage pages from local files instead of downloading them.

LocalHtmlLoader(url).load() behaves like AsyncHtmlLoader(url).load() for the pages saved in
rag/data/wikivoyage: it returns one Document whose page_content is the raw HTML and whose
metadata["source"] is the original URL (kept so answers can cite the source).
"""
from pathlib import Path
from urllib.parse import unquote, urlparse

from langchain_core.documents import Document

DATA_DIR = Path(__file__).resolve().parent / "data" / "wikivoyage"


class LocalHtmlLoader:
    def __init__(self, url):
        self.urls = [url] if isinstance(url, str) else list(url)

    def load(self):
        docs = []
        for url in self.urls:
            name = unquote(urlparse(url).path.rsplit("/", 1)[-1])
            path = DATA_DIR / f"{name}.html"
            if not path.exists():
                raise FileNotFoundError(
                    f"No local copy of {url}. Expected {path}. "
                    "Run scripts/fetch_wikivoyage_pages.py to create it."
                )
            docs.append(Document(page_content=path.read_text(encoding="utf-8"),
                                 metadata={"source": url}))
        return docs
