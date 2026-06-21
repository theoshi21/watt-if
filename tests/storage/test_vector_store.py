"""
Unit tests for storage/vector_store.py  (task 6.1).

Uses an in-memory ChromaDB client so no files are written to disk.
"""

from __future__ import annotations

import uuid

import chromadb
import pytest

from pipeline.models import ForecastDocument, ForecastMetadata
from storage.vector_store import VectorStore, VectorStoreError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(
    forecast_month: str = "2026-01",
    horizon_label: str = "1m",
    kwh: float = 350.0,
    price: float = 85.0,
) -> ForecastDocument:
    doc_id = f"{forecast_month}_{horizon_label}"
    text = (
        f"Forecast for {forecast_month} (horizon: {horizon_label}):\n"
        f"  Electricity consumption: {kwh:.2f} kWh\n"
        f"  Electricity price: £{price:.2f}"
    )
    return ForecastDocument(
        id=doc_id,
        text=text,
        metadata=ForecastMetadata(
            forecast_month=forecast_month,
            forecasted_kwh=kwh,
            forecasted_price=price,
            horizon_label=horizon_label,
        ),
    )


@pytest.fixture()
def store(monkeypatch: pytest.MonkeyPatch) -> VectorStore:
    """Return a VectorStore backed by an in-memory ChromaDB client.

    Each test gets a unique collection name to ensure full isolation even
    though the underlying chromadb.Client() shares an in-process store.
    """
    unique_name = f"test_{uuid.uuid4().hex}"
    monkeypatch.setattr("storage.vector_store.COLLECTION_NAME", unique_name)
    client = chromadb.Client()
    return VectorStore(client=client)


# ---------------------------------------------------------------------------
# collection_size
# ---------------------------------------------------------------------------

class TestCollectionSize:
    def test_empty_store_returns_zero(self, store: VectorStore) -> None:
        assert store.collection_size() == 0

    def test_size_increases_after_upsert(self, store: VectorStore) -> None:
        store.upsert(_make_doc("2026-01", "1m"))
        assert store.collection_size() == 1

    def test_size_reflects_multiple_documents(self, store: VectorStore) -> None:
        store.upsert(_make_doc("2026-01", "1m"))
        store.upsert(_make_doc("2026-02", "1m"))
        store.upsert(_make_doc("2026-03", "3m"))
        assert store.collection_size() == 3


# ---------------------------------------------------------------------------
# upsert
# ---------------------------------------------------------------------------

class TestUpsert:
    def test_upsert_adds_document(self, store: VectorStore) -> None:
        doc = _make_doc("2026-01", "1m")
        store.upsert(doc)
        assert store.collection_size() == 1

    def test_upsert_is_idempotent(self, store: VectorStore) -> None:
        """Upserting the same ID twice must not create a duplicate."""
        doc = _make_doc("2026-01", "1m", kwh=300.0)
        store.upsert(doc)

        # Overwrite with updated values
        updated_doc = _make_doc("2026-01", "1m", kwh=999.0)
        store.upsert(updated_doc)

        assert store.collection_size() == 1

    def test_upsert_replaces_existing_document_content(self, store: VectorStore) -> None:
        """After a second upsert the stored document reflects the new content."""
        store.upsert(_make_doc("2026-01", "1m", kwh=300.0))
        store.upsert(_make_doc("2026-01", "1m", kwh=999.0))

        results = store.query("electricity forecast January", top_k=1)
        assert len(results) == 1
        assert results[0].metadata.forecasted_kwh == pytest.approx(999.0)

    def test_upsert_different_horizon_same_month_creates_separate_entries(
        self, store: VectorStore
    ) -> None:
        """Same forecast_month but different horizon_label → separate documents."""
        store.upsert(_make_doc("2026-01", "1m"))
        store.upsert(_make_doc("2026-01", "3m"))
        assert store.collection_size() == 2

    def test_upsert_stores_correct_metadata(self, store: VectorStore) -> None:
        doc = _make_doc("2026-03", "3m", kwh=420.5, price=101.25)
        store.upsert(doc)

        results = store.query("March electricity", top_k=1)
        assert len(results) == 1
        meta = results[0].metadata
        assert meta.forecast_month == "2026-03"
        assert meta.horizon_label == "3m"
        assert meta.forecasted_kwh == pytest.approx(420.5)
        assert meta.forecasted_price == pytest.approx(101.25)

    def test_upsert_embedding_failure_raises_vector_store_error(
        self, store: VectorStore, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A broken embedding model must surface as VectorStoreError."""

        def _bad_encode(*args, **kwargs):
            raise RuntimeError("GPU out of memory")

        monkeypatch.setattr(store._get_model(), "encode", _bad_encode)

        with pytest.raises(VectorStoreError):
            store.upsert(_make_doc())

    def test_upsert_embedding_failure_leaves_collection_unchanged(
        self, store: VectorStore, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """On embedding failure the collection must not grow."""
        store.upsert(_make_doc("2026-01", "1m"))  # succeeds
        size_before = store.collection_size()

        def _bad_encode(*args, **kwargs):
            raise RuntimeError("error")

        monkeypatch.setattr(store._get_model(), "encode", _bad_encode)

        with pytest.raises(VectorStoreError):
            store.upsert(_make_doc("2026-02", "1m"))

        assert store.collection_size() == size_before


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------

class TestQuery:
    def test_query_empty_store_returns_empty_list(self, store: VectorStore) -> None:
        results = store.query("electricity forecast")
        assert results == []

    def test_query_returns_forecast_documents(self, store: VectorStore) -> None:
        store.upsert(_make_doc("2026-01", "1m"))
        results = store.query("January electricity consumption")
        assert len(results) == 1
        assert isinstance(results[0], ForecastDocument)

    def test_query_top_k_limits_results(self, store: VectorStore) -> None:
        for month in ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]:
            store.upsert(_make_doc(month, "3m"))

        results = store.query("electricity forecast", top_k=3)
        assert len(results) <= 3

    def test_query_returns_all_when_fewer_than_top_k(self, store: VectorStore) -> None:
        store.upsert(_make_doc("2026-01", "1m"))
        store.upsert(_make_doc("2026-02", "1m"))

        results = store.query("electricity forecast", top_k=5)
        assert len(results) == 2

    def test_query_default_top_k_is_five(self, store: VectorStore) -> None:
        for month in ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]:
            store.upsert(_make_doc(month, "1m"))

        results = store.query("electricity forecast")  # default top_k=5
        assert len(results) == 5

    def test_query_result_metadata_matches_stored_document(
        self, store: VectorStore
    ) -> None:
        doc = _make_doc("2026-04", "6m", kwh=510.0, price=125.50)
        store.upsert(doc)

        results = store.query("April electricity price")
        assert len(results) == 1
        meta = results[0].metadata
        assert meta.forecast_month == "2026-04"
        assert meta.horizon_label == "6m"
        assert meta.forecasted_kwh == pytest.approx(510.0)
        assert meta.forecasted_price == pytest.approx(125.50)

    def test_query_returns_forecast_document_with_correct_id(
        self, store: VectorStore
    ) -> None:
        doc = _make_doc("2026-05", "3m")
        store.upsert(doc)

        results = store.query("May forecast")
        assert results[0].id == "2026-05_3m"
