"""
Data Management test module (DM-01 to DM-40).

Covers manual entry validation, CSV upload, entry history CRUD,
model training, pagination, and clear all data flows for the
WATT-IF application.

Requirements: 5.1–5.12
"""

import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium.pages import DataEntryPage


# ---------------------------------------------------------------------------
# Manual Entry Tests (DM-01 through DM-12)
# ---------------------------------------------------------------------------


@pytest.mark.data_management
def test_DM_01_valid_entry(logged_in_driver, base_url):
    """Submitting a valid month and kWh value saves the entry. Entry appears in history."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Get initial row count
    initial_rows = len(page.get_entry_rows())

    # Add a valid entry with unique month
    page.add_entry("2027-01", 350)

    # Wait for the new row to appear in the table (polls until row count increases or timeout)
    from selenium.webdriver.support.ui import WebDriverWait
    WebDriverWait(logged_in_driver, 15).until(
        lambda d: len(page.get_entry_rows()) > initial_rows
    )

    # Verify entry appears in history
    rows = page.get_entry_rows()
    assert len(rows) > initial_rows, "Expected a new row in entry history after valid entry"


@pytest.mark.data_management
def test_DM_02_blank_kwh(logged_in_driver, base_url):
    """Submitting without kWh shows validation error. No entry added to history."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Get initial row count
    initial_rows = len(page.get_entry_rows())

    # Submit with blank kWh — select month but leave kWh empty
    page.add_entry("2027-02", "")

    # Wait briefly for validation to trigger
    time.sleep(1)

    # Verify error message appears (kWh validation: "Must be a number between...")
    error_msg = page.get_error_message()
    assert error_msg, "Expected an error message when kWh is blank"

    # Verify no new row was added
    rows = page.get_entry_rows()
    assert len(rows) == initial_rows, "No new row should be added when kWh is blank"


@pytest.mark.data_management
def test_DM_03_zero_kwh(logged_in_driver, base_url):
    """Zero kWh rejected. Error message shown and no entry added."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Get initial row count
    initial_rows = len(page.get_entry_rows())

    # Submit with kWh = 0
    page.add_entry("2027-03", 0)

    # Wait briefly for validation to trigger
    time.sleep(1)

    # Verify error message appears (client-side validation rejects 0)
    error_msg = page.get_error_message()
    assert error_msg, "Expected an error message when kWh is 0"

    # Verify no new row was added
    rows = page.get_entry_rows()
    assert len(rows) == initial_rows, "No new row should be added when kWh is 0"


@pytest.mark.data_management
def test_DM_04_negative_kwh(logged_in_driver, base_url):
    """Negative kWh rejected. Error message shown and no entry added."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Get initial row count
    initial_rows = len(page.get_entry_rows())

    # Submit with negative kWh
    page.add_entry("2027-04", -100)

    # Wait briefly for validation to trigger
    time.sleep(1)

    # Verify error message appears or form was not submitted
    # The HTML input type="number" with min=0 may reject negative input entirely,
    # or the client-side validation catches it
    error_msg = page.get_error_message()
    assert error_msg, "Expected an error message when kWh is negative"

    # Verify no new row was added
    rows = page.get_entry_rows()
    assert len(rows) == initial_rows, "No new row should be added when kWh is negative"


@pytest.mark.data_management
def test_DM_05_non_numeric_kwh(logged_in_driver, base_url):
    """Non-numeric kWh rejected. Field rejects letters or error shown. No entry created."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Get initial row count
    initial_rows = len(page.get_entry_rows())

    # Attempt to enter non-numeric value
    page.add_entry("2027-05", "abc")

    # The HTML number input may reject the text entirely (leaving it blank),
    # or the form may show an error. Either way, no valid entry should be created.
    rows = page.get_entry_rows()
    assert len(rows) == initial_rows, "No new row should be added when kWh is non-numeric"


@pytest.mark.data_management
def test_DM_06_minimum_valid_kwh(logged_in_driver, base_url):
    """Minimum valid value (1 kWh) accepted. Entry saved with 1 kWh."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Get initial row count
    initial_rows = len(page.get_entry_rows())

    # Submit with kWh = 1 (minimum valid)
    page.add_entry("2027-06", 1)

    # Wait for the new row to appear in the table
    from selenium.webdriver.support.ui import WebDriverWait
    WebDriverWait(logged_in_driver, 15).until(
        lambda d: len(page.get_entry_rows()) > initial_rows
    )

    # Verify entry appears in history (no success toast — success = new row)
    rows = page.get_entry_rows()
    assert len(rows) > initial_rows, "Expected a new row for kWh=1"

    # Verify the entry shows 1 kWh
    latest_row_text = page.get_row_text(0)
    assert "1" in latest_row_text, "Expected row to contain kWh value of 1"


