#!/usr/bin/env python3
"""One-off data preparation: save the Wikivoyage pages used by the RAG labs as local HTML.

The labs then read these files and need no internet access.
Run: python3 scripts/fetch_wikivoyage_pages.py
"""
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

DEST = [
    "Cornwall", "North_Cornwall", "South_Cornwall", "West_Cornwall", "Tintagel", "Bodmin",
    "Wadebridge", "Penzance", "Newquay", "St_Ives", "Port_Isaac", "Looe", "Polperro", "Porthleven",
    "East_Sussex", "Brighton", "Battle", "Hastings_(England)", "Rye_(England)", "Seaford", "Ashdown_Forest",
]
OUT = Path(__file__).resolve().parent.parent / "rag/data/wikivoyage"
OUT.mkdir(parents=True, exist_ok=True)
ok = []
for d in DEST:
    url = f"https://en.wikivoyage.org/wiki/{urllib.parse.quote(d, safe='_()')}"
    req = urllib.request.Request(url, headers={"User-Agent": "course-lab-data-fetch/1.0 (one-off, educational)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        (OUT / f"{d}.html").write_bytes(r.read())
    ok.append(d)
    print("saved", d)
    time.sleep(1.5)
(OUT / "README.md").write_text(
    "# Wikivoyage pages for the RAG labs\n\n"
    f"Raw HTML of {len(ok)} pages of [English Wikivoyage](https://en.wikivoyage.org), fetched once on {date.today().isoformat()} "
    "by `scripts/fetch_wikivoyage_pages.py`, so that the labs run without internet access.\n\n"
    "Wikivoyage text is available under a Creative Commons Attribution-ShareAlike licence; the exact version and the "
    "list of authors are given on each page of the source site. Pages: "
    + ", ".join(f"[{d.replace('_', ' ')}](https://en.wikivoyage.org/wiki/{d})" for d in ok) + ".\n",
    encoding="utf-8")
