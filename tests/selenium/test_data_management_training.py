"""
Selenium tests for Data Management — Model Training and Clear Data (DM-36 to DM-40).

This module automates test cases DM-36 through DM-40 from the WATT-IF
Test Plan, covering model training with sufficient/insufficient data,
concurrent training prevention, and the Clear All Data destructive operation.

Requirements covered: 9.1–9.5
"""

from __future__ import annotations

import time

import pytest
from selenium.webdriver.support.ui import WebDriverWait

from tests.selenium.pages.data_entry_page import DataEntryPage
from tests.selenium.pages.forecast_page import ForecastPage


@pytest.mark.data_management
class TestModelTraining:
    """Model Training and Clear Data tests (DM-36 to DM-40)."""

    @pytest.fixture(autouse=True)
    def setup_page(self, logged_in_driver, base_url):
        """Navigate to the Data Entry page before each test."""
        self.driver = logged_in_driver
        self.base_url = base_url
        self.page = DataEntryPage(logged_in_driver, base_url)
        self.page.navigate_to_data_entry()
        # Wait for the page to stabilize
        time.sleep(1)

    def test_DM_36_train_model_success(self, logged_in_driver, test_csv_path):
        """DM-36: Training with ≥14 entries completes successfully.

        Steps:
        1. Ensure ≥14 entries by uploading synthetic_2022_2025.csv (48 rows).
        2. Click Train Model.
        3. Wait up to 60 seconds for training to complete.

        Expected: Status transitions from Idle → Training → Done.
        """
        # Upload the synthetic CSV to get ≥14 entries
        self.page.upload_csv(str(test_csv_path))
        time.sleep(3)  # Allow upload to process

        # Verify initial status is "Idle"
        initial_status = self.page.get_training_status()
        assert "Idle" in initial_status, f"Expected initial status 'Idle', got '{initial_status}'"

        # Click Train Model
        self.page.train_model()

        # Wait briefly and check for "Training" status
        time.sleep(2)
        training_status = self.page.get_training_status()
        # Status should be "Training" or already "Done" if very fast
        assert "Training" in training_status or "Done" in training_status, (
            f"Expected status 'Training' or 'Done' after clicking Train, got '{training_status}'"
        )

        # Wait for training to complete (up to 60 seconds)
        final_status = self.page.wait_for_training_complete(timeout=60)
        assert "Done" in final_status, f"Expected final status 'Done', got '{final_status}'"

    def test_DM_37_train_empty_database(self, logged_in_driver):
        """DM-37: Training on empty database shows error.

        Steps:
        1. Start with no data (fresh test user from logged_in_driver).
        2. Click Train Model.

        Expected: Error message displayed (e.g., "Not enough data."). Status stays Idle.
        """
        # Fresh user has no data — verify empty state
        assert self.page.is_empty_state(), "Expected empty state for fresh user"

        # Click Train Model
        self.page.train_model()

        # Verify error message appears
        error_msg = self.page.get_error_message()
        assert error_msg, "Expected an error message when training with no data"

        # Verify status did not change to "Training"
        status = self.page.get_training_status()
        assert "Training" not in status, (
            f"Status should not be 'Training' with no data, got '{status}'"
        )

    def test_DM_38_train_insufficient_data(self, logged_in_driver):
        """DM-38: Insufficient data (below minimum of 14) rejected.

        Steps:
        1. Manually add fewer than 14 entries (5 entries).
        2. Click Train Model.

        Expected: Error indicates insufficient data. Training doesn't start.
        """
        # Add 5 entries (below the 14-entry minimum)
        for i in range(5):
            month = f"2027-{(i + 1):02d}"
            self.page.add_entry(month, 200 + i * 10)
            time.sleep(1)  # Allow each entry to process

        # Verify entries were added
        time.sleep(1)
        rows = self.page.get_entry_rows()
        assert len(rows) >= 1, "Expected at least one entry to be added"

        # Click Train Model
        self.page.train_model()

        # Verify error message appears
        error_msg = self.page.get_error_message()
        assert error_msg, "Expected an error message when training with <14 entries"

        # Verify status did not change to "Training"
        status = self.page.get_training_status()
        assert "Training" not in status, (
            f"Status should not be 'Training' with insufficient data, got '{status}'"
        )

    def test_DM_39_train_button_disabled_during_training(self, logged_in_driver, test_csv_path):
        """DM-39: Concurrent training prevented — button disabled while training.

        Steps:
        1. Upload CSV to have sufficient data.
        2. Click Train Model.
        3. Immediately check if the Train button is disabled.

        Expected: Button disabled or message "Training in progress."
        """
        # Upload the synthetic CSV to get ≥14 entries
        self.page.upload_csv(str(test_csv_path))
        time.sleep(3)  # Allow upload to process

        # Click Train Model to start training
        self.page.train_model()

        # Immediately check the button state (should be disabled during training)
        time.sleep(0.5)  # Brief pause to let the UI update
        is_enabled = self.page.is_train_button_enabled()
        assert not is_enabled, "Train button should be disabled during training"

        # Wait for training to complete so we don't leave the test in a bad state
        self.page.wait_for_training_complete(timeout=60)

    def test_DM_40_clear_all_data(self, logged_in_driver):
        """DM-40: Clear All removes entries and model.

        Steps:
        1. Add entries to have some data.
        2. Click Clear All Data.
        3. Click confirm (Yes, clear everything).
        4. Verify Entry History is empty.
        5. Navigate to Forecast page and verify "no model" error.

        Expected: History empty. Forecast shows "no model" error.
        """
        # Add a few entries first so we have data to clear
        for i in range(3):
            month = f"2028-{(i + 1):02d}"
            self.page.add_entry(month, 300 + i * 50)
            time.sleep(1)

        # Verify entries exist
        time.sleep(1)
        rows = self.page.get_entry_rows()
        assert len(rows) > 0, "Expected entries to exist before clearing"

        # Click Clear All Data
        self.page.clear_all_data()
        time.sleep(0.5)

        # Confirm the clear action
        self.page.confirm_clear_all()
        time.sleep(2)  # Allow the clear operation to complete

        # Verify Entry History is empty
        assert self.page.is_empty_state(), (
            "Expected empty state after clearing all data"
        )

        # Navigate to Forecast page and verify "no model" error
        forecast_page = ForecastPage(self.driver, self.base_url)
        forecast_page.navigate("/forecast")
        time.sleep(3)  # Allow forecast page API call to complete

        error_msg = forecast_page.get_error_message(timeout=20)
        assert error_msg, "Expected an error message on Forecast page after clearing data"
