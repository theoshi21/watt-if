"""Page object for the Account Settings page (/account)."""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium.pages.base_page import BasePage


class AccountSettingsPage(BasePage):
    """Page object encapsulating the Account Settings page locators and interactions.

    Provides methods for password change, customer type selection,
    forecast horizon, rate override, chat preferences, data & privacy
    actions, notification thresholds, model retraining settings, and logout
    on the /account route.
    """

    # --- Global Feedback Locators ---
    SETTINGS_SUCCESS = (By.CSS_SELECTOR, "div[role='status']")
    SETTINGS_ERROR = (By.CSS_SELECTOR, "p[role='alert']")

    # --- Password Change Section Locators ---
    PASSWORD_SECTION = (By.CSS_SELECTOR, "section[aria-labelledby='password-change-hd']")
    CURRENT_PASSWORD_INPUT = (By.ID, "current-password")
    NEW_PASSWORD_INPUT = (By.ID, "new-password")
    CONFIRM_PASSWORD_INPUT = (By.ID, "confirm-password")
    NEW_PASSWORD_ERROR = (By.ID, "new-pw-err")
    CONFIRM_PASSWORD_ERROR = (By.ID, "confirm-pw-err")
    PASSWORD_API_ERROR = (
        By.CSS_SELECTOR,
        "section[aria-labelledby='password-change-hd'] p[role='alert']",
    )
    PASSWORD_SUCCESS = (
        By.CSS_SELECTOR,
        "section[aria-labelledby='password-change-hd'] div[role='status']",
    )
    PASSWORD_SUBMIT_BUTTON = (
        By.CSS_SELECTOR,
        "section[aria-labelledby='password-change-hd'] button[type='submit'].btn-primary",
    )

    # --- Customer Type Section Locators ---
    CUSTOMER_TYPE_SELECT = (By.ID, "customer-type-select")

    # --- Forecast Horizon Section Locators ---
    HORIZON_SELECT = (By.ID, "horizon-select")

    # --- Rate Override Section Locators ---
    RATE_OVERRIDE_INPUT = (By.ID, "rate-override-input")
    RATE_OVERRIDE_CLEAR_BUTTON = (
        By.CSS_SELECTOR,
        "section[aria-labelledby='rate-override-hd'] button.btn-secondary",
    )

    # --- Chat Preferences Section Locators ---
    CHAT_MAX_HISTORY_INPUT = (By.ID, "chat-max-history")
    AUTO_CLEAR_TOGGLE = (
        By.CSS_SELECTOR,
        "section[aria-labelledby='chat-prefs-hd'] label.toggle",
    )

    # --- Data & Privacy Section Locators ---
    CLEAR_CHAT_BUTTON = (
        By.XPATH,
        "//section[@aria-labelledby='data-privacy-hd']//button[contains(text(),'Clear Chat History')]",
    )
    CLEAR_CHAT_CONFIRM_BUTTON = (
        By.XPATH,
        "//section[@aria-labelledby='data-privacy-hd']//button[contains(text(),'Yes, clear')]",
    )
    CLEAR_ALL_DATA_BUTTON = (
        By.XPATH,
        "//section[@aria-labelledby='data-privacy-hd']//button[contains(text(),'Clear All Data')]",
    )
    CLEAR_ALL_CONFIRM_BUTTON = (
        By.XPATH,
        "//section[@aria-labelledby='data-privacy-hd']//button[contains(text(),'Yes, delete all')]",
    )

    # --- Notification Thresholds Section Locators ---
    NOTIFY_KWH_BUDGET_INPUT = (By.ID, "notify-kwh-budget")
    NOTIFY_BILL_CEILING_INPUT = (By.ID, "notify-bill-ceiling")
    NOTIFY_HIGH_CONSUMPTION_INPUT = (By.ID, "notify-high-consumption")

    # --- Model Retraining Section Locators ---
    AUTO_RETRAIN_TOGGLE = (
        By.CSS_SELECTOR,
        "section[aria-labelledby='retrain-hd'] label.toggle",
    )
    MIN_DATAPOINTS_INPUT = (By.ID, "min-datapoints")

    # --- Logout Section Locators ---
    LOGOUT_BUTTON = (
        By.XPATH,
        "//section[@aria-labelledby='logout-hd']//button[contains(text(),'Logout')]",
    )
    LOGOUT_CONFIRM_BUTTON = (
        By.XPATH,
        "//section[@aria-labelledby='logout-hd']//button[contains(text(),'Yes, log out')]",
    )

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        """Initialize AccountSettingsPage.

        Args:
            driver: Selenium WebDriver instance.
            base_url: Base URL of the application.
        """
        super().__init__(driver, base_url)

    def navigate_to_settings(self) -> None:
        """Navigate to the Account Settings page."""
        self.navigate("/account")

    # --- Password Change Methods ---

    def change_password(self, current: str, new: str, confirm: str) -> None:
        """Fill the password change form, submit, then confirm the dialog.

        Args:
            current: The current password.
            new: The new password.
            confirm: The confirmation of the new password.
        """
        current_input = self.wait_for_element(self.CURRENT_PASSWORD_INPUT)
        current_input.clear()
        current_input.send_keys(current)

        new_input = self.wait_for_element(self.NEW_PASSWORD_INPUT)
        new_input.clear()
        new_input.send_keys(new)

        confirm_input = self.wait_for_element(self.CONFIRM_PASSWORD_INPUT)
        confirm_input.clear()
        confirm_input.send_keys(confirm)

        # First click — triggers the "Confirm password change?" dialog
        submit_btn = self.wait_for_clickable(self.PASSWORD_SUBMIT_BUTTON)
        submit_btn.click()

        # Click "Yes, update" in the confirmation dialog
        yes_btn = self.wait_for_clickable(
            (By.XPATH, "//button[contains(text(),'Yes, update')]")
        )
        yes_btn.click()

    # --- Feedback Methods ---

    def get_success_message(self, timeout: int = 10) -> str:
        """Wait for and return the visible success status text.

        Checks both the global settings success banner and the password
        section success message.

        Args:
            timeout: Maximum seconds to wait for the success message.

        Returns:
            The success message text.

        Raises:
            TimeoutException: If no success message appears within the timeout.
        """
        wait = WebDriverWait(self.driver, timeout)
        success_el = wait.until(
            EC.visibility_of_element_located(self.SETTINGS_SUCCESS)
        )
        return success_el.text

    def get_error_message(self, timeout: int = 10) -> str:
        """Wait for and return the visible error message text.

        Checks for any visible role='alert' element on the page including
        password API errors, field validation errors, and settings errors.

        Args:
            timeout: Maximum seconds to wait for the error message.

        Returns:
            The error message text.

        Raises:
            TimeoutException: If no error message appears within the timeout.
        """
        wait = WebDriverWait(self.driver, timeout)
        error_el = wait.until(
            EC.visibility_of_element_located(self.SETTINGS_ERROR)
        )
        return error_el.text

    # --- Customer Type Methods ---

    def set_customer_type(self, type_key: str) -> None:
        """Select a customer type from the dropdown.

        Triggers an immediate save on change.

        Args:
            type_key: The customer type value to select
                      (e.g., "Residential", "General Service A", "General Service B").
        """
        select_el = self.wait_for_element(self.CUSTOMER_TYPE_SELECT)
        Select(select_el).select_by_value(type_key)

    # --- Forecast Horizon Methods ---

    def set_forecast_horizon(self, h: int | str) -> None:
        """Select a forecast horizon value from the dropdown.

        Args:
            h: The horizon value to select (1, 3, 6, 9, or 12).
        """
        select_el = self.wait_for_element(self.HORIZON_SELECT)
        Select(select_el).select_by_value(str(h))

    # --- Rate Override Methods ---

    def set_rate_override(self, value: str | int | float) -> None:
        """Enter a rate override value and trigger blur to save.

        Args:
            value: The rate override value to enter (e.g., 11.80).
        """
        rate_input = self.wait_for_element(self.RATE_OVERRIDE_INPUT)
        rate_input.clear()
        rate_input.send_keys(str(value))
        rate_input.send_keys(Keys.TAB)

    def clear_rate_override(self) -> None:
        """Clear the rate override input field and trigger save."""
        from selenium.webdriver.common.keys import Keys
        input_el = self.wait_for_element(self.RATE_OVERRIDE_INPUT)
        input_el.clear()
        input_el.send_keys(Keys.TAB)

    # --- Chat Preferences Methods ---

    def set_chat_max_history(self, value: int | str) -> None:
        """Enter a max chat history value and trigger blur to save.

        Args:
            value: The max messages value to enter (10–500).
        """
        input_el = self.wait_for_element(self.CHAT_MAX_HISTORY_INPUT)
        input_el.clear()
        input_el.send_keys(str(value))
        input_el.send_keys(Keys.TAB)

    def toggle_auto_clear(self) -> None:
        """Toggle the auto-clear chat on logout checkbox via its label."""
        label = self.wait_for_clickable(self.AUTO_CLEAR_TOGGLE)
        label.click()

    # --- Data & Privacy Methods ---

    def clear_chat_history(self) -> None:
        """Click Clear Chat History and confirm the action."""
        clear_btn = self.wait_for_clickable(self.CLEAR_CHAT_BUTTON)
        clear_btn.click()
        confirm_btn = self.wait_for_clickable(self.CLEAR_CHAT_CONFIRM_BUTTON)
        confirm_btn.click()

    def clear_all_data(self) -> None:
        """Click Clear All Data & Model and confirm the action."""
        clear_btn = self.wait_for_clickable(self.CLEAR_ALL_DATA_BUTTON)
        clear_btn.click()
        confirm_btn = self.wait_for_clickable(self.CLEAR_ALL_CONFIRM_BUTTON)
        confirm_btn.click()

    # --- Notification Threshold Methods ---

    def set_notification_thresholds(
        self,
        kwh: int | str | None = None,
        bill: int | str | None = None,
        high: int | str | None = None,
    ) -> None:
        """Fill all three notification threshold inputs and trigger blur to save.

        Args:
            kwh: Monthly kWh budget threshold (or None to skip).
            bill: Bill ceiling threshold in ₱ (or None to skip).
            high: High consumption warning threshold in kWh (or None to skip).
        """
        if kwh is not None:
            kwh_input = self.wait_for_element(self.NOTIFY_KWH_BUDGET_INPUT)
            kwh_input.clear()
            kwh_input.send_keys(str(kwh))
            kwh_input.send_keys(Keys.TAB)

        if bill is not None:
            bill_input = self.wait_for_element(self.NOTIFY_BILL_CEILING_INPUT)
            bill_input.clear()
            bill_input.send_keys(str(bill))
            bill_input.send_keys(Keys.TAB)

        if high is not None:
            high_input = self.wait_for_element(self.NOTIFY_HIGH_CONSUMPTION_INPUT)
            high_input.clear()
            high_input.send_keys(str(high))
            high_input.send_keys(Keys.TAB)

    # --- Model Retraining Methods ---

    def toggle_auto_retrain(self) -> None:
        """Toggle the auto-retrain on CSV upload checkbox via its label."""
        label = self.wait_for_clickable(self.AUTO_RETRAIN_TOGGLE)
        label.click()

    def set_min_data_points(self, value: int | str) -> None:
        """Enter a minimum data points value and trigger blur to save.

        Args:
            value: The minimum data points value to enter (3–60).
        """
        input_el = self.wait_for_element(self.MIN_DATAPOINTS_INPUT)
        input_el.clear()
        input_el.send_keys(str(value))
        input_el.send_keys(Keys.TAB)

    # --- Logout Methods ---

    def click_logout(self) -> None:
        """Click the Logout button and confirm the 'Are you sure?' dialog."""
        logout_btn = self.wait_for_clickable(self.LOGOUT_BUTTON)
        logout_btn.click()
        # Confirm the "Are you sure you want to log out?" dialog
        confirm_btn = self.wait_for_clickable(self.LOGOUT_CONFIRM_BUTTON)
        confirm_btn.click()
