"""Page object for the Register page (/register)."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.selenium.pages.base_page import BasePage


class RegisterPage(BasePage):
    """Page object encapsulating the Register page locators and interactions.

    Provides methods to register a new account, check error/hint messages,
    and verify submit button state on the /register route.
    """

    # Locators
    EMAIL_INPUT = (By.ID, "register-email")
    PASSWORD_INPUT = (By.ID, "register-password")
    CONFIRM_PASSWORD_INPUT = (By.ID, "register-confirm-password")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit'].btn-primary.auth-page__submit")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".auth-page__error[role='alert']")
    PASSWORD_HINT = (By.CSS_SELECTOR, ".auth-page__hint")
    MISMATCH_HINT = (By.CSS_SELECTOR, ".auth-page__hint.auth-page__hint--error")
    LOGIN_LINK = (By.CSS_SELECTOR, "a.auth-page__link[href='/login']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        """Initialize RegisterPage.

        Args:
            driver: Selenium WebDriver instance.
            base_url: Base URL of the application.
        """
        super().__init__(driver, base_url)

    def register(self, email: str, password: str, confirm: str) -> None:
        """Navigate to /register, fill in all fields, and click submit.

        Args:
            email: The email address to register with.
            password: The password to use (must be ≥8 characters).
            confirm: The confirm password value (should match password).
        """
        self.navigate("/register")
        email_field = self.wait_for_element(self.EMAIL_INPUT)
        email_field.clear()
        email_field.send_keys(email)

        password_field = self.wait_for_element(self.PASSWORD_INPUT)
        password_field.clear()
        password_field.send_keys(password)

        confirm_field = self.wait_for_element(self.CONFIRM_PASSWORD_INPUT)
        confirm_field.clear()
        confirm_field.send_keys(confirm)

        submit_btn = self.wait_for_clickable(self.SUBMIT_BUTTON)
        submit_btn.click()

    def get_error_message(self) -> str:
        """Wait for the error message element and return its text.

        Returns:
            The text content of the error message element.

        Raises:
            TimeoutException: If no error message appears within the timeout.
        """
        error_el = self.wait_for_element(self.ERROR_MESSAGE)
        return error_el.text

    def is_submit_enabled(self) -> bool:
        """Check whether the submit button is currently enabled.

        The submit button is disabled when:
        - Password is shorter than 8 characters
        - Password and confirm password do not match
        - A submission is in progress

        Returns:
            True if the submit button is enabled, False if disabled.
        """
        submit_btn = self.wait_for_element(self.SUBMIT_BUTTON)
        return submit_btn.is_enabled()

    def get_password_hint(self) -> str:
        """Get the password hint text (shown when password is >0 and <8 chars).

        Returns:
            The text of the password hint element.

        Raises:
            TimeoutException: If no hint appears within the timeout.
        """
        hint_el = self.wait_for_element(self.PASSWORD_HINT)
        return hint_el.text

    def get_mismatch_hint(self) -> str:
        """Get the password mismatch hint text.

        Returns:
            The text of the mismatch hint element.

        Raises:
            TimeoutException: If no mismatch hint appears within the timeout.
        """
        hint_el = self.wait_for_element(self.MISMATCH_HINT)
        return hint_el.text

    def click_login_link(self) -> None:
        """Click the 'Sign in' link to navigate to the login page."""
        link = self.wait_for_clickable(self.LOGIN_LINK)
        link.click()