@pytest.mark.data_management
def test_DM_07_maximum_valid_kwh(logged_in_driver, base_url):
    """Maximum valid value accepted. Entry saved.
    Note: The frontend input clamps at 99999 (via onChange handler), so
    99999 is the effective max the UI allows."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Get initial row count
    initial_rows = len(page.get_entry_rows())

    # Submit with kWh = 99999 (UI maximum, input clamps higher values)
    page.add_entry("2027-07", 99999)

    # Wait for the new row to appear in the table
    from selenium.webdriver.support.ui import WebDriverWait
    WebDriverWait(logged_in_driver, 15).until(
        lambda d: len(page.get_entry_rows()) > initial_rows
    )

    # Verify entry appears in history
    rows = page.get_entry_rows()
    assert len(rows) > initial_rows, "Expected a new row for kWh=99999"


@pytest.mark.data_management
def test_DM_08_exceeds_maximum_kwh(logged_in_driver, base_url):
    """Value above UI max is clamped by input handler. The frontend input clamps
    at 99999, so entering a higher value results in 99999 being submitted.
    We verify the input was clamped."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Attempt to enter a value exceeding the UI max
    from selenium.webdriver.common.by import By
    kwh_input = page.wait_for_element(page.KWH_INPUT)
    kwh_input.clear()
    kwh_input.send_keys("100001")

    # Wait for the onChange handler to clamp the value
    time.sleep(0.5)

    # Verify the input was clamped to 99999
    actual_value = kwh_input.get_attribute("value")
    assert actual_value == "99999", (
        f"Expected input to be clamped to '99999', got: '{actual_value}'"
    )


@pytest.mark.data_management
def test_DM_09_kwh_with_bill_amount(logged_in_driver, base_url):
    """Optional bill amount saves correctly alongside kWh. Both values appear in history row."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Get initial row count
    initial_rows = len(page.get_entry_rows())

    # Submit with kWh and bill amount
    page.add_entry("2027-09", 320, bill=4500)

    # Wait for the new row to appear in the table
    from selenium.webdriver.support.ui import WebDriverWait
    WebDriverWait(logged_in_driver, 15).until(
        lambda d: len(page.get_entry_rows()) > initial_rows
    )

    # Verify entry appears in history
    rows = page.get_entry_rows()
    assert len(rows) > initial_rows, "Expected a new row for entry with bill amount"

    # Verify both kWh and bill values appear in the row
    latest_row_text = page.get_row_text(0)
    assert "320" in latest_row_text, "Expected row to show kWh value of 320"
    assert "4,500" in latest_row_text or "4500" in latest_row_text, (
        "Expected row to show bill amount of 4500"
    )


@pytest.mark.data_management
def test_DM_10_kwh_with_rate_override(logged_in_driver, base_url):
    """Custom rate override used for calculation. Entry saved with custom rate."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Get initial row count
    initial_rows = len(page.get_entry_rows())

    # Submit with kWh and rate override
    page.add_entry("2027-10", 280, rate=11.50)

    # Wait for the new row to appear in the table
    from selenium.webdriver.support.ui import WebDriverWait
    WebDriverWait(logged_in_driver, 15).until(
        lambda d: len(page.get_entry_rows()) > initial_rows
    )

    # Verify entry appears in history
    rows = page.get_entry_rows()
    assert len(rows) > initial_rows, "Expected a new row for entry with rate override"

    # Verify the entry contains the rate value
    latest_row_text = page.get_row_text(0)
    assert "11.5" in latest_row_text or "11.50" in latest_row_text, (
        "Expected row to show custom rate of 11.50"
    )


@pytest.mark.data_management
def test_DM_11_bill_preview(logged_in_driver, base_url):
    """Estimated bill preview appears as kWh is typed. Shows ₱ currency within 5 seconds."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Type into the kWh field directly without submitting
    kwh_input = page.wait_for_element(page.KWH_INPUT)
    kwh_input.clear()
    kwh_input.send_keys("250")

    # Wait for bill preview to appear (within 5 seconds as per test spec)
    preview_text = page.get_bill_preview(timeout=5)

    # Verify the preview contains the peso sign
    assert "₱" in preview_text, (
        f"Expected bill preview to contain ₱ symbol, got: {preview_text}"
    )


@pytest.mark.data_management
def test_DM_12_duplicate_month(logged_in_driver, base_url):
    """Same month submitted twice is rejected. Error indicates record already exists. No duplicate created."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # First entry — should succeed
    page.add_entry("2027-12", 400)

    # Wait for the row to appear
    from selenium.webdriver.support.ui import WebDriverWait
    WebDriverWait(logged_in_driver, 15).until(
        lambda d: len(page.get_entry_rows()) > 0
    )

    # Verify first entry was created
    rows_after_first = page.get_entry_rows()
    assert len(rows_after_first) >= 1, "Expected first entry to succeed"

    # Count rows after first entry
    entry_count_before = len(rows_after_first)

    # Submit the same month again
    page.add_entry("2027-12", 450)

    # Wait for API response
    time.sleep(2)

    # Verify error message appears (backend returns duplicate error)
    error_msg = page.get_error_message()
    assert error_msg, "Expected an error message for duplicate month"

    # Verify no duplicate row was added
    rows_after_second = len(page.get_entry_rows())
    assert rows_after_second == entry_count_before, (
        "No duplicate row should be created for the same month"
    )
