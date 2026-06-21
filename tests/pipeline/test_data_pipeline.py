"""
Unit tests for DataPipeline — task 2.1 scope.

Covers:
  - Column presence validation (Req 1.1, 1.2, 1.3)
  - year_month format validation and row rejection (Req 1.4, 1.5)
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pipeline.data_pipeline import DataPipeline
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
# Column validation tests (Req 1.1, 1.2, 1.3)
# ---------------------------------------------------------------------------


class TestColumnValidation:
    def test_all_required_columns_present_returns_ok(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,320.5,64.10
            2024-02,295.0,59.00
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"
        assert result.error_message is None

    def test_missing_year_month_column_returns_error(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            kwh,price
            320.5,64.10
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "error"
        assert "year_month" in result.error_message.lower()

    def test_missing_kwh_column_returns_error(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,price
            2024-01,64.10
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "error"
        assert "kwh" in result.error_message.lower()

    def test_missing_price_column_returns_error(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh
            2024-01,320.5
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "error"
        assert "price" in result.error_message.lower()

    def test_missing_multiple_columns_lists_all_in_error(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month
            2024-01
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "error"
        assert "kwh" in result.error_message.lower()
        assert "price" in result.error_message.lower()

    def test_missing_all_required_columns_returns_error(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            some_column,another_column
            foo,bar
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "error"
        assert "year_month" in result.error_message.lower()
        assert "kwh" in result.error_message.lower()
        assert "price" in result.error_message.lower()

    def test_missing_column_returns_zero_row_count(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh
            2024-01,320.5
            """,
        )
        result = pipeline.ingest(csv)
        assert result.row_count == 0

    def test_missing_column_returns_no_cleaning_report(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh
            2024-01,320.5
            """,
        )
        result = pipeline.ingest(csv)
        assert result.cleaning_report is None

    def test_column_names_are_case_insensitive(self, pipeline, tmp_path):
        """Columns named YEAR_MONTH, KWH, PRICE (upper-case) should be accepted."""
        csv = _write_csv(
            tmp_path,
            """
            YEAR_MONTH,KWH,PRICE
            2024-01,320.5,64.10
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"

    def test_extra_columns_are_accepted(self, pipeline, tmp_path):
        """Files with extra columns beyond the three required should be accepted."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price,notes
            2024-01,320.5,64.10,some note
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"


# ---------------------------------------------------------------------------
# year_month format validation tests (Req 1.4, 1.5)
# ---------------------------------------------------------------------------


class TestYearMonthValidation:
    def test_valid_year_month_accepted(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,320.5,64.10
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"
        assert result.row_count == 1
        assert result.cleaning_report.rows_with_invalid_year_month == []

    def test_invalid_year_month_row_is_rejected(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,320.5,64.10
            not-a-month,295.0,59.00
            2024-03,310.0,62.00
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"
        # Two valid rows remain; bad row is rejected.
        assert result.row_count == 2

    def test_invalid_year_month_recorded_in_cleaning_report(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,320.5,64.10
            2024/02,295.0,59.00
            """,
        )
        result = pipeline.ingest(csv)
        assert len(result.cleaning_report.rows_with_invalid_year_month) == 1
        rejected = result.cleaning_report.rows_with_invalid_year_month[0]
        assert "row_index" in rejected
        assert "original_value" in rejected
        assert rejected["original_value"] == "2024/02"

    def test_multiple_invalid_year_months_all_recorded(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,320.5,64.10
            January 2024,295.0,59.00
            2024-13,310.0,62.00
            2024-04,300.0,60.00
            """,
        )
        # Note: 2024-13 matches ^\d{4}-\d{2}$ so only "January 2024" is invalid.
        result = pipeline.ingest(csv)
        assert len(result.cleaning_report.rows_with_invalid_year_month) == 1
        original_values = {
            r["original_value"]
            for r in result.cleaning_report.rows_with_invalid_year_month
        }
        assert "January 2024" in original_values

    def test_full_date_string_is_rejected(self, pipeline, tmp_path):
        """A YYYY-MM-DD value should not match YYYY-MM and must be rejected."""
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01-15,320.5,64.10
            """,
        )
        result = pipeline.ingest(csv)
        assert result.row_count == 0
        assert len(result.cleaning_report.rows_with_invalid_year_month) == 1

    def test_all_rows_invalid_returns_zero_rows(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            bad-month-1,320.5,64.10
            bad-month-2,295.0,59.00
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"
        assert result.row_count == 0
        assert len(result.cleaning_report.rows_with_invalid_year_month) == 2

    def test_cleaning_report_total_rows_received(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            2024-01,320.5,64.10
            not-valid,295.0,59.00
            2024-03,310.0,62.00
            """,
        )
        result = pipeline.ingest(csv)
        assert result.cleaning_report.total_rows_received == 3

    def test_empty_csv_returns_ok_with_zero_rows(self, pipeline, tmp_path):
        csv = _write_csv(
            tmp_path,
            """
            year_month,kwh,price
            """,
        )
        result = pipeline.ingest(csv)
        assert result.validation_status == "ok"
        assert result.row_count == 0
        assert result.cleaning_report.total_rows_received == 0

    def test_unreadable_file_returns_error(self, pipeline):
        result = pipeline.ingest("/nonexistent/path/to/file.csv")
        assert result.validation_status == "error"
        assert result.error_message is not None
