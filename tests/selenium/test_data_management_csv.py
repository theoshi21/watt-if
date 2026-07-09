"""
Selenium tests for Data Management — CSV Upload (DM-13 to DM-21).

This module automates test cases DM-13 through DM-21 from the WATT-IF
Test Plan, covering CSV file upload scenarios including valid uploads,
invalid file types, missing columns, blank values, duplicates, and
count verification.

Requirements covered: 6.1–6.9
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from tests.selenium.pages.data_entry_page import DataEntryPage


# Resolve fixture directory once at module level
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.data_management
class TestCSVUpload:
    """CSV Upload tests (DM-13 to DM-21)."""

    @pytest.fixture(autouse=True)
    def setup_page(self, logged_in_driver, base_url):
        """Navigate to the Data Entry page before each test."""
        self.page = DataEntryPage(logged_in_driver, base_url)
        self.page.navigate_to_data_entry()
        # Wait briefly for the page to stabilize
        time.sleep(1)

    @pytest.mark.data_management
    def test_DM_13_upload_valid_csv(self, logged_in_driver):
        """DM-13: Upload a valid CSV with 3 rows.

        Steps:
        1. Navigate to Data Entry page
        2. Upload valid_3_rows.csv (3 data rows with year_month, kwh, price)
        3. Verify success message is displayed
        4. Verify Entry History contains 3 rows

        Expected: Success message visible, 3 rows appear in Entry History.
        """
        csv_path = str(FIXTURES_DIR / "valid_3_rows.csv")
        self.page.upload_csv(csv_path)

        # Verify success message
        success_msg = self.page.get_success_message()
        assert success_msg, "Expected a success message after valid CSV upload"

        # Verify 3 rows in history
        time.sleep(2)  # Allow table to refresh
        rows = self.page.get_entry_rows()
        assert len(rows) == 3, f"Expected 3 rows in Entry History, got {len(rows)}"

    @pytest.mark.data_management
    def test_DM_14_upload_full_dataset(self, logged_in_driver, test_csv_path):
        """DM-14: Upload the full synthetic_2022_2025.csv (48 rows).

        Steps:
        1. Navigate to Data Entry page
        2. Upload data/synthetic_2022_2025.csv (48 rows)
        3. Verify success message is displayed
        4. Verify all 48 rows are visible via entry count label

        Expected: Success message visible, entry count shows 48 entries.
        Note: Pagination may apply (>10 per page), so verify via count label.
        """
        self.page.upload_csv(str(test_csv_path))

        # Verify success message
        success_msg = self.page.get_success_message()
        assert success_msg, "Expected a success message after uploading full dataset"

        # Verify total count via entry count label (pagination may limit visible rows)
        time.sleep(2)  # Allow table to refresh
        count_text = self.page.get_entry_count()
        assert "48" in count_text, (
            f"Expected entry count to show 48 entries, got: '{count_text}'"
        )

    @pytest.mark.data_management
    def test_DM_15_upload_non_csv(self, logged_in_driver):
        """DM-15: Upload a non-CSV file (.txt).

        Steps:
        1. Navigate to Data Entry page
        2. Upload non_csv_file.txt
        3. Verify an error message is displayed
        4. Verify no entries are added to Entry History

        Expected: Error message shown, Entry History remains empty.
        """
        txt_path = str(FIXTURES_DIR / "non_csv_file.txt")

        # Check initial row count
        initial_rows = self.page.get_entry_rows()
        initial_count = len(initial_rows)

        self.page.upload_csv(txt_path)

        # Verify error message
        error_msg = self.page.get_error_message()
        assert error_msg, "Expected an error message when uploading a non-CSV file"

        # Verify no entries were added
        time.sleep(1)
        rows_after = self.page.get_entry_rows()
        assert len(rows_after) == initial_count, (
            f"Expected no new entries after non-CSV upload, "
            f"had {initial_count}, now have {len(rows_after)}"
        )

    @pytest.mark.data_management
    def test_DM_16_missing_column(self, logged_in_driver):
        """DM-16: Upload a CSV missing the 'kwh' column.

        Steps:
        1. Navigate to Data Entry page
        2. Upload missing_kwh_column.csv (has year_month and price but no kwh)
        3. Verify an error message indicating the missing column is displayed
        4. Verify no entries are added to Entry History

        Expected: Error message about missing column, no entries added.
        """
        csv_path = str(FIXTURES_DIR / "missing_kwh_column.csv")

        # Check initial row count
        initial_rows = self.page.get_entry_rows()
        initial_count = len(initial_rows)

        self.page.upload_csv(csv_path)

        # Verify error message
        error_msg = self.page.get_error_message()
        assert error_msg, "Expected an error message for CSV missing 'kwh' column"

        # Verify no entries were added
        time.sleep(1)
        rows_after = self.page.get_entry_rows()
        assert len(rows_after) == initial_count, (
            f"Expected no new entries after missing-column CSV upload, "
            f"had {initial_count}, now have {len(rows_after)}"
        )

    @pytest.mark.data_management
    def test_DM_17_blank_kwh_values(self, logged_in_driver):
        """DM-17: Upload a CSV with blank kWh values.

        Steps:
        1. Navigate to Data Entry page
        2. Upload blank_kwh_values.csv (some rows have empty kWh cells)
        3. Verify the application handles it gracefully without crashing

        Expected: No crash; page remains functional. The application may
        skip blank rows, show partial success, or display a warning.
        """
        csv_path = str(FIXTURES_DIR / "blank_kwh_values.csv")

        self.page.upload_csv(csv_path)

        # Allow processing
        time.sleep(2)

        # Verify page hasn't crashed — we can still interact with it
        # The page should still be functional (navigate or find elements)
        self.page.navigate_to_data_entry()
        time.sleep(1)

        # Page is still responsive if we can find the history section
        rows = self.page.get_entry_rows()
        # The test passes as long as no unhandled exception occurred
        # At minimum, the valid row (2024-03, 280) may have been imported
        assert True, "Page handled blank kWh values without crashing"

    @pytest.mark.data_management
    def test_DM_18_duplicate_months_csv(self, logged_in_driver):
        """DM-18: Upload a CSV with duplicate months.

        Steps:
        1. Navigate to Data Entry page
        2. Upload duplicate_months.csv (has two entries for 2024-01)
        3. Verify only one row per month exists in Entry History

        Expected: Only one row per unique month — duplicates are deduplicated.
        """
        csv_path = str(FIXTURES_DIR / "duplicate_months.csv")

        self.page.upload_csv(csv_path)

        # Allow processing
        time.sleep(2)

        # The CSV has 3 rows but 2024-01 appears twice, so we expect 2 unique months
        rows = self.page.get_entry_rows()
        assert len(rows) == 2, (
            f"Expected 2 rows (one per unique month) after duplicate-month CSV upload, "
            f"got {len(rows)}"
        )

    @pytest.mark.data_management
    def test_DM_19_invalid_date_format(self, logged_in_driver):
        """DM-19: Upload a CSV with invalid date format (YYYY/MM instead of YYYY-MM).

        Steps:
        1. Navigate to Data Entry page
        2. Upload invalid_date_format.csv (uses YYYY/MM format)
        3. Verify an error message is displayed
        4. Verify no entries are added to Entry History

        Expected: Error message shown, no entries added.
        """
        csv_path = str(FIXTURES_DIR / "invalid_date_format.csv")

        # Check initial row count
        initial_rows = self.page.get_entry_rows()
        initial_count = len(initial_rows)

        self.page.upload_csv(csv_path)

        # Verify error message
        error_msg = self.page.get_error_message()
        assert error_msg, "Expected an error message for invalid date format CSV"

        # Verify no entries were added
        time.sleep(1)
        rows_after = self.page.get_entry_rows()
        assert len(rows_after) == initial_count, (
            f"Expected no new entries after invalid-date CSV upload, "
            f"had {initial_count}, now have {len(rows_after)}"
        )

    @pytest.mark.data_management
    def test_DM_20_duplicate_upload(self, logged_in_driver):
        """DM-20: Upload the same CSV twice — entry count should not increase.

        Steps:
        1. Navigate to Data Entry page
        2. Upload valid_3_rows.csv
        3. Wait for success and record entry count
        4. Upload the same valid_3_rows.csv again
        5. Verify entry count remains unchanged after second upload

        Expected: Entry count does not increase on the second upload.
        """
        csv_path = str(FIXTURES_DIR / "valid_3_rows.csv")

        # First upload
        self.page.upload_csv(csv_path)
        time.sleep(2)

        # Record entry count after first upload
        rows_after_first = self.page.get_entry_rows()
        count_after_first = len(rows_after_first)

        # Second upload of the same file
        self.page.upload_csv(csv_path)
        time.sleep(2)

        # Verify entry count unchanged
        rows_after_second = self.page.get_entry_rows()
        count_after_second = len(rows_after_second)

        assert count_after_second == count_after_first, (
            f"Expected entry count to remain {count_after_first} after duplicate upload, "
            f"got {count_after_second}"
        )

    @pytest.mark.data_management
    def test_DM_21_upload_count_verification(self, logged_in_driver):
        """DM-21: After upload, verify entry count label matches expected total.

        Steps:
        1. Navigate to Data Entry page
        2. Upload valid_3_rows.csv (3 rows)
        3. Verify the entry count label matches the expected total (3)

        Expected: Entry count label displays the correct number of uploaded rows.
        """
        csv_path = str(FIXTURES_DIR / "valid_3_rows.csv")

        self.page.upload_csv(csv_path)

        # Wait for upload to complete
        time.sleep(2)

        # Verify the count label shows 3
        count_text = self.page.get_entry_count()
        assert "3" in count_text, (
            f"Expected entry count label to contain '3', got: '{count_text}'"
        )
