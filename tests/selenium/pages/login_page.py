"""Page object for the Login page (/login)."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.selenium.pages.base_page import BasePage


class LoginPage(BasePage):
    """Page object encapsulating the Login page locators and interactions.

    Provides methods to log in, check error messages, and verify
    submit button state on the /login route.
    """

    # Locators
    EMAIL_INPUT = (By.ID, "login-email")
    PASSWORD_INPUT = (By.ID, "login-password")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit'].btn-primary.auth-page__submit")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".auth-page__error[role='alert']")
    REGISTER_LINK = (By.CSS_SELECTOR, "a.auth-page__link[href='/register']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        """Initialize LoginPage.

        Args:
            driver: Selenium WebDriver instance.
            base_url: Base URL of the application.
        """
        super().__init__(driver, base_url)

    def login(self, email: str, password: str) -> None:
        """Navigate to /login, fill in credentials, and click submit.

        Args:
            email: The email address to enter.
            password: The password to enter.
        """
        self.navigate("/login")
        email_field = self.wait_for_element(self.EMAIL_INPUT)
        email_field.clear()
        email_field.send_keys(email)

        password_field = self.wait_for_element(self.PASSWORD_INPUT)
        password_field.clear()
        password_field.send_keys(password)

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

        Returns:
            True if the submit button is enabled, False if disabled.
        """
        submit_btn = self.wait_for_element(self.SUBMIT_BUTTON)
        return submit_btn.is_enabled()

    def click_register_link(self) -> None:
        """Click the 'Register' link to navigate to the registration page."""
        link = self.wait_for_clickable(self.REGISTER_LINK)
        link.click()
