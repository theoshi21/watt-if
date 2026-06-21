"""
Shared pytest fixtures for WATT-IF tests.

Provides:
- ``db``              — an in-memory SQLite connection with the full WATT-IF schema applied.
- ``chroma_client``   — an ephemeral in-memory ChromaDB client (no persistence).
- ``monthly_record``  — a sample MonthlyRecord instance.
- ``enriched_record`` — a sample EnrichedRecord instance.
- ``forecast_month``  — a sample ForecastMonth instance.
- ``forecast_metadata`` — a sample ForecastMetadata instance.
- ``forecast_document`` — a sample ForecastDocument instance.
- ``cleaning_report`` — a sample CleaningReport instance.
"""

from __future__ import annotations

import sqlite3

import chromadb
import pytest

from pipeline.models import (
    CleaningReport,
    EnrichedRecord,
    ForecastDocument,
    ForecastMetadata,
    ForecastMonth,
    MonthlyRecord,
)
from storage.db import create_in_memory_db


@pytest.fixture()
def db() -> sqlite3.Connection:
    """Yield a fresh in-memory SQLite connection with WATT-IF schema.

    The connection is closed automatically after each test.
    """
    conn = create_in_memory_db()
    yield conn
    conn.close()


@pytest.fixture()
def chroma_client() -> chromadb.ClientAPI:
    """Yield an ephemeral in-memory ChromaDB client.

    Uses ``chromadb.EphemeralClient()`` so no files are written to disk and
    each test starts with a clean, empty vector store.
    """
    client = chromadb.EphemeralClient()
    yield client


@pytest.fixture()
def monthly_record() -> MonthlyRecord:
    """Return a sample MonthlyRecord for use in tests."""
    return MonthlyRecord(
        year_month="2024-03",
        kwh=320.5,
        price=64.10,
    )


@pytest.fixture()
def enriched_record() -> EnrichedRecord:
    """Return a sample EnrichedRecord with all exogenous fields populated."""
    return EnrichedRecord(
        year_month="2024-03",
        kwh=320.5,
        price=64.10,
        mean_temp_c=8.4,
        total_precip_mm=52.3,
        holiday_count=1,
    )


@pytest.fixture()
def forecast_month() -> ForecastMonth:
    """Return a sample ForecastMonth with point forecast and 95% CI values."""
    return ForecastMonth(
        year_month="2026-04",
        kwh_forecast=310.0,
        kwh_lower_95=285.0,
        kwh_upper_95=335.0,
        price_forecast=62.0,
        price_lower_95=57.0,
        price_upper_95=67.0,
    )


@pytest.fixture()
def forecast_metadata() -> ForecastMetadata:
    """Return a sample ForecastMetadata instance."""
    return ForecastMetadata(
        forecast_month="2026-04",
        forecasted_kwh=310.0,
        forecasted_price=62.0,
        horizon_label="3m",
    )


@pytest.fixture()
def forecast_document(forecast_metadata: ForecastMetadata) -> ForecastDocument:
    """Return a sample ForecastDocument with embedded text and metadata."""
    return ForecastDocument(
        id="2026-04_3m",
        text=(
            "Forecast for 2026-04 (horizon: 3m):\n"
            "  Electricity consumption: 310.00 kWh (95% CI: 285.00 – 335.00)\n"
            "  Electricity price: £62.00 (95% CI: £57.00 – £67.00)"
        ),
        metadata=forecast_metadata,
    )


@pytest.fixture()
def cleaning_report() -> CleaningReport:
    """Return a sample CleaningReport representing a clean ingest run."""
    return CleaningReport(
        total_rows_received=12,
        rows_with_invalid_year_month=[],
        rows_imputed=[],
        duplicate_rows_removed=0,
        rows_after_cleaning=12,
    )
