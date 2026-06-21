"""
Unit tests for DataPipeline — task 2.3 scope.

Covers:
  - kWh/price imputation via linear interpolation (Req 1.6)
  - Edge-case imputation via forward/backward fill (Req 1.7)
  - rows_imputed reporting in CleaningReport
  - Deduplication — keep last occurrence per year_month (Req 1.8)
  - Persist to SQLite monthly_bill_records (upsert on year_month) (Req 1.9)
  - get_monthly_records() query
  - get_training_window_extent() query
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pipeline.data_pipeline import DataPipeline
from pipeline.models import MonthlyRecord
from storage.db import create_in_memory_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_csv(tmp_path: Path, content: str) -> str:
    """Write *content* to a temp CSV and return its path as a string."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(textwrap.dedent(content).strip())
    return str(csv_file)


@pytest.fixture()
def pipeline(db):
    """Return a DataPipeline wired to an in-memory SQLite database."""
    return DataPipeline(db_conn=db)


# ---------------------------------------------------------------------------
# Imputation tests — linear interpolation (Req 1.6)
# ---------------------------------------------------------------------------


class TestImputation:
    def test_null_kwh_middle_is_interpolated(self, pipeline, tmp_path):
        """A null kWh value bracketed by 10 and 20 should be imputed to 15."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,10.0,1.00
            2024-02,,1.50
            2024-03,20.0,2.00
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"
        records = pipeline.get_monthly_records("2024-01", "2024-03")
        assert len(records) == 3
        assert records[1].kwh == pytest.approx(15.0)

    def test_null_price_middle_is_interpolated(self, pipeline, tmp_path):
        """A null price bracketed by 1.0 and 3.0 should be imputed to 2.0."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,10.0,1.00
            2024-02,12.0,
            2024-03,14.0,3.00
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"
        records = pipeline.get_monthly_records("2024-01", "2024-03")
        assert records[1].price == pytest.approx(2.0)

    def test_non_numeric_kwh_is_imputed(self, pipeline, tmp_path):
        """A non-numeric kWh string should be coerced to NaN and imputed."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,10.0,1.00
            2024-02,bad_value,1.50
            2024-03,20.0,2.00
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"
        records = pipeline.get_monthly_records("2024-01", "2024-03")
        assert records[1].kwh == pytest.approx(15.0)

    def test_imputed_row_recorded_in_cleaning_report(self, pipeline, tmp_path):
        """Imputed rows must appear in cleaning_report.rows_imputed."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,10.0,1.00
            2024-02,,1.50
            2024-03,20.0,2.00
            """,
        )
        result = pipeline.ingest(csv)
        imputed = result.cleaning_report.rows_imputed
        assert len(imputed) == 1
        entry = imputed[0]
        assert entry["field"] == "kwh"
        assert entry["replacement"] == pytest.approx(15.0)

    def test_imputed_entry_contains_required_keys(self, pipeline, tmp_path):
        """Each imputed entry must have row_index, field, original, replacement."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,10.0,1.00
            2024-02,,2.00
            2024-03,30.0,3.00
            """,
        )
        result = pipeline.ingest(csv)
        entry = result.cleaning_report.rows_imputed[0]
        assert "row_index" in entry
        assert "field" in entry
        assert "original" in entry
        assert "replacement" in entry

    def test_no_nulls_produces_empty_rows_imputed(self, pipeline, tmp_path):
        """A clean CSV with no nulls should leave rows_imputed empty."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,10.0,1.00
            2024-02,12.0,1.20
            """,
        )
        result = pipeline.ingest(csv)
        assert result.cleaning_report.rows_imputed == []

    # -- Edge-case fill (Req 1.7) ----------------------------------------

    def test_leading_null_kwh_uses_backward_fill(self, pipeline, tmp_path):
        """A null at the start of kWh (no preceding value) must be backward-filled."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,,1.00
            2024-02,20.0,2.00
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"
        records = pipeline.get_monthly_records("2024-01", "2024-02")
        # Backward-fill: row 0 gets the value from row 1.
        assert records[0].kwh == pytest.approx(20.0)
        assert len(result.cleaning_report.rows_imputed) == 1

    def test_trailing_null_price_uses_forward_fill(self, pipeline, tmp_path):
        """A null at the end of price (no following value) must be forward-filled."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,10.0,1.00
            2024-02,12.0,
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"
        records = pipeline.get_monthly_records("2024-01", "2024-02")
        assert records[1].price == pytest.approx(1.00)
        assert len(result.cleaning_report.rows_imputed) == 1

    def test_multiple_nulls_both_fields_all_flagged(self, pipeline, tmp_path):
        """Multiple nulls across both fields should all appear in rows_imputed."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,10.0,1.00
            2024-02,,
            2024-03,30.0,3.00
            """,
        )
        result = pipeline.ingest(csv)
        assert len(result.cleaning_report.rows_imputed) == 2
        fields_imputed = {e["field"] for e in result.cleaning_report.rows_imputed}
        assert fields_imputed == {"kwh", "price"}


# ---------------------------------------------------------------------------
# Deduplication tests (Req 1.8)
# ---------------------------------------------------------------------------


class TestDeduplication:
    def test_duplicate_year_month_keeps_last_occurrence(self, pipeline, tmp_path):
        """When the same year_month appears twice, the last row's values are kept."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,10.0,1.00
            2024-01,99.0,9.99
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"
        records = pipeline.get_monthly_records("2024-01", "2024-01")
        assert len(records) == 1
        assert records[0].kwh == pytest.approx(99.0)
        assert records[0].price == pytest.approx(9.99)

    def test_duplicate_count_in_cleaning_report(self, pipeline, tmp_path):
        """Number of rows removed by deduplication must be in the report."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,10.0,1.00
            2024-01,20.0,2.00
            2024-02,15.0,1.50
            """,
        )
        result = pipeline.ingest(csv)
        assert result.cleaning_report.duplicate_rows_removed == 1

    def test_no_duplicates_reports_zero_removed(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,10.0,1.00
            2024-02,12.0,1.20
            """,
        )
        result = pipeline.ingest(csv)
        assert result.cleaning_report.duplicate_rows_removed == 0

    def test_three_duplicates_keeps_last(self, pipeline, tmp_path):
        """Three rows with the same year_month — only the third must survive."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-03,1.0,0.10
            2024-03,2.0,0.20
            2024-03,3.0,0.30
            """,
        )
        result = pipeline.ingest(csv)
        assert result.cleaning_report.duplicate_rows_removed == 2
        records = pipeline.get_monthly_records("2024-03", "2024-03")
        assert records[0].kwh == pytest.approx(3.0)

    def test_row_count_reflects_post_dedup(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,10.0,1.00
            2024-01,20.0,2.00
            2024-02,15.0,1.50
            """,
        )
        result = pipeline.ingest(csv)
        assert result.row_count == 2


