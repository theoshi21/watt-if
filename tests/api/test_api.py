"""
Smoke tests for the WATT-IF FastAPI server (api/main.py).

Uses FastAPI TestClient with mocked backend services so that no real
SQLite, ChromaDB, SARIMAX artefact, or Ollama instance is required.

Covers:
  - POST /upload: valid CSV, missing columns, oversized file, path-traversal filename
  - POST /forecast: valid horizons, invalid horizon
  - POST /ask: valid question, empty question, question > 500 chars, Ollama 503 path
  - GET /health: all operational, mixed degraded
"""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.schemas import ForecastResponse, HealthResponse
from pipeline.models import (
    CleaningReport,
    ForecastMetadata,
    ForecastMonth,
    IngestResult,
)
from rag.rag_service import RAGResponse

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

client = TestClient(app, raise_server_exceptions=False)

# A minimal valid CSV body.
_VALID_CSV = (
    "year_month,kwh,price\n"
    "2024-01,320.5,85.20\n"
    "2024-02,310.0,82.50\n"
    "2024-03,295.0,79.00\n"
)


def _make_ingest_ok(rows: int = 3) -> IngestResult:
    return IngestResult(
        validation_status="ok",
        error_message=None,
        row_count=rows,
        cleaning_report=CleaningReport(
            total_rows_received=rows,
            rows_with_invalid_year_month=[],
            rows_imputed=[],
            duplicate_rows_removed=0,
            rows_after_cleaning=rows,
        ),
    )


def _make_ingest_error(msg: str) -> IngestResult:
    return IngestResult(
        validation_status="error",
        error_message=msg,
        row_count=0,
        cleaning_report=None,
    )


