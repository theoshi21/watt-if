"""Page object for the Data Entry page (/data-entry)."""

import os

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium.pages.base_page import BasePage


class DataEntryPage(BasePage):
    """Page object encapsulating the Data Entry page locators and interactions.

    Provides methods for all CRUD operations on entries, CSV upload,
    model training, pagination, and clearing all data on the /data-entry route.
    """

    # --- New Reading Form Locators ---
    MONTH_SELECT = (By.CSS_SELECTOR, "select[aria-label='Month']")
    YEAR_SELECT = (By.CSS_SELECTOR, "select[aria-label='Year']")
    KWH_INPUT = (By.ID, "r-kwh")
    KWH_ERROR = (By.ID, "kwh-err")
    BILL_PREVIEW = (By.CSS_SELECTOR, "span")  # Refined in get_bill_preview method
    OPTIONAL_OVERRIDES_TOGGLE = (By.CSS_SELECTOR, "details > summary")
    BILL_OVERRIDE_INPUT = (By.ID, "r-bill")
    RATE_OVERRIDE_INPUT = (By.ID, "r-rate")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit'].btn-primary")
    SUBMIT_ERROR = (By.CSS_SELECTOR, "p[role='alert']")

    # --- Upload Section Locators ---
    CSV_UPLOAD_INPUT = (By.ID, "csv-upload")

    # --- Train Model Section Locators ---
    TRAIN_MODEL_SECTION = (By.CSS_SELECTOR, "section[aria-labelledby='train-model-hd']")
    TRAIN_BUTTON = (By.CSS_SELECTOR, "section[aria-labelledby='train-model-hd'] button.btn-primary")
    TRAINING_STATUS = (By.CSS_SELECTOR, "section[aria-labelledby='train-model-hd'] strong")

    # --- Entry History Section Locators ---
    HISTORY_SECTION = (By.CSS_SELECTOR, "section[aria-labelledby='history-hd']")
    HISTORY_HEADING = (By.ID, "history-hd")
    ENTRY_COUNT_SPAN = (By.CSS_SELECTOR, "h2#history-hd span")
    EMPTY_STATE = (By.XPATH, "//section[@aria-labelledby='history-hd']//p[contains(text(),'No entries recorded yet')]")
    HISTORY_ROWS = (By.CSS_SELECTOR, "section[aria-labelledby='history-hd'] tbody tr")

    # --- Delete Confirmation Dialog Locators ---
    DELETE_DIALOG = (By.CSS_SELECTOR, "div[role='alertdialog']")
    DELETE_CONFIRM_BUTTON = (By.CSS_SELECTOR, "div[role='alertdialog'] button.btn-danger")
    DELETE_CANCEL_BUTTON = (By.CSS_SELECTOR, "div[role='alertdialog'] button.btn-secondary")

    # --- Pagination Locators ---
    FIRST_PAGE_BUTTON = (By.CSS_SELECTOR, "button[aria-label='First page']")
    PREV_PAGE_BUTTON = (By.CSS_SELECTOR, "button[aria-label='Previous page']")
    NEXT_PAGE_BUTTON = (By.CSS_SELECTOR, "button[aria-label='Next page']")
    LAST_PAGE_BUTTON = (By.CSS_SELECTOR, "button[aria-label='Last page']")
    PAGE_INFO_SPAN = (By.XPATH, "//span[contains(text(),'Page')]")

    # --- Danger Zone Locators ---
    DANGER_ZONE_SECTION = (By.CSS_SELECTOR, "section[aria-labelledby='danger-zone-hd']")
    CLEAR_ALL_BUTTON = (By.CSS_SELECTOR, "section[aria-labelledby='danger-zone-hd'] button.btn-danger")

    # --- Success Message Locator ---
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".toast--success, [role='status'], .success-message")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        """Initialize DataEntryPage.

        Args:
            driver: Selenium WebDriver instance.
            base_url: Base URL of the application.
        """
        super().__init__(driver, base_url)

    def navigate_to_data_entry(self) -> None:
        """Navigate to the Data Entry page and wait for it to load."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        self.navigate("/data-entry")
        # Poll until the page content is visible (form or history section)
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(self.HISTORY_SECTION)
        )

    def add_entry(
        self,
        month: str,
        kwh: str | int | float,
        bill: str | int | float | None = None,
        rate: str | int | float | None = None,
    ) -> None:
        """Add a new reading entry with the specified month and kWh value.

        The month parameter should be in "YYYY-MM" format (e.g., "2024-03").
        This method splits it into year and month selections for the two
        separate dropdown controls.

        Args:
            month: Month in "YYYY-MM" format (e.g., "2024-03").
            kwh: The kWh consumption value to enter.
            bill: Optional bill override amount.
            rate: Optional rate override value.
        """
        # Parse year and month from YYYY-MM format
        parts = month.split("-")
        year_value = parts[0]
        month_value = parts[1] if len(parts) > 1 else "01"

        # Select month from dropdown
        month_select_el = self.wait_for_element(self.MONTH_SELECT)
        Select(month_select_el).select_by_value(month_value)

        # Select year from dropdown
        year_select_el = self.wait_for_element(self.YEAR_SELECT)
        Select(year_select_el).select_by_value(year_value)

        # Enter kWh value
        kwh_input = self.wait_for_element(self.KWH_INPUT)
        kwh_input.clear()
        kwh_input.send_keys(str(kwh))

        # Handle optional overrides
        if bill is not None or rate is not None:
            self._open_optional_overrides()

            if bill is not None:
                bill_input = self.wait_for_element(self.BILL_OVERRIDE_INPUT)
                bill_input.clear()
                bill_input.send_keys(str(bill))

            if rate is not None:
                rate_input = self.wait_for_element(self.RATE_OVERRIDE_INPUT)
                rate_input.clear()
                rate_input.send_keys(str(rate))

        # Click submit
        submit_btn = self.wait_for_clickable(self.SUBMIT_BUTTON)
        submit_btn.click()

    def _open_optional_overrides(self) -> None:
        """Open the optional overrides section if not already open."""
        details_el = self.driver.find_element(By.CSS_SELECTOR, "details")
        is_open = details_el.get_attribute("open")
        if is_open is None:
            summary = self.wait_for_clickable(self.OPTIONAL_OVERRIDES_TOGGLE)
            summary.click()

    def get_entry_rows(self) -> list[WebElement]:
        """Get all visible entry rows in the Entry History table.

        Returns:
            A list of WebElements representing table rows in the history.
        """
        return self.find_elements(self.HISTORY_ROWS)

    def get_entry_count(self) -> str:
        """Get the entry count text from the history heading.

        Returns:
            The entry count text (e.g., "(48 entries)").
        """
        count_span = self.wait_for_element(self.ENTRY_COUNT_SPAN)
        return count_span.text

    def edit_entry(self, row_idx: int, kwh: str | int | float) -> None:
        """Edit an entry at the given row index with a new kWh value.

        Clicks the Edit button on the specified row, clears and types
        the new kWh value, then clicks Save.

        Args:
            row_idx: Zero-based index of the row to edit.
            kwh: The new kWh value to enter.
        """
        rows = self.get_entry_rows()
        if row_idx >= len(rows):
            raise IndexError(f"Row index {row_idx} out of range (only {len(rows)} rows)")

        row = rows[row_idx]

        # Click the Edit button for this row
        edit_btn = row.find_element(By.CSS_SELECTOR, "button[aria-label^='Edit']")
        edit_btn.click()

        # Wait for edit mode: find the number input in the row
        wait = WebDriverWait(self.driver, 10)
        kwh_edit_input = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "section[aria-labelledby='history-hd'] tbody tr input[type='number']")
            )
        )
        kwh_edit_input.clear()
        kwh_edit_input.send_keys(str(kwh))

        # Click the Save button in the row
        # Re-fetch rows since DOM may have updated
        rows = self.get_entry_rows()
        row = rows[row_idx]
        save_btn = row.find_element(By.CSS_SELECTOR, "button.btn-primary")
        save_btn.click()

    def cancel_edit(self, row_idx: int) -> None:
        """Cancel an in-progress edit on the specified row.

        Args:
            row_idx: Zero-based index of the row being edited.
        """
        rows = self.get_entry_rows()
        if row_idx >= len(rows):
            raise IndexError(f"Row index {row_idx} out of range (only {len(rows)} rows)")

        row = rows[row_idx]
        cancel_btn = row.find_element(By.XPATH, ".//button[text()='Cancel']")
        cancel_btn.click()

    def click_edit_button(self, row_idx: int) -> None:
        """Click the Edit button on a specific row without modifying anything.

        Args:
            row_idx: Zero-based index of the row to put in edit mode.
        """
        rows = self.get_entry_rows()
        if row_idx >= len(rows):
            raise IndexError(f"Row index {row_idx} out of range (only {len(rows)} rows)")

        row = rows[row_idx]
        edit_btn = row.find_element(By.CSS_SELECTOR, "button[aria-label^='Edit']")
        edit_btn.click()

    def delete_entry(self, row_idx: int) -> None:
        """Click the Delete button on the specified row.

        This triggers the delete confirmation dialog. Call confirm_dialog()
        or cancel_dialog() after this to complete or cancel the deletion.

        Args:
            row_idx: Zero-based index of the row to delete.
        """
        rows = self.get_entry_rows()
        if row_idx >= len(rows):
            raise IndexError(f"Row index {row_idx} out of range (only {len(rows)} rows)")

        row = rows[row_idx]
        delete_btn = row.find_element(By.CSS_SELECTOR, "button[aria-label^='Delete']")
        delete_btn.click()

    def confirm_dialog(self) -> None:
        """Confirm the delete action in the alertdialog overlay.

        Waits for the dialog to appear, then clicks "Yes, delete".
        """
        confirm_btn = self.wait_for_clickable(self.DELETE_CONFIRM_BUTTON)
        confirm_btn.click()

    def cancel_dialog(self) -> None:
        """Cancel the delete action in the alertdialog overlay.

        Waits for the dialog to appear, then clicks "Cancel".
        """
        cancel_btn = self.wait_for_clickable(self.DELETE_CANCEL_BUTTON)
        cancel_btn.click()

    def is_delete_dialog_visible(self) -> bool:
        """Check if the delete confirmation dialog is currently visible.

        Returns:
            True if the alertdialog is visible, False otherwise.
        """
        dialogs = self.find_elements(self.DELETE_DIALOG)
        return len(dialogs) > 0 and dialogs[0].is_displayed()

    def upload_csv(self, path: str) -> None:
        """Upload a CSV file using the file input.

        Args:
            path: Absolute path to the CSV file to upload.
        """
        file_input = self.driver.find_element(*self.CSV_UPLOAD_INPUT)
        file_input.send_keys(os.path.abspath(path))

    def train_model(self) -> None:
        """Click the Train Model button to start model training."""
        train_btn = self.wait_for_clickable(self.TRAIN_BUTTON)
        train_btn.click()

    def get_training_status(self) -> str:
        """Get the current training status text.

        Returns:
            The training status text (e.g., "Idle", "Training…", or "Done").
        """
        status_el = self.wait_for_element(self.TRAINING_STATUS)
        return status_el.text

    def wait_for_training_complete(self, timeout: int = 60) -> str:
        """Wait for training to complete (status changes to "Done").

        Args:
            timeout: Maximum seconds to wait for training completion.

        Returns:
            The final training status text.

        Raises:
            TimeoutException: If training does not complete within the timeout.
        """
        wait = WebDriverWait(self.driver, timeout)
        wait.until(
            lambda d: "Done" in d.find_element(*self.TRAINING_STATUS).text
        )
        return self.get_training_status()

    def is_train_button_enabled(self) -> bool:
        """Check whether the Train Model button is currently enabled.

        Returns:
            True if the button is enabled, False if disabled.
        """
        train_btn = self.wait_for_element(self.TRAIN_BUTTON)
        return train_btn.is_enabled()

    def clear_all_data(self) -> None:
        """Click the Clear All Data button in the Danger Zone section.

        After clicking, the confirmation panel appears. The caller must
        handle the confirmation step separately.
        """
        clear_btn = self.wait_for_clickable(self.CLEAR_ALL_BUTTON)
        clear_btn.click()

    def confirm_clear_all(self) -> None:
        """Confirm the Clear All Data action.

        Looks for a confirm button within the danger zone section
        after the Clear All button has been clicked.
        """
        # After clicking Clear All, a confirmation panel appears with
        # "Yes, clear everything" as the confirm button text.
        confirm_btn = self.wait_for_clickable(
            (By.XPATH, "//section[@aria-labelledby='danger-zone-hd']//button[contains(text(),'Yes')]")
        )
        confirm_btn.click()

    def cancel_clear_all(self) -> None:
        """Cancel the Clear All Data action.

        Clicks the Cancel button in the danger zone confirmation panel.
        """
        cancel_btn = self.wait_for_clickable(
            (By.XPATH, "//section[@aria-labelledby='danger-zone-hd']//button[text()='Cancel']")
        )
        cancel_btn.click()

    def get_pagination_controls(self) -> dict[str, bool]:
        """Get the state of pagination controls.

        Returns:
            A dictionary with keys 'first', 'prev', 'next', 'last' indicating
            whether each pagination button exists and is enabled.
        """
        controls = {}
        for name, locator in [
            ("first", self.FIRST_PAGE_BUTTON),
            ("prev", self.PREV_PAGE_BUTTON),
            ("next", self.NEXT_PAGE_BUTTON),
            ("last", self.LAST_PAGE_BUTTON),
        ]:
            elements = self.find_elements(locator)
            if elements:
                controls[name] = elements[0].is_enabled()
            else:
                controls[name] = False
        return controls

    def has_pagination(self) -> bool:
        """Check if pagination controls are present on the page.

        Returns:
            True if any pagination buttons exist, False otherwise.
        """
        controls = self.get_pagination_controls()
        return any(controls.values()) or any(
            len(self.find_elements(loc)) > 0
            for loc in [self.FIRST_PAGE_BUTTON, self.NEXT_PAGE_BUTTON]
        )

    def click_next_page(self) -> None:
        """Click the Next Page (›) pagination button."""
        next_btn = self.wait_for_clickable(self.NEXT_PAGE_BUTTON)
        next_btn.click()

    def click_prev_page(self) -> None:
        """Click the Previous Page (‹) pagination button."""
        prev_btn = self.wait_for_clickable(self.PREV_PAGE_BUTTON)
        prev_btn.click()

    def click_first_page(self) -> None:
        """Click the First Page («) pagination button."""
        first_btn = self.wait_for_clickable(self.FIRST_PAGE_BUTTON)
        first_btn.click()

    def click_last_page(self) -> None:
        """Click the Last Page (») pagination button."""
        last_btn = self.wait_for_clickable(self.LAST_PAGE_BUTTON)
        last_btn.click()

    def get_page_info(self) -> str:
        """Get the page info text (e.g., "Page 1 of 5 · 48 entries").

        Returns:
            The pagination info text.
        """
        info_span = self.wait_for_element(self.PAGE_INFO_SPAN)
        return info_span.text

    def get_success_message(self, timeout: int = 10) -> str:
        """Wait for and return the success message text.

        Args:
            timeout: Maximum seconds to wait for the success message.

        Returns:
            The success message text.

        Raises:
            TimeoutException: If no success message appears within the timeout.
        """
        wait = WebDriverWait(self.driver, timeout)
        success_el = wait.until(EC.visibility_of_element_located(self.SUCCESS_MESSAGE))
        return success_el.text

    def get_error_message(self, timeout: int = 10) -> str:
        """Wait for and return the error message text.

        Looks for error messages from various sources: kWh validation error,
        form submission error, or upload error.

        Args:
            timeout: Maximum seconds to wait for the error message.

        Returns:
            The error message text.

        Raises:
            TimeoutException: If no error message appears within the timeout.
        """
        wait = WebDriverWait(self.driver, timeout)
        # Check for kWh error first, then form-level alert
        error_el = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "#kwh-err[role='alert'], p[role='alert'], [role='alert']")
            )
        )
        return error_el.text

    def get_bill_preview(self, timeout: int = 5) -> str:
        """Wait for and return the bill preview text.

        The bill preview appears as a span containing "Est. bill:" and a
        currency value when a valid kWh is entered.

        Args:
            timeout: Maximum seconds to wait for the bill preview.

        Returns:
            The bill preview text (e.g., "Est. bill: ₱1,234.56").

        Raises:
            TimeoutException: If no bill preview appears within the timeout.
        """
        wait = WebDriverWait(self.driver, timeout)
        preview_el = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//span[contains(text(),'Est. bill')]")
            )
        )
        return preview_el.text

    def is_empty_state(self) -> bool:
        """Check if the Entry History section shows the empty state message.

        Returns:
            True if "No entries recorded yet." is displayed, False otherwise.
        """
        empty_elements = self.find_elements(self.EMPTY_STATE)
        return len(empty_elements) > 0 and empty_elements[0].is_displayed()

    def get_kwh_error(self) -> str:
        """Get the kWh field validation error text.

        Returns:
            The kWh error text from the span#kwh-err element.

        Raises:
            TimeoutException: If no kWh error appears within the timeout.
        """
        error_el = self.wait_for_element(self.KWH_ERROR)
        return error_el.text

    def is_submit_enabled(self) -> bool:
        """Check whether the Submit button is currently enabled.

        Returns:
            True if the submit button is enabled, False if disabled.
        """
        submit_btn = self.wait_for_element(self.SUBMIT_BUTTON)
        return submit_btn.is_enabled()

    def get_row_text(self, row_idx: int) -> str:
        """Get the full text content of a specific history table row.

        Args:
            row_idx: Zero-based index of the row.

        Returns:
            The text content of the row element.
        """
        rows = self.get_entry_rows()
        if row_idx >= len(rows):
            raise IndexError(f"Row index {row_idx} out of range (only {len(rows)} rows)")
        return rows[row_idx].text

    def is_row_in_edit_mode(self, row_idx: int) -> bool:
        """Check if a specific row is currently in edit mode.

        A row in edit mode contains an input[type='number'] element.

        Args:
            row_idx: Zero-based index of the row to check.

        Returns:
            True if the row contains edit inputs, False otherwise.
        """
        rows = self.get_entry_rows()
        if row_idx >= len(rows):
            raise IndexError(f"Row index {row_idx} out of range (only {len(rows)} rows)")
        row = rows[row_idx]
        inputs = row.find_elements(By.CSS_SELECTOR, "input[type='number']")
        return len(inputs) > 0
