"""
Selenium tests for Data Management — Pagination (DM-32 to DM-35).

This module automates test cases DM-32 through DM-35 from the WATT-IF
Test Plan, covering pagination controls when the Entry History table
contains more than 10 entries, verifying correct page size, navigation
between pages, absence of controls for small data sets, and entry count
label accuracy.

Requirements covered: 8.1–8.4
"""

from __future__ import annotations

import time

import pytest

from tests.selenium.pages.data_entry_page import DataEntryPage


@pytest.mark.data_management
class TestPagination:
    """Pagination tests (DM-32 to DM-35)."""

    @pytest.fixture(autouse=True)
    def setup_page(self, logged_in_driver, base_url):
        """Navigate to the Data Entry page before each test."""
        self.page = DataEntryPage(logged_in_driver, base_url)
        self.page.navigate_to_data_entry()
        # Wait briefly for the page to stabilize
        time.sleep(1)

    @pytest.mark.data_management
    def test_DM_32_first_page_ten_rows(self, logged_in_driver, test_csv_path):
        """DM-32: When more than 10 entries exist, first page shows exactly 10 rows.

        Steps:
        1. Navigate to Data Entry page
        2. Upload synthetic_2022_2025.csv (48 rows) to ensure >10 entries
        3. Verify the first page displays exactly 10 rows in Entry History

        Expected: First page shows exactly 10 rows when total entries exceed 10.
        """
        # Upload CSV to get >10 entries
        self.page.upload_csv(str(test_csv_path))

        # Wait for upload to complete and table to refresh
        time.sleep(3)

        # Refresh page to ensure pagination is applied from a clean state
        self.page.navigate_to_data_entry()
        time.sleep(2)

        # Verify exactly 10 rows on first page
        rows = self.page.get_entry_rows()
        assert len(rows) == 10, (
            f"Expected exactly 10 rows on the first page, got {len(rows)}"
        )

    @pytest.mark.data_management
    def test_DM_33_next_page_different_rows(self, logged_in_driver, test_csv_path):
        """DM-33: Click Next page button displays a different set of rows.

        Steps:
        1. Navigate to Data Entry page
        2. Upload synthetic_2022_2025.csv (48 rows) to ensure multiple pages
        3. Record the text of the first row on page 1
        4. Click Next Page button
        5. Verify the first row on page 2 has different text than page 1's first row

        Expected: After clicking Next, the table displays a different set of rows.
        """
        # Upload CSV to get >10 entries
        self.page.upload_csv(str(test_csv_path))

        # Wait for upload to complete and table to refresh
        time.sleep(3)

        # Refresh page to ensure pagination is applied from a clean state
        self.page.navigate_to_data_entry()
        time.sleep(2)

        # Record text of rows on page 1
        page_1_first_row = self.page.get_row_text(0)

        # Click Next Page
        self.page.click_next_page()
        time.sleep(1)

        # Verify page 2 displays different rows
        page_2_first_row = self.page.get_row_text(0)
        assert page_1_first_row != page_2_first_row, (
            "Expected different rows after clicking Next Page, "
            f"but page 1 row 0 '{page_1_first_row}' equals page 2 row 0 '{page_2_first_row}'"
        )

    @pytest.mark.data_management
    def test_DM_34_no_pagination_few_entries(self, logged_in_driver, base_url):
        """DM-34: When 10 or fewer entries exist, pagination controls are not displayed.

        Steps:
        1. Navigate to Data Entry page (fresh user, no existing entries)
        2. Add a few entries manually (3 entries) so total is ≤10
        3. Verify pagination controls are not present

        Expected: No pagination buttons visible when entry count is ≤10.
        """
        # Add a few entries manually (≤10) with unique months to avoid conflicts
        self.page.add_entry("2028-01", 200)
        time.sleep(1)
        self.page.add_entry("2028-02", 250)
        time.sleep(1)
        self.page.add_entry("2028-03", 300)
        time.sleep(1)

        # Verify no pagination controls are present
        has_pagination = self.page.has_pagination()
        assert not has_pagination, (
            "Expected no pagination controls when entry count is ≤10"
        )

    @pytest.mark.data_management
    def test_DM_35_entry_count_label(self, logged_in_driver, test_csv_path):
        """DM-35: Entry count label displays the correct total number of entries.

        Steps:
        1. Navigate to Data Entry page
        2. Upload synthetic_2022_2025.csv (48 rows)
        3. Verify the entry count label shows the correct total (48 entries)

        Expected: Count label matches the total number of entries in the database.
        """
        # Upload CSV to get known number of entries
        self.page.upload_csv(str(test_csv_path))

        # Wait for upload to complete
        time.sleep(3)

        # Refresh page to ensure count is accurate
        self.page.navigate_to_data_entry()
        time.sleep(2)

        # Verify entry count label matches total
        count_text = self.page.get_entry_count()
        assert "48" in count_text, (
            f"Expected entry count label to contain '48', got: '{count_text}'"
        )
