"""
EDA Vector Store for WATT-IF.

Stores and retrieves exploratory-data-analysis (EDA) summary documents in a
dedicated ChromaDB collection ('eda_documents'), separate from forecast
documents.  Uses the same sentence-transformers embedding model as VectorStore.

Used by:
  - data/ingest_eda.py  — to populate the collection
  - rag/rag_service.py  — to retrieve relevant EDA context for a user query
"""

from __future__ import annotations

import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

DEFAULT_CHROMA_PATH = Path(__file__).parent.parent / "data" / "chroma"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EDA_COLLECTION_NAME = "eda_documents"


class EDAStoreError(Exception):
    """Raised when the EDA store encounters an unrecoverable error."""


class EDAStore:
    """ChromaDB-backed store for EDA summary documents.

    Parameters
    ----------
    chroma_path:
        Directory where ChromaDB persists its files.  Defaults to the same
        persistent path used by :class:`~storage.vector_store.VectorStore`.
        Pass ``":memory:"`` for an in-memory store (useful in tests).
    client:
        Optional pre-constructed ``chromadb.Client`` instance.  When provided,
        *chroma_path* is ignored.
    model_name:
        sentence-transformers model used for embedding.
    """

    def __init__(
        self,
        chroma_path: str | Path | None = None,
        *,
        client: chromadb.ClientAPI | None = None,
        model_name: str = EMBEDDING_MODEL,
    ) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

        if client is not None:
            self._client = client
        else:
            path = Path(chroma_path) if chroma_path is not None else DEFAULT_CHROMA_PATH
            if str(path) == ":memory:":
                self._client = chromadb.Client()
            else:
                path.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(
                    path=str(path),
                    settings=Settings(anonymized_telemetry=False),
                )

        self._collection = self._client.get_or_create_collection(
            name=EDA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.debug("Loading sentence-transformers model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def _embed(self, text: str) -> list[float]:
        try:
            vector = self._get_model().encode(text, convert_to_numpy=True)
            return vector.tolist()
        except Exception as exc:
            raise EDAStoreError(
                f"Embedding failed for text (first 80 chars): {text[:80]!r}"
            ) from exc

    # ── Public interface ──────────────────────────────────────────────────────

    def upsert(self, doc_id: str, text: str) -> None:
        """Embed and upsert an EDA summary document.

        Parameters
        ----------
        doc_id:
            Stable identifier for the document (e.g. ``"eda_overview"``).
            Upserting with the same ID replaces the existing entry.
        text:
            Human-readable summary text to embed and store.
        """
        embedding = self._embed(text)
        self._collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{"doc_type": "eda"}],
        )
        logger.debug("Upserted EDA document id=%r.", doc_id)

    def query(self, question: str, top_k: int = 3) -> list[str]:
        """Return up to *top_k* EDA summary texts most similar to *question*.

        Returns an empty list if the collection is empty.

        Parameters
        ----------
        question:
            Natural-language query to search against.
        top_k:
            Maximum number of results to return.
        """
        total = self.collection_size()
        if total == 0:
            return []

        n_results = min(top_k, total)
        embedding = self._embed(question)
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["documents"],
        )
        return results["documents"][0]

    def collection_size(self) -> int:
        """Return the total number of EDA documents in the collection."""
        return self._collection.count()
