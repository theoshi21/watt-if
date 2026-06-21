"""
Ingest EDA summaries into the ChromaDB vector store (EDA collection).

Reads data/eda_summaries.json (produced by data/eda.py) and upserts each
summary as a document into the 'eda_documents' ChromaDB collection so the
RAG service can retrieve historical-dataset context alongside forecast data.

Usage (run from project root):
    python data/eda.py          # generate summaries first
    python data/ingest_eda.py   # then ingest them
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on the path when run directly.
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage.eda_store import EDAStore  # noqa: E402  (after sys.path patch)

SUMMARIES_PATH = ROOT / "data" / "eda_summaries.json"


def main() -> None:
    if not SUMMARIES_PATH.exists():
        print(f"ERROR: {SUMMARIES_PATH} not found. Run `python data/eda.py` first.")
        sys.exit(1)

    with open(SUMMARIES_PATH, encoding="utf-8") as f:
        summaries: list[dict[str, str]] = json.load(f)

    print(f"Loaded {len(summaries)} EDA summaries from {SUMMARIES_PATH}")

    store = EDAStore()
    ingested = 0
    for entry in summaries:
        store.upsert(doc_id=entry["id"], text=entry["text"])
        ingested += 1
        print(f"  ✓ upserted: {entry['id']}")

    print(f"\nIngested {ingested} EDA documents into ChromaDB (collection: eda_documents).")
    print(f"Collection now has {store.collection_size()} documents total.")


if __name__ == "__main__":
    main()