# ---------------------------------------------------------------------------
# Monthly bill records persistence (Req 1.9)
# ---------------------------------------------------------------------------


class TestMonthlyPersistence:
    def test_monthly_records_persisted_after_ingest(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-03,320.5,64.10
            2024-04,295.0,59.00
            """,
        )
        pipeline.ingest(csv)
        records = pipeline.get_monthly_records("2024-03", "2024-04")
        assert len(records) == 2

    def test_monthly_record_values_correct(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-05,310.0,62.00
            """,
        )
        pipeline.ingest(csv)
        records = pipeline.get_monthly_records("2024-05", "2024-05")
        assert records[0].kwh == pytest.approx(310.0)
        assert records[0].price == pytest.approx(62.00)
        assert records[0].year_month == "2024-05"

    def test_get_monthly_records_range_filtering(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,100.0,20.00
            2024-02,110.0,22.00
            2024-03,120.0,24.00
            2024-04,130.0,26.00
            """,
        )
        pipeline.ingest(csv)
        records = pipeline.get_monthly_records("2024-02", "2024-03")
        assert len(records) == 2
        assert records[0].year_month == "2024-02"
        assert records[1].year_month == "2024-03"

    def test_get_monthly_records_empty_range_returns_empty_list(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,100.0,20.00
            """,
        )
        pipeline.ingest(csv)
        records = pipeline.get_monthly_records("2025-06", "2025-12")
        assert records == []

    def test_monthly_records_are_monthlyrecord_instances(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-07,280.0,56.00
            """,
        )
        pipeline.ingest(csv)
        records = pipeline.get_monthly_records("2024-07", "2024-07")
        assert isinstance(records[0], MonthlyRecord)

    def test_upsert_replaces_existing_record(self, pipeline, tmp_path):
        """Re-ingesting new data for the same year_month should replace via upsert."""
        csv1 = tmp_path / "first.csv"
        csv1.write_text("year_month,kwh,price\n2024-01,100.0,20.00\n")
        csv2 = tmp_path / "second.csv"
        csv2.write_text("year_month,kwh,price\n2024-01,999.0,99.99\n")

        pipeline.ingest(str(csv1))
        pipeline.ingest(str(csv2))

        records = pipeline.get_monthly_records("2024-01", "2024-01")
        assert len(records) == 1
        assert records[0].kwh == pytest.approx(999.0)

    def test_records_sorted_ascending_after_ingest(self, pipeline, tmp_path):
        """Records must be returned in ascending year_month order."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-06,60.0,12.00
            2024-03,30.0,6.00
            2024-09,90.0,18.00
            """,
        )
        pipeline.ingest(csv)
        records = pipeline.get_monthly_records("2024-01", "2024-12")
        year_months = [r.year_month for r in records]
        assert year_months == sorted(year_months)


# ---------------------------------------------------------------------------
# get_training_window_extent (Req 1.9)
# ---------------------------------------------------------------------------


class TestTrainingWindowExtent:
    def test_returns_min_and_max_year_month(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2023-11,250.0,50.00
            2023-12,270.0,54.00
            2024-01,310.0,62.00
            """,
        )
        pipeline.ingest(csv)
        start, end = pipeline.get_training_window_extent()
        assert start == "2023-11"
        assert end == "2024-01"

    def test_single_record_min_equals_max(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-05,300.0,60.00
            """,
        )
        pipeline.ingest(csv)
        start, end = pipeline.get_training_window_extent()
        assert start == end == "2024-05"

    def test_raises_value_error_when_no_records(self, pipeline):
        """With an empty database, get_training_window_extent() must raise ValueError."""
        with pytest.raises(ValueError, match="No records"):
            pipeline.get_training_window_extent()

    def test_extent_updates_after_second_ingest(self, pipeline, tmp_path):
        csv1_path = tmp_path / "first.csv"
        csv1_path.write_text("year_month,kwh,price\n2024-01,100.0,20.00\n")

        csv2_path = tmp_path / "second.csv"
        csv2_path.write_text("year_month,kwh,price\n2024-12,110.0,22.00\n")

        pipeline.ingest(str(csv1_path))
        pipeline.ingest(str(csv2_path))
        start, end = pipeline.get_training_window_extent()
        assert start == "2024-01"
        assert end == "2024-12"