def _make_forecast_months(n: int) -> list[ForecastMonth]:
    return [
        ForecastMonth(
            year_month=f"2026-0{i+1}",
            kwh_forecast=300.0 + i,
            kwh_lower_95=270.0 + i,
            kwh_upper_95=330.0 + i,
            price_forecast=85.0 + i,
            price_lower_95=75.0 + i,
            price_upper_95=95.0 + i,
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# POST /upload
# ---------------------------------------------------------------------------

class TestUpload:
    def _post(self, content: bytes, filename: str = "bills.csv"):
        return client.post(
            "/upload",
            files={"file": (filename, io.BytesIO(content), "text/csv")},
        )

    def test_valid_csv_returns_200(self):
        with (
            patch("api.main._get_db_conn") as mock_conn,
            patch("api.main.DataPipeline") as mock_pipeline_cls,
        ):
            mock_pipeline_cls.return_value.ingest.return_value = _make_ingest_ok(3)
            resp = self._post(_VALID_CSV.encode())

        assert resp.status_code == 200
        body = resp.json()
        assert body["validation_status"] == "ok"
        assert body["rows_received"] == 3

    def test_non_csv_extension_returns_400(self):
        resp = self._post(b"data", filename="bills.txt")
        assert resp.status_code == 400
        assert "csv" in resp.json()["detail"].lower()

    def test_oversized_file_returns_400(self):
        big_content = b"x" * (10 * 1024 * 1024 + 1)
        resp = self._post(big_content)
        assert resp.status_code == 400
        assert "10 MB" in resp.json()["detail"] or "limit" in resp.json()["detail"].lower()

    def test_path_traversal_filename_returns_400(self):
        resp = self._post(_VALID_CSV.encode(), filename="../../etc/passwd.csv")
        assert resp.status_code == 400
        assert "traversal" in resp.json()["detail"].lower() or "invalid" in resp.json()["detail"].lower()

    def test_path_traversal_with_backslash_returns_400(self):
        resp = self._post(_VALID_CSV.encode(), filename="..\\evil.csv")
        assert resp.status_code == 400

    def test_missing_columns_pipeline_error_returns_200_with_error_status(self):
        """DataPipeline returns validation_status='error' — server still returns 200."""
        with (
            patch("api.main._get_db_conn"),
            patch("api.main.DataPipeline") as mock_pipeline_cls,
        ):
            mock_pipeline_cls.return_value.ingest.return_value = _make_ingest_error(
                "Missing required column(s): kwh"
            )
            resp = self._post(b"year_month,price\n2024-01,85.0\n")

        assert resp.status_code == 200
        assert resp.json()["validation_status"] == "error"

    def test_retraining_triggered_is_false(self):
        with (
            patch("api.main._get_db_conn"),
            patch("api.main.DataPipeline") as mock_pipeline_cls,
        ):
            mock_pipeline_cls.return_value.ingest.return_value = _make_ingest_ok()
            resp = self._post(_VALID_CSV.encode())

        assert resp.json()["retraining_triggered"] is False


# ---------------------------------------------------------------------------
# POST /forecast
# ---------------------------------------------------------------------------

class TestForecast:
    def _post(self, payload: dict):
        return client.post("/forecast", json=payload)

    def test_invalid_horizon_returns_422(self):
        resp = self._post({"horizon": 2})
        assert resp.status_code == 422

    def test_horizon_zero_returns_422(self):
        resp = self._post({"horizon": 0})
        assert resp.status_code == 422

    def test_horizon_12_returns_422(self):
        resp = self._post({"horizon": 12})
        assert resp.status_code == 422

    def test_missing_horizon_returns_422(self):
        resp = self._post({})
        assert resp.status_code == 422

    def test_valid_horizon_1_returns_200(self):
        months = _make_forecast_months(1)
        with (
            patch("api.main.SARIMAXModel") as mock_model_cls,
            patch("api.main.VectorStore") as mock_vs_cls,
        ):
            mock_model = MagicMock()
            mock_model.forecast.return_value = months
            mock_model_cls.return_value = mock_model
            mock_vs_cls.return_value.upsert.return_value = None

            resp = self._post({"horizon": 1})

        assert resp.status_code == 200
        body = resp.json()
        assert body["horizon"] == 1
        assert len(body["months"]) == 1

    def test_valid_horizon_3_returns_200(self):
        months = _make_forecast_months(3)
        with (
            patch("api.main.SARIMAXModel") as mock_model_cls,
            patch("api.main.VectorStore") as mock_vs_cls,
        ):
            mock_model = MagicMock()
            mock_model.forecast.return_value = months
            mock_model_cls.return_value = mock_model
            mock_vs_cls.return_value.upsert.return_value = None

            resp = self._post({"horizon": 3})

        assert resp.status_code == 200
        assert len(resp.json()["months"]) == 3

    def test_valid_horizon_6_returns_200(self):
        months = _make_forecast_months(6)
        with (
            patch("api.main.SARIMAXModel") as mock_model_cls,
            patch("api.main.VectorStore") as mock_vs_cls,
        ):
            mock_model = MagicMock()
            mock_model.forecast.return_value = months
            mock_model_cls.return_value = mock_model
            mock_vs_cls.return_value.upsert.return_value = None

            resp = self._post({"horizon": 6})

        assert resp.status_code == 200
        assert len(resp.json()["months"]) == 6

    def test_model_not_found_returns_503(self):
        with patch("api.main.SARIMAXModel") as mock_model_cls:
            mock_model = MagicMock()
            mock_model.load.side_effect = FileNotFoundError("artefact missing")
            mock_model_cls.return_value = mock_model

            resp = self._post({"horizon": 3})

        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# POST /ask
# ---------------------------------------------------------------------------

class TestAsk:
    def _post(self, payload: dict):
        return client.post("/ask", json=payload)

    def test_empty_question_returns_422(self):
        resp = self._post({"question": ""})
        assert resp.status_code == 422

    def test_question_over_500_chars_returns_422(self):
        resp = self._post({"question": "x" * 501})
        assert resp.status_code == 422

    def test_missing_question_returns_422(self):
        resp = self._post({})
        assert resp.status_code == 422

    def test_valid_question_returns_200(self):
        sources = [
            ForecastMetadata(
                forecast_month="2026-03",
                forecasted_kwh=320.5,
                forecasted_price=85.2,
                horizon_label="3m",
            )
        ]
        rag_resp = RAGResponse(
            answer="Your forecast for March 2026 is 320.5 kWh.",
            sources=sources,
            error=False,
        )
        with patch("api.main.RAGService") as mock_rag_cls:
            mock_rag_cls.return_value.answer.return_value = rag_resp
            resp = self._post({"question": "What is my forecast for March 2026?"})

        assert resp.status_code == 200
        body = resp.json()
        assert "320.5" in body["answer"]
        assert len(body["sources"]) == 1

    def test_ollama_unavailable_returns_503(self):
        rag_resp = RAGResponse(
            answer="The LLM service (Ollama) is currently unavailable.",
            sources=[],
            error=True,
        )
        with patch("api.main.RAGService") as mock_rag_cls:
            mock_rag_cls.return_value.answer.return_value = rag_resp
            resp = self._post({"question": "What is my forecast?"})

        assert resp.status_code == 503

    def test_no_forecast_data_returns_200(self):
        """Zero-docs path: RAGService returns error=False with a 'no data' message."""
        rag_resp = RAGResponse(
            answer="No forecast data is currently available.",
            sources=[],
            error=False,
        )
        with patch("api.main.RAGService") as mock_rag_cls:
            mock_rag_cls.return_value.answer.return_value = rag_resp
            resp = self._post({"question": "What is my forecast?"})

        assert resp.status_code == 200
        assert "no forecast data" in resp.json()["answer"].lower()

    def test_question_exactly_500_chars_returns_200(self):
        rag_resp = RAGResponse(answer="ok", sources=[], error=False)
        with patch("api.main.RAGService") as mock_rag_cls:
            mock_rag_cls.return_value.answer.return_value = rag_resp
            resp = self._post({"question": "a" * 500})

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_all_operational_returns_200(self):
        with (
            patch("api.main._get_db_conn") as mock_conn,
            patch("api.main.SARIMAXModel") as mock_model_cls,
            patch("api.main.VectorStore") as mock_vs_cls,
            patch("httpx.Client") as mock_http_cls,
        ):
            mock_conn.return_value.execute.return_value = None
            mock_conn.return_value.close.return_value = None
            mock_model_cls.return_value.load.return_value = None
            mock_vs_cls.return_value.collection_size.return_value = 0

            mock_http_instance = MagicMock()
            mock_http_cls.return_value.__enter__ = MagicMock(return_value=mock_http_instance)
            mock_http_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_http_instance.get.return_value.raise_for_status.return_value = None

            resp = client.get("/health")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert all(v == "operational" for v in body["subsystems"].values())

    def test_degraded_subsystem_returns_207(self):
        with (
            patch("api.main._get_db_conn") as mock_conn,
            patch("api.main.SARIMAXModel") as mock_model_cls,
            patch("api.main.VectorStore") as mock_vs_cls,
            patch("httpx.Client") as mock_http_cls,
        ):
            mock_conn.return_value.execute.return_value = None
            mock_conn.return_value.close.return_value = None
            # SARIMAX model artefact missing
            mock_model_cls.return_value.load.side_effect = FileNotFoundError("no artefact")
            mock_vs_cls.return_value.collection_size.return_value = 0

            mock_http_instance = MagicMock()
            mock_http_cls.return_value.__enter__ = MagicMock(return_value=mock_http_instance)
            mock_http_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_http_instance.get.return_value.raise_for_status.return_value = None

            resp = client.get("/health")

        assert resp.status_code == 207
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["subsystems"]["sarimax_model"] == "degraded"

    def test_health_response_has_all_subsystems(self):
        with (
            patch("api.main._get_db_conn") as mock_conn,
            patch("api.main.SARIMAXModel") as mock_model_cls,
            patch("api.main.VectorStore") as mock_vs_cls,
            patch("httpx.Client") as mock_http_cls,
        ):
            mock_conn.return_value.execute.return_value = None
            mock_conn.return_value.close.return_value = None
            mock_model_cls.return_value.load.return_value = None
            mock_vs_cls.return_value.collection_size.return_value = 0

            mock_http_instance = MagicMock()
            mock_http_cls.return_value.__enter__ = MagicMock(return_value=mock_http_instance)
            mock_http_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_http_instance.get.return_value.raise_for_status.return_value = None

            resp = client.get("/health")

        subsystems = resp.json()["subsystems"]
        assert "data_pipeline" in subsystems
        assert "sarimax_model" in subsystems
        assert "vector_store" in subsystems
        assert "llm_service" in subsystems
