"""
Vector Store for WATT-IF forecast documents.

Wraps ChromaDB with sentence-transformers embeddings (all-MiniLM-L6-v2) for
storing and retrieving ForecastDocument objects via cosine similarity search.

Each document is indexed by the ID "{forecast_month}_{horizon_label}" so that
upserting a document for the same month+horizon pair replaces the existing
entry — no duplicates.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from pipeline.models import ForecastDocument, ForecastMetadata

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Default persistent path; tests may override via the constructor.
DEFAULT_CHROMA_PATH = Path(__file__).parent.parent / "data" / "chroma"

# Embedding model name (sentence-transformers).
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ChromaDB collection name.
COLLECTION_NAME = "forecast_documents"


class VectorStoreError(Exception):
    """Raised when the vector store encounters an unrecoverable error."""


class VectorStore:
    """ChromaDB-backed store for WATT-IF Forecast Documents.

    Parameters
    ----------
    chroma_path:
        Directory where ChromaDB persists its files.  Pass ``":memory:"`` (or
        leave as *None* and set *client* directly) for an in-memory store —
        useful for tests.
    client:
        Optional pre-constructed ``chromadb.Client`` instance.  When
        provided, *chroma_path* is ignored.  Primarily for testing.
    model_name:
        sentence-transformers model used for embedding.  Defaults to
        ``all-MiniLM-L6-v2``.
    """

    def __init__(
        self,
        chroma_path: str | Path | None = None,
        *,
        client: chromadb.ClientAPI | None = None,
        model_name: str = EMBEDDING_MODEL,
    ) -> None:
        # ── Embedding model ──────────────────────────────────────────────────
        self._model_name = model_name
        self._model: SentenceTransformer | None = None  # lazy-loaded

        # ── ChromaDB client ───────────────────────────────────────────────────
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

        # ── Collection (cosine similarity) ────────────────────────────────────
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_model(self) -> SentenceTransformer:
        """Lazily load and cache the sentence-transformers model."""
        if self._model is None:
            logger.debug("Loading sentence-transformers model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def _embed(self, text: str) -> list[float]:
        """Return the embedding vector for *text*.

        Raises
        ------
        VectorStoreError
            If the embedding model raises any exception.
        """
        try:
            model = self._get_model()
            vector = model.encode(text, convert_to_numpy=True)
            return vector.tolist()
        except Exception as exc:
            raise VectorStoreError(
                f"Embedding failed for text (first 80 chars): {text[:80]!r}"
            ) from exc

    # ── Public interface ──────────────────────────────────────────────────────

    def upsert(self, doc: ForecastDocument) -> None:
        """Embed and upsert a :class:`~pipeline.models.ForecastDocument`.

        The document is stored under the ID
        ``"{forecast_month}_{horizon_label}"`` (e.g. ``"2026-03_3m"``), which
        guarantees that a subsequent upsert for the same month+horizon pair
        replaces the existing entry rather than creating a duplicate.

        Parameters
        ----------
        doc:
            The forecast document to embed and store.

        Raises
        ------
        VectorStoreError
            If the sentence-transformers embedding step fails.  The collection
            is left unchanged in that case.
        """
        # Embedding may raise VectorStoreError — let it propagate so callers
        # know the document was NOT stored.
        embedding = self._embed(doc.text)

        metadata: dict = {
            "forecast_month":    doc.metadata.forecast_month,
            "forecasted_kwh":    doc.metadata.forecasted_kwh,
            "forecasted_price":  doc.metadata.forecasted_price,
            "horizon_label":     doc.metadata.horizon_label,
            "meralco_rate":      doc.metadata.meralco_rate,
            "avg_temperature":   doc.metadata.avg_temperature,
            "avg_humidity":      doc.metadata.avg_humidity,
            "total_rainfall_mm": doc.metadata.total_rainfall_mm,
            "holiday_count":     doc.metadata.holiday_count,
            "weekend_count":     doc.metadata.weekend_count,
            "hot_days_count":    doc.metadata.hot_days_count,
            "rainy_days_count":  doc.metadata.rainy_days_count,
            "is_el_nino":        doc.metadata.is_el_nino,
        }

        self._collection.upsert(
            ids=[doc.id],
            embeddings=[embedding],
            documents=[doc.text],
            metadatas=[metadata],
        )
        logger.debug("Upserted document id=%r into collection.", doc.id)

    def query(self, question: str, top_k: int = 5) -> list[ForecastDocument]:
        """Return up to *top_k* :class:`~pipeline.models.ForecastDocument`
        objects most similar to *question*, ranked by cosine similarity.

        Returns an empty list if the collection is empty.

        Parameters
        ----------
        question:
            Natural-language query string to embed and search against.
        top_k:
            Maximum number of results to return.  Actual count may be less if
            fewer documents exist in the store.
        """
        total = self.collection_size()
        if total == 0:
            return []

        # Clamp n_results to the actual collection size to avoid ChromaDB
        # raising an error when top_k > number of stored documents.
        n_results = min(top_k, total)

        question_embedding = self._embed(question)

        results = self._collection.query(
            query_embeddings=[question_embedding],
            n_results=n_results,
            include=["documents", "metadatas"],
        )

        docs: list[ForecastDocument] = []
        for doc_text, meta, doc_id in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["ids"][0],
        ):
            forecast_metadata = ForecastMetadata(
                forecast_month=meta["forecast_month"],
                forecasted_kwh=float(meta["forecasted_kwh"]),
                forecasted_price=float(meta["forecasted_price"]),
                horizon_label=meta["horizon_label"],
                meralco_rate=float(meta.get("meralco_rate", 0.0)),
                avg_temperature=float(meta.get("avg_temperature", 0.0)),
                avg_humidity=float(meta.get("avg_humidity", 0.0)),
                total_rainfall_mm=float(meta.get("total_rainfall_mm", 0.0)),
                holiday_count=int(meta.get("holiday_count", 0)),
                weekend_count=int(meta.get("weekend_count", 0)),
                hot_days_count=int(meta.get("hot_days_count", 0)),
                rainy_days_count=int(meta.get("rainy_days_count", 0)),
                is_el_nino=int(meta.get("is_el_nino", 0)),
            )
            docs.append(
                ForecastDocument(
                    id=doc_id,
                    text=doc_text,
                    metadata=forecast_metadata,
                )
            )

        return docs

    def collection_size(self) -> int:
        """Return the total number of documents currently in the collection."""
        return self._collection.count()
