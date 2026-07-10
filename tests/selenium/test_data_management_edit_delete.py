"""
Data Management test module — Edit and Delete (DM-22 to DM-31).

Covers editing entries (valid/invalid edits, cancel, single edit mode)
and deleting entries (confirmation dialog, confirmed/cancelled deletion,
delete last entry empty state) in the Entry History table.

Requirements: 7.1–7.10
"""

import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium.pages import DataEntryPage


# ---------------------------------------------------------------------------
# Edit Tests (DM-22 through DM-27)
# ---------------------------------------------------------------------------


@pytest.mark.data_management
def test_DM_22_edit_mode_display(logged_in_driver, base_url):
    """Click Edit on a row → editable input fields for kWh and bill amount displayed, along with Save and Cancel buttons."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Create an entry to edit
    page.add_entry("2027-01", 300)
    time.sleep(2)  # Wait for entry to be created via API

    # Click Edit on the first row
    page.click_edit_button(0)

    # Verify row is in edit mode (has input fields)
    assert page.is_row_in_edit_mode(0), "Expected row 0 to be in edit mode with input fields"

    # Verify Save and Cancel buttons are visible in the row
    rows = page.get_entry_rows()
    row = rows[0]
    save_buttons = row.find_elements(By.CSS_SELECTOR, "button.btn-primary")
    cancel_buttons = row.find_elements(By.XPATH, ".//button[text()='Cancel']")
    assert len(save_buttons) > 0, "Expected Save button to be visible in edit mode"
    assert len(cancel_buttons) > 0, "Expected Cancel button to be visible in edit mode"


@pytest.mark.data_management
def test_DM_23_edit_valid_kwh(logged_in_driver, base_url):
    """Enter 500 kWh in edit field and Save → row exits edit mode and displays updated value of 500."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Create an entry to edit
    page.add_entry("2027-02", 300)
    time.sleep(2)  # Wait for entry to be created via API

    # Edit the entry with a new valid kWh value
    page.edit_entry(0, 500)

    # Wait for edit mode to exit
    time.sleep(1)

    # Verify the row shows the updated value
    row_text = page.get_row_text(0)
    assert "500" in row_text, f"Expected row to show updated kWh of 500, got: {row_text}"

    # Verify row is no longer in edit mode
    assert not page.is_row_in_edit_mode(0), "Expected row to exit edit mode after Save"


@pytest.mark.data_management
def test_DM_24_edit_invalid_zero(logged_in_driver, base_url):
    """Enter 0 in edit field and Save → error message shown, original value preserved."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Create an entry to edit
    page.add_entry("2027-03", 350)
    time.sleep(2)  # Wait for entry to be created via API

    # Get original row text
    original_row_text = page.get_row_text(0)

    # Attempt to edit with invalid value (0)
    page.edit_entry(0, 0)

    # Verify error message appears
    error_msg = page.get_error_message()
    assert error_msg, "Expected an error message when editing kWh to 0"

    # Wait for state to settle
    time.sleep(1)

    # Cancel the edit to restore the row or verify original is preserved
    # After error, the row may still be in edit mode — check original value is preserved
    # Try to cancel if still in edit mode
    if page.is_row_in_edit_mode(0):
        page.cancel_edit(0)
        time.sleep(0.5)

    # Verify original value is preserved
    row_text = page.get_row_text(0)
    assert "350" in row_text, f"Expected original kWh of 350 to be preserved, got: {row_text}"


@pytest.mark.data_management
def test_DM_25_edit_exceeds_max(logged_in_driver, base_url):
    """Enter 1000001 in edit field and Save → error message shown, original value preserved."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Create an entry to edit
    page.add_entry("2027-04", 400)
    time.sleep(2)  # Wait for entry to be created via API

    # Get original row text
    original_row_text = page.get_row_text(0)

    # Attempt to edit with value exceeding maximum
    page.edit_entry(0, 1000001)

    # Verify error message appears
    error_msg = page.get_error_message()
    assert error_msg, "Expected an error message when editing kWh to 1000001"

    # Wait for state to settle
    time.sleep(1)

    # Cancel the edit if still in edit mode
    if page.is_row_in_edit_mode(0):
        page.cancel_edit(0)
        time.sleep(0.5)

    # Verify original value is preserved
    row_text = page.get_row_text(0)
    assert "400" in row_text, f"Expected original kWh of 400 to be preserved, got: {row_text}"


