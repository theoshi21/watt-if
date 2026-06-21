"""
Unit tests for model/retraining.py (tasks 10.1 and 10.2).

Tests are fully unit-level — all external collaborators (DataPipeline,
FeatureEngineeringService, SARIMAXModel, VectorStore) are mocked.

Covers:
  - Trigger condition: retraining fires iff new_latest_month > previous_latest_month
  - No-op when no new month
  - Backup created before training; deleted on success (Req 9.5, 9.6)
  - Failed training leaves existing artefact unchanged (via backup/restore)
  - Training log written with correct fields (Req 9.4)
  - Old log entries are purged after 90 days
  - Vector store upsert retried once on failure
  - RetrainingResult fields populated correctly
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from model.retraining import RetrainingResult, RetrainingService
from pipeline.models import (
    EnrichedRecord,
    ForecastMonth,
    ModelTrainingError,
    MonthlyRecord,
    TrainingResult,
)
from storage.db import create_in_memory_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_conn() -> sqlite3.Connection:
    """Fresh in-memory SQLite database for each test."""
    return create_in_memory_db()


def _make_monthly_records(n: int = 20) -> list[MonthlyRecord]:
    return [
        MonthlyRecord(year_month=f"202{i // 12 + 3}-{i % 12 + 1:02d}", kwh=300.0 + i, price=80.0 + i)
        for i in range(n)
    ]


def _make_enriched_records(n: int = 20) -> list[EnrichedRecord]:
    return [
        EnrichedRecord(
            year_month=f"202{i // 12 + 3}-{i % 12 + 1:02d}",
            kwh=300.0 + i,
            price=80.0 + i,
            mean_temp_c=15.0,
            total_precip_mm=50.0,
            holiday_count=2,
        )
        for i in range(n)
    ]


def _make_training_result() -> TrainingResult:
    return TrainingResult(
        order=(1, 0, 1),
        seasonal_order=(0, 1, 1, 12),
        mape_validation=0.08,
        training_window={"start": "2023-01", "end": "2024-08"},
        artefact_path="/data/sarimax_model.joblib",
    )


def _make_forecast_months(horizon: int) -> list[ForecastMonth]:
    return [
        ForecastMonth(
            year_month=f"2025-{i + 1:02d}",
            kwh_forecast=300.0,
            kwh_lower_95=270.0,
            kwh_upper_95=330.0,
            price_forecast=85.0,
            price_lower_95=75.0,
            price_upper_95=95.0,
        )
        for i in range(horizon)
    ]


def _make_service(
    db_conn: sqlite3.Connection,
    monthly_records: list[MonthlyRecord] | None = None,
    enriched_records: list[EnrichedRecord] | None = None,
    training_result: TrainingResult | None = None,
    training_side_effect=None,
    forecast_side_effect=None,
    backup_side_effect=None,
    backup_return: str = "/data/sarimax_model.backup_20250101T000000Z.joblib",
    window_extent: tuple[str, str] = ("2023-01", "2024-09"),
) -> tuple[RetrainingService, MagicMock, MagicMock, MagicMock, MagicMock]:
    """Build a RetrainingService with all collaborators mocked."""
    mock_pipeline = MagicMock()
    mock_pipeline.get_training_window_extent.return_value = window_extent
    mock_pipeline.get_monthly_records.return_value = monthly_records or _make_monthly_records()

    mock_feature = MagicMock()
    mock_feature.enrich.return_value = enriched_records or _make_enriched_records()

    mock_model = MagicMock()
    if training_side_effect:
        mock_model.train.side_effect = training_side_effect
    else:
        mock_model.train.return_value = training_result or _make_training_result()

    if backup_side_effect:
        mock_model.backup.side_effect = backup_side_effect
    else:
        mock_model.backup.return_value = backup_return

    if forecast_side_effect:
        mock_model.forecast.side_effect = forecast_side_effect
    else:
        mock_model.forecast.side_effect = lambda horizon, exog, historical_records: _make_forecast_months(horizon)

    mock_model._artefact_path = MagicMock()

    mock_vs = MagicMock()
    mock_vs.upsert.return_value = None

    with (
        patch("model.retraining.DataPipeline", return_value=mock_pipeline),
        patch("model.retraining.FeatureEngineeringService", return_value=mock_feature),
    ):
        svc = RetrainingService(
            db_conn=db_conn,
            model=mock_model,
            feature_service=mock_feature,
            vector_store=mock_vs,
        )

    # Attach mocked pipeline so tests can access it
    svc._pipeline_mock = mock_pipeline

    return svc, mock_pipeline, mock_feature, mock_model, mock_vs


# ---------------------------------------------------------------------------
# Trigger condition
# ---------------------------------------------------------------------------

class TestTriggerCondition:
    def test_triggered_when_new_month_greater(self, db_conn):
        svc, mock_pipeline, _, mock_model, _ = _make_service(
            db_conn, window_extent=("2023-01", "2024-09")
        )
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.triggered is True
        assert result.new_latest_month == "2024-09"

    def test_not_triggered_when_same_month(self, db_conn):
        svc, mock_pipeline, _, mock_model, _ = _make_service(
            db_conn, window_extent=("2023-01", "2024-08")
        )
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.triggered is False
        assert result.success is True
        mock_model.train.assert_not_called()

    def test_not_triggered_when_previous_is_later(self, db_conn):
        svc, mock_pipeline, _, mock_model, _ = _make_service(
            db_conn, window_extent=("2023-01", "2024-07")
        )
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.triggered is False
        mock_model.train.assert_not_called()

    def test_triggered_when_previous_is_none(self, db_conn):
        """First upload — no previous month — always triggers."""
        svc, mock_pipeline, _, mock_model, _ = _make_service(
            db_conn, window_extent=("2023-01", "2024-09")
        )
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month=None)

        assert result.triggered is True
        mock_model.train.assert_called_once()

    def test_not_triggered_when_no_records(self, db_conn):
        svc, mock_pipeline, _, mock_model, _ = _make_service(db_conn)
        mock_pipeline.get_training_window_extent.side_effect = ValueError("No records")

        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.triggered is False
        assert result.success is False
        mock_model.train.assert_not_called()


# ---------------------------------------------------------------------------
# Backup semantics (Req 9.5, 9.6)
# ---------------------------------------------------------------------------

class TestBackupSemantics:
    def test_backup_created_before_training(self, db_conn):
        svc, mock_pipeline, _, mock_model, _ = _make_service(db_conn)
        call_order: list[str] = []
        mock_model.backup.side_effect = lambda: call_order.append("backup") or "/bak"
        mock_model.train.side_effect = lambda records: (call_order.append("train") or _make_training_result())

        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.success is True
        assert call_order.index("backup") < call_order.index("train")

    def test_backup_deleted_on_success(self, db_conn):
        backup_path = "/data/sarimax_model.backup_20250101T000000Z.joblib"
        svc, mock_pipeline, _, mock_model, _ = _make_service(
            db_conn, backup_return=backup_path
        )
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.success is True
        mock_model.delete_backup.assert_called_once_with(backup_path)

    def test_backup_not_deleted_on_training_failure(self, db_conn):
        backup_path = "/data/sarimax_model.backup_20250101T000000Z.joblib"
        svc, mock_pipeline, _, mock_model, _ = _make_service(
            db_conn,
            backup_return=backup_path,
            training_side_effect=ModelTrainingError("convergence failure"),
        )
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.success is False
        mock_model.delete_backup.assert_not_called()

    def test_no_backup_on_first_training_run(self, db_conn):
        """FileNotFoundError from backup() is silently skipped (first-time run)."""
        svc, mock_pipeline, _, mock_model, _ = _make_service(
            db_conn,
            backup_side_effect=FileNotFoundError("no artefact"),
        )
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month=None)

        assert result.success is True
        mock_model.delete_backup.assert_not_called()


# ---------------------------------------------------------------------------
# Failure semantics (Req 9.3)
# ---------------------------------------------------------------------------

class TestFailureSemantics:
    def test_training_failure_returns_failed_result(self, db_conn):
        svc, mock_pipeline, _, mock_model, _ = _make_service(
            db_conn,
            training_side_effect=ModelTrainingError("auto_arima failed"),
        )
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.triggered is True
        assert result.success is False
        assert "Step 4" in result.error_message
        assert "auto_arima failed" in result.error_message

    def test_feature_engineering_failure_halts_pipeline(self, db_conn):
        svc, mock_pipeline, mock_feature, mock_model, _ = _make_service(db_conn)
        mock_feature.enrich.side_effect = RuntimeError("weather API down")

        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.success is False
        assert "Step 2" in result.error_message
        mock_model.train.assert_not_called()

    def test_forecast_failure_halts_pipeline(self, db_conn):
        svc, mock_pipeline, _, mock_model, _ = _make_service(
            db_conn,
            forecast_side_effect=ValueError("insufficient data"),
        )
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.success is False
        assert "Step 5" in result.error_message

    def test_no_crash_on_failure(self, db_conn):
        """A pipeline failure must never propagate as an unhandled exception."""
        svc, mock_pipeline, mock_feature, _, _ = _make_service(db_conn)
        mock_feature.enrich.side_effect = Exception("unexpected crash")

        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            try:
                result = svc.check_and_retrain(previous_latest_month="2024-08")
            except Exception as exc:
                pytest.fail(f"check_and_retrain raised unexpectedly: {exc}")

        assert result.success is False


# ---------------------------------------------------------------------------
# Training log (Req 9.4)
# ---------------------------------------------------------------------------

class TestTrainingLog:
    def test_training_log_written_on_success(self, db_conn):
        svc, mock_pipeline, _, _, _ = _make_service(db_conn)
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.success is True
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM training_log")
        rows = cursor.fetchall()
        assert len(rows) == 1
        row = rows[0]
        assert row["new_mape"] == pytest.approx(0.08)
        assert row["training_window_start"] == "2023-01"
        assert row["training_window_end"] == "2024-08"

    def test_training_log_not_written_on_failure(self, db_conn):
        svc, mock_pipeline, _, mock_model, _ = _make_service(
            db_conn,
            training_side_effect=ModelTrainingError("convergence failure"),
        )
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            svc.check_and_retrain(previous_latest_month="2024-08")

        cursor = db_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM training_log")
        assert cursor.fetchone()[0] == 0

    def test_old_log_entries_purged(self, db_conn):
        """Entries older than 90 days must be deleted."""
        old_ts = (
            datetime.now(timezone.utc) - timedelta(days=91)
        ).isoformat()
        cursor = db_conn.cursor()
        cursor.execute(
            "INSERT INTO training_log "
            "(trained_at, previous_mape, new_mape, training_window_start, training_window_end) "
            "VALUES (?, NULL, 0.10, '2022-01', '2022-12')",
            (old_ts,),
        )
        db_conn.commit()

        svc, mock_pipeline, _, _, _ = _make_service(db_conn)
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            svc.check_and_retrain(previous_latest_month="2024-08")

        cursor.execute("SELECT COUNT(*) FROM training_log WHERE trained_at = ?", (old_ts,))
        assert cursor.fetchone()[0] == 0

    def test_recent_log_entries_retained(self, db_conn):
        """Entries within 90 days must be kept."""
        recent_ts = (
            datetime.now(timezone.utc) - timedelta(days=30)
        ).isoformat()
        cursor = db_conn.cursor()
        cursor.execute(
            "INSERT INTO training_log "
            "(trained_at, previous_mape, new_mape, training_window_start, training_window_end) "
            "VALUES (?, NULL, 0.12, '2023-01', '2023-12')",
            (recent_ts,),
        )
        db_conn.commit()

        svc, mock_pipeline, _, _, _ = _make_service(db_conn)
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            svc.check_and_retrain(previous_latest_month="2024-08")

        cursor.execute("SELECT COUNT(*) FROM training_log WHERE trained_at = ?", (recent_ts,))
        assert cursor.fetchone()[0] == 1


# ---------------------------------------------------------------------------
# Vector store upsert retry
# ---------------------------------------------------------------------------

class TestVectorStoreUpsert:
    def test_all_horizons_upserted(self, db_conn):
        """Forecasts for horizons 1, 3, 6 are all upserted."""
        svc, mock_pipeline, _, _, mock_vs = _make_service(db_conn)
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.success is True
        # 1 + 3 + 6 = 10 documents
        assert mock_vs.upsert.call_count == 10

    def test_upsert_retried_once_on_failure(self, db_conn):
        """A single upsert failure is retried; second success means pipeline continues."""
        call_counts: dict[str, int] = {"count": 0}

        def flaky_upsert(doc):
            call_counts["count"] += 1
            if call_counts["count"] == 1:
                raise Exception("transient error")

        svc, mock_pipeline, _, _, mock_vs = _make_service(db_conn)
        mock_vs.upsert.side_effect = flaky_upsert

        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.success is True
        # 10 normal calls + 1 retry = 11 total
        assert call_counts["count"] == 11


# ---------------------------------------------------------------------------
# RetrainingResult fields
# ---------------------------------------------------------------------------

class TestRetrainingResultFields:
    def test_successful_result_fields(self, db_conn):
        svc, mock_pipeline, _, _, _ = _make_service(db_conn)
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.triggered is True
        assert result.success is True
        assert result.new_latest_month == "2024-09"
        assert result.new_mape == pytest.approx(0.08)
        assert result.error_message is None

    def test_no_trigger_result_fields(self, db_conn):
        svc, mock_pipeline, _, _, _ = _make_service(
            db_conn, window_extent=("2023-01", "2024-08")
        )
        with patch("model.retraining.DataPipeline", return_value=mock_pipeline):
            result = svc.check_and_retrain(previous_latest_month="2024-08")

        assert result.triggered is False
        assert result.success is True
        assert result.new_mape is None
        assert result.error_message is None
