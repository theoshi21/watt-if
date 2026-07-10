"""Page object for the TopBar header component."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.selenium.pages.base_page import BasePage


class TopBar(BasePage):
    """Page object encapsulating the TopBar locators and interactions.

    The TopBar is a sticky header containing a hamburger menu button
    (mobile only), the current page title, a dark mode toggle, and
    a user account button.
    """

    # Locators
    HEADER = (By.CSS_SELECTOR, "header.topbar-compact")
    HAMBURGER_BUTTON = (By.CSS_SELECTOR, "button.topbar-menu-btn[aria-label='Open navigation menu']")
    PAGE_TITLE = (By.CSS_SELECTOR, "header.topbar-compact h1")
    DARK_MODE_TOGGLE = (By.CSS_SELECTOR, "button[aria-label='Toggle dark mode']")
    USER_ACCOUNT_BUTTON = (By.CSS_SELECTOR, "button[aria-label='User account']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        """Initialize TopBar.

        Args:
            driver: Selenium WebDriver instance.
            base_url: Base URL of the application.
        """
        super().__init__(driver, base_url)

    def toggle_dark_mode(self) -> None:
        """Click the dark mode toggle button.

        Raises:
            TimeoutException: If the toggle button is not clickable.
        """
        toggle = self.wait_for_clickable(self.DARK_MODE_TOGGLE)
        toggle.click()

    def is_dark_mode(self) -> bool:
        """Check whether the application is in dark mode.

        Dark mode is indicated by the ``data-theme="dark"`` attribute
        on the ``<html>`` element.

        Returns:
            True if dark mode is active, False otherwise.
        """
        theme = self.driver.execute_script(
            "return document.documentElement.getAttribute('data-theme');"
        )
        return theme == "dark"

    def click_settings_icon(self) -> None:
        """Click the user account button to navigate to /account.

        Raises:
            TimeoutException: If the user account button is not clickable.
        """
        btn = self.wait_for_clickable(self.USER_ACCOUNT_BUTTON)
        btn.click()

    def get_health_status(self) -> str:
        """Return the health status text from the sidebar health indicator.

        This delegates to the sidebar's health indicator element since
        the TopBar itself does not render a health widget.

        Returns:
            The health status text.

        Raises:
            TimeoutException: If the health indicator is not found.
        """
        health = self.wait_for_element(
            (By.CSS_SELECTOR, "aside[aria-label='System health']")
        )
        return health.text.strip()

    def get_page_title(self) -> str:
        """Return the current page title displayed in the TopBar.

        Returns:
            The text of the h1 element (e.g., "Dashboard", "Forecast").

        Raises:
            TimeoutException: If the page title element is not found.
        """
        title = self.wait_for_element(self.PAGE_TITLE)
        return title.text.strip()

    def open_mobile_menu(self) -> None:
        """Click the hamburger button to open the mobile sidebar.

        The hamburger button is only visible on mobile viewports
        (≤767px width).

        Raises:
            TimeoutException: If the hamburger button is not clickable.
        """
        hamburger = self.wait_for_clickable(self.HAMBURGER_BUTTON)
        hamburger.click()