@pytest.mark.data_management
def test_DM_26_edit_cancel(logged_in_driver, base_url):
    """Click Cancel during active edit → row exits edit mode and original kWh value unchanged."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Create an entry to edit
    page.add_entry("2027-05", 275)
    time.sleep(2)  # Wait for entry to be created via API

    # Get original row text
    original_row_text = page.get_row_text(0)

    # Enter edit mode
    page.click_edit_button(0)
    assert page.is_row_in_edit_mode(0), "Expected row to be in edit mode"

    # Click Cancel
    page.cancel_edit(0)

    # Wait for edit mode to exit
    time.sleep(0.5)

    # Verify row is no longer in edit mode
    assert not page.is_row_in_edit_mode(0), "Expected row to exit edit mode after Cancel"

    # Verify original value unchanged
    row_text = page.get_row_text(0)
    assert "275" in row_text, f"Expected original kWh of 275 to be preserved after Cancel, got: {row_text}"


@pytest.mark.data_management
def test_DM_27_single_edit_mode(logged_in_driver, base_url):
    """Edit second row while first is in edit mode → only second row is editable (single edit at a time)."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Create two entries
    page.add_entry("2027-06", 200)
    time.sleep(2)  # Wait for entry to be created via API

    page.add_entry("2027-07", 250)
    time.sleep(2)  # Wait for entry to be created via API

    # Click Edit on the first row (row 0)
    page.click_edit_button(0)
    assert page.is_row_in_edit_mode(0), "Expected first row to be in edit mode"

    # Click Edit on the second row (row 1)
    page.click_edit_button(1)

    # Wait for UI to update
    time.sleep(0.5)

    # Verify only the second row is in edit mode
    assert page.is_row_in_edit_mode(1), "Expected second row to be in edit mode"
    assert not page.is_row_in_edit_mode(0), "Expected first row to exit edit mode when second is edited"


# ---------------------------------------------------------------------------
# Delete Tests (DM-28 through DM-31)
# ---------------------------------------------------------------------------


@pytest.mark.data_management
def test_DM_28_delete_confirmation(logged_in_driver, base_url):
    """Click Delete on a row → confirmation dialog appears before any deletion occurs."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Create an entry to delete
    page.add_entry("2027-08", 310)
    time.sleep(2)  # Wait for entry to be created via API

    # Click Delete button on the first row
    page.delete_entry(0)

    # Verify confirmation dialog is visible
    assert page.is_delete_dialog_visible(), "Expected delete confirmation dialog to appear"

    # Cancel the dialog to clean up state
    page.cancel_dialog()


@pytest.mark.data_management
def test_DM_29_delete_confirmed(logged_in_driver, base_url):
    """Accept delete confirmation → row removed from Entry History and total entry count decreases by 1."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Create an entry to delete
    page.add_entry("2027-09", 420)
    time.sleep(2)  # Wait for entry to be created via API

    # Get row count before deletion
    rows_before = len(page.get_entry_rows())
    assert rows_before >= 1, "Expected at least 1 row before deletion"

    # Delete the first row
    page.delete_entry(0)

    # Confirm the deletion
    page.confirm_dialog()

    # Wait for deletion to complete
    time.sleep(1)

    # Verify the row count has decreased
    rows_after = len(page.get_entry_rows())
    assert rows_after == rows_before - 1, (
        f"Expected row count to decrease by 1 (before: {rows_before}, after: {rows_after})"
    )


@pytest.mark.data_management
def test_DM_30_delete_cancelled(logged_in_driver, base_url):
    """Cancel delete confirmation → row remains in Entry History and entry count is unchanged."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Create an entry
    page.add_entry("2027-10", 380)
    time.sleep(2)  # Wait for entry to be created via API

    # Get row count before attempted deletion
    rows_before = len(page.get_entry_rows())

    # Click Delete
    page.delete_entry(0)

    # Verify dialog appears
    assert page.is_delete_dialog_visible(), "Expected delete confirmation dialog"

    # Cancel the deletion
    page.cancel_dialog()

    # Wait for dialog to close
    time.sleep(0.5)

    # Verify row count is unchanged
    rows_after = len(page.get_entry_rows())
    assert rows_after == rows_before, (
        f"Expected row count to remain unchanged after cancel (before: {rows_before}, after: {rows_after})"
    )


@pytest.mark.data_management
def test_DM_31_delete_last_entry(logged_in_driver, base_url):
    """Delete the only entry and confirm → Entry History displays empty state message and no rows shown."""
    page = DataEntryPage(logged_in_driver, base_url)
    page.navigate_to_data_entry()

    # Create a single entry (this is a fresh test user so history should be empty)
    page.add_entry("2027-11", 260)
    time.sleep(2)  # Wait for entry to be created via API

    # Verify we have exactly 1 row
    rows = page.get_entry_rows()
    assert len(rows) == 1, f"Expected exactly 1 entry, got {len(rows)}"

    # Delete the only entry
    page.delete_entry(0)
    page.confirm_dialog()

    # Wait for deletion to complete
    time.sleep(1)

    # Verify empty state message is shown
    assert page.is_empty_state(), "Expected empty state message after deleting the last entry"

    # Verify no rows in history
    rows_after = page.get_entry_rows()
    assert len(rows_after) == 0, f"Expected 0 rows after deleting last entry, got {len(rows_after)}"
