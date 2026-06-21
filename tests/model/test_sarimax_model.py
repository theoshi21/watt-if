"""
Unit tests for SARIMAXModel — tasks 5.1 and 5.3.

Covers:
  - ModelTrainingError on insufficient data (< 14 records)      Req 3.6
  - Successful training produces a persisted artefact            Req 3.2, 3.3
  - Artefact contains required fields                            Req 3.3
  - MAPE is logged / computed on validation set                  Req 3.4
  - load() round-trip preserves artefact fields                  Req 3.3
  - forecast() honours valid horizons {1, 3, 6}                  Req 4.2
  - forecast() rejects invalid horizons                          Req 4.2
  - forecast() returns non-negative values                       Req 4.1
  - forecast() falls back to historical means when exog=None     Req 4.4
  - forecast() raises on insufficient historical records         Req 4.6
  - backup() / delete_backup() round-trip                        Req 9.5, 9.6
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from model.sarimax_model import SARIMAXModel
from pipeline.models import EnrichedRecord, ExogenousRow, ModelTrainingError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_enriched_records(n: int, start_year: int = 2020) -> list[EnrichedRecord]:
    """Generate *n* synthetic monthly EnrichedRecords starting from start_year-01."""
    records: list[EnrichedRecord] = []
    year, month = start_year, 1
    for i in range(n):
        # Simple sinusoidal kWh signal with mild upward trend + noise proxy
        kwh = 300.0 + 60.0 * math.sin(2 * math.pi * month / 12) + i * 0.5
        price = kwh * 0.20
        records.append(
            EnrichedRecord(
                year_month=f"{year:04d}-{month:02d}",
                kwh=kwh,
                price=price,
                mean_temp_c=15.0 - 10.0 * math.cos(2 * math.pi * month / 12),
                total_precip_mm=50.0 + 20.0 * math.sin(2 * math.pi * month / 12),
                holiday_count=1 if month in (1, 12) else 0,
            )
        )
        month += 1
        if month > 12:
            month = 1
            year += 1
    return records


@pytest.fixture()
def model_artefact_path(tmp_path: Path) -> Path:
    """Return a temp path for the model artefact."""
    return tmp_path / "sarimax_model.joblib"


@pytest.fixture()
def model(model_artefact_path: Path) -> SARIMAXModel:
    """Return an untrained SARIMAXModel backed by a temp artefact path."""
    return SARIMAXModel(artefact_path=model_artefact_path)


@pytest.fixture()
def trained_model(model: SARIMAXModel) -> SARIMAXModel:
    """Return a trained SARIMAXModel with 30 synthetic records."""
    records = _make_enriched_records(30)
    model.train(records)
    return model


# ---------------------------------------------------------------------------
# Task 5.1 — Training
# ---------------------------------------------------------------------------


class TestTraining:
    def test_raises_on_too_few_records(self, model: SARIMAXModel) -> None:
        """Fewer than 14 records must raise ModelTrainingError."""
        records = _make_enriched_records(13)
        with pytest.raises(ModelTrainingError, match="Insufficient data"):
            model.train(records)

    def test_raises_on_zero_records(self, model: SARIMAXModel) -> None:
        with pytest.raises(ModelTrainingError):
            model.train([])

    def test_exactly_14_records_does_not_raise(
        self, model: SARIMAXModel
    ) -> None:
        """Exactly 14 records is the minimum; training must succeed."""
        records = _make_enriched_records(14)
        result = model.train(records)
        assert result is not None

    def test_artefact_file_is_written(
        self, model: SARIMAXModel, model_artefact_path: Path
    ) -> None:
        records = _make_enriched_records(24)
        model.train(records)
        assert model_artefact_path.exists()
        assert model_artefact_path.stat().st_size > 0

    def test_training_result_contains_required_fields(
        self, model: SARIMAXModel
    ) -> None:
        """TrainingResult must expose order, seasonal_order, mape, window, path."""
        records = _make_enriched_records(24)
        result = model.train(records)
        # order is (p, d, q)
        assert len(result.order) == 3
        # seasonal_order is (P, D, Q, s)
        assert len(result.seasonal_order) == 4
        assert result.seasonal_order[3] == 12   # s=12 fixed
        assert isinstance(result.mape_validation, float)
        assert result.mape_validation >= 0.0
        assert "start" in result.training_window
        assert "end" in result.training_window
        assert result.artefact_path.endswith(".joblib")

    def test_training_window_covers_80pct_of_data(
        self, model: SARIMAXModel
    ) -> None:
        """Training window start/end should reflect the 80% train split."""
        records = _make_enriched_records(20)
        result = model.train(records)
        # First 16 records are training (80% of 20)
        assert result.training_window["start"] == records[0].year_month
        assert result.training_window["end"] == records[15].year_month

    def test_mape_is_non_negative_finite(self, model: SARIMAXModel) -> None:
        records = _make_enriched_records(24)
        result = model.train(records)
        assert math.isfinite(result.mape_validation)
        assert result.mape_validation >= 0.0


class TestLoad:
    def test_load_restores_artefact(
        self, model: SARIMAXModel, model_artefact_path: Path
    ) -> None:
        """load() must populate the internal artefact from disk."""
        records = _make_enriched_records(24)
        original_result = model.train(records)

        fresh_model = SARIMAXModel(artefact_path=model_artefact_path)
        assert fresh_model._artefact is None
        fresh_model.load()
        assert fresh_model._artefact is not None

    def test_load_preserves_order(
        self, model: SARIMAXModel, model_artefact_path: Path
    ) -> None:
        records = _make_enriched_records(24)
        original_result = model.train(records)

        fresh_model = SARIMAXModel(artefact_path=model_artefact_path)
        fresh_model.load()
        assert fresh_model._artefact["order"] == original_result.order
        assert fresh_model._artefact["seasonal_order"] == original_result.seasonal_order

    def test_load_preserves_exog_columns(
        self, model: SARIMAXModel, model_artefact_path: Path
    ) -> None:
        records = _make_enriched_records(24)
        model.train(records)

        fresh_model = SARIMAXModel(artefact_path=model_artefact_path)
        fresh_model.load()
        assert fresh_model._artefact["exog_columns"] == [
            "mean_temp_c",
            "total_precip_mm",
            "holiday_count",
        ]

    def test_load_raises_if_artefact_missing(self, tmp_path: Path) -> None:
        model = SARIMAXModel(artefact_path=tmp_path / "nonexistent.joblib")
        with pytest.raises(FileNotFoundError):
            model.load()


# ---------------------------------------------------------------------------
# Task 5.3 — Forecasting
# ---------------------------------------------------------------------------


class TestForecast:
    @pytest.mark.parametrize("horizon", [1, 3, 6])
    def test_valid_horizons_return_correct_month_count(
        self, trained_model: SARIMAXModel
    , horizon: int) -> None:
        """POST /forecast must return exactly `horizon` ForecastMonth entries."""
        records = _make_enriched_records(30)
        exog = [
            ExogenousRow(
                year_month="2000-01",  # dummy, not used for labelling
                mean_temp_c=10.0,
                total_precip_mm=50.0,
                holiday_count=1,
            )
            for _ in range(horizon)
        ]
        result = trained_model.forecast(horizon=horizon, exog=exog,
                                        historical_records=records)
        assert len(result) == horizon

    def test_invalid_horizon_raises_value_error(
        self, trained_model: SARIMAXModel
    ) -> None:
        with pytest.raises(ValueError, match="Invalid horizon"):
            trained_model.forecast(horizon=2)

    def test_horizon_zero_raises_value_error(
        self, trained_model: SARIMAXModel
    ) -> None:
        with pytest.raises(ValueError, match="Invalid horizon"):
            trained_model.forecast(horizon=0)

    def test_all_forecast_values_are_non_negative(
        self, trained_model: SARIMAXModel
    ) -> None:
        """All point forecasts and CI bounds must be >= 0 (Req 4.1)."""
        records = _make_enriched_records(30)
        exog = [
            ExogenousRow(
                year_month="2000-01",
                mean_temp_c=10.0,
                total_precip_mm=50.0,
                holiday_count=1,
            )
            for _ in range(6)
        ]
        months = trained_model.forecast(horizon=6, exog=exog,
                                        historical_records=records)
        for fm in months:
            assert fm.kwh_forecast >= 0.0
            assert fm.kwh_lower_95 >= 0.0
            assert fm.kwh_upper_95 >= 0.0
            assert fm.price_forecast >= 0.0
            assert fm.price_lower_95 >= 0.0
            assert fm.price_upper_95 >= 0.0

    def test_year_month_labels_are_sequential(
        self, trained_model: SARIMAXModel
    ) -> None:
        """ForecastMonth year_month labels must follow the training window end."""
        records = _make_enriched_records(30)  # ends at 2022-06
        exog = [
            ExogenousRow(year_month="x", mean_temp_c=10.0,
                         total_precip_mm=50.0, holiday_count=0)
            for _ in range(3)
        ]
        months = trained_model.forecast(horizon=3, exog=exog,
                                        historical_records=records)
        # Training window end = records[23].year_month (80% of 30 = 24 records)
        training_end = records[23].year_month
        year, month = int(training_end[:4]), int(training_end[5:7])
        for i, fm in enumerate(months):
            expected_total = year * 12 + (month - 1) + (i + 1)
            expected_year, expected_m = divmod(expected_total, 12)
            expected_ym = f"{expected_year:04d}-{expected_m + 1:02d}"
            assert fm.year_month == expected_ym

    def test_exog_fallback_uses_historical_means(
        self, trained_model: SARIMAXModel
    ) -> None:
        """When exog=None, forecast must use historical means (Req 4.4).
        
        We verify this indirectly: the call must succeed and return results
        without raising, since we cannot inspect the internal fallback values
        directly in a unit test.
        """
        records = _make_enriched_records(30)
        # Pass exog=None to trigger fallback path
        months = trained_model.forecast(horizon=3, exog=None,
                                        historical_records=records)
        assert len(months) == 3

    def test_insufficient_historical_records_raises(
        self, trained_model: SARIMAXModel
    ) -> None:
        """Fewer than 14 historical records must raise ValueError (Req 4.6)."""
        records = _make_enriched_records(10)
        with pytest.raises(ValueError, match="Insufficient historical data"):
            trained_model.forecast(horizon=1, exog=None,
                                   historical_records=records)

    def test_forecast_without_loaded_model_raises(
        self, model_artefact_path: Path
    ) -> None:
        fresh_model = SARIMAXModel(artefact_path=model_artefact_path)
        with pytest.raises(ValueError, match="No SARIMAX artefact"):
            fresh_model.forecast(horizon=1)

    def test_exog_length_mismatch_raises(
        self, trained_model: SARIMAXModel
    ) -> None:
        """Providing wrong number of ExogenousRows must raise ValueError."""
        exog = [
            ExogenousRow(year_month="x", mean_temp_c=10.0,
                         total_precip_mm=50.0, holiday_count=0)
        ]
        with pytest.raises(ValueError, match="Expected 3"):
            trained_model.forecast(horizon=3, exog=exog)


# ---------------------------------------------------------------------------
# Backup / restore — Req 9.5, 9.6
# ---------------------------------------------------------------------------


class TestBackup:
    def test_backup_creates_file(
        self, trained_model: SARIMAXModel, model_artefact_path: Path
    ) -> None:
        backup_path = trained_model.backup()
        assert Path(backup_path).exists()

    def test_backup_path_contains_timestamp(
        self, trained_model: SARIMAXModel
    ) -> None:
        backup_path = trained_model.backup()
        assert "backup_" in Path(backup_path).name

    def test_delete_backup_removes_file(
        self, trained_model: SARIMAXModel
    ) -> None:
        backup_path = trained_model.backup()
        assert Path(backup_path).exists()
        trained_model.delete_backup(backup_path)
        assert not Path(backup_path).exists()

    def test_backup_raises_if_no_artefact(
        self, model_artefact_path: Path
    ) -> None:
        fresh_model = SARIMAXModel(artefact_path=model_artefact_path)
        with pytest.raises(FileNotFoundError):
            fresh_model.backup()

    def test_delete_backup_is_idempotent(
        self, trained_model: SARIMAXModel
    ) -> None:
        """Calling delete_backup on a non-existent path must not raise."""
        trained_model.delete_backup("/nonexistent/path/backup.joblib")
