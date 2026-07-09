"""Page object for the Sidebar navigation component."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.selenium.pages.base_page import BasePage


class Sidebar(BasePage):
    """Page object encapsulating the Sidebar locators and interactions.

    The sidebar contains the main navigation links, a health indicator,
    user email display, and a logout button. On mobile viewports, the
    sidebar is hidden by default and revealed via a hamburger button in
    the TopBar; it can be closed via the overlay or Escape key.
    """

    # Locators
    NAV_SIDEBAR = (By.CSS_SELECTOR, "nav[aria-label='Main navigation']")
    NAV_LINKS = (By.CSS_SELECTOR, "ul[role='list'] a.nav-item")
    ACTIVE_LINK = (By.CSS_SELECTOR, "ul[role='list'] a.nav-item--active")
    LOGOUT_BUTTON = (By.CSS_SELECTOR, "button[aria-label='Logout']")
    SIDEBAR_WRAPPER = (By.CSS_SELECTOR, ".app-shell__sidebar")
    SIDEBAR_OPEN = (By.CSS_SELECTOR, ".app-shell__sidebar--open")
    OVERLAY = (By.CSS_SELECTOR, ".app-shell__overlay--visible")
    HEALTH_INDICATOR = (By.CSS_SELECTOR, "aside[aria-label='System health']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        """Initialize Sidebar.

        Args:
            driver: Selenium WebDriver instance.
            base_url: Base URL of the application.
        """
        super().__init__(driver, base_url)

    def navigate_to(self, page: str) -> None:
        """Click a navigation link matching the given page name.

        Args:
            page: The visible link text to click (e.g., "Dashboard",
                  "Forecast", "Ask WATT-IF", "Price Calculator", "Data Entry").

        Raises:
            TimeoutException: If the sidebar or the target link is not found.
        """
        self.wait_for_element(self.NAV_SIDEBAR)
        links = self.find_elements(self.NAV_LINKS)
        for link in links:
            if link.text.strip() == page:
                link.click()
                return
        raise ValueError(f"Navigation link '{page}' not found in sidebar")

    def get_active_link(self) -> str:
        """Return the text of the currently active navigation link.

        Returns:
            The text content of the nav link with the active class.

        Raises:
            TimeoutException: If no active link is found within the timeout.
        """
        active = self.wait_for_element(self.ACTIVE_LINK)
        return active.text.strip()

    def click_logout(self) -> None:
        """Click the Logout button in the sidebar.

        Raises:
            TimeoutException: If the logout button is not clickable.
        """
        logout_btn = self.wait_for_clickable(self.LOGOUT_BUTTON)
        logout_btn.click()

    def is_visible(self) -> bool:
        """Check whether the sidebar nav element is currently visible.

        Returns:
            True if the sidebar nav is displayed, False otherwise.
        """
        elements = self.find_elements(self.NAV_SIDEBAR)
        if not elements:
            return False
        return elements[0].is_displayed()

    def close_mobile_menu(self) -> None:
        """Close the mobile sidebar by clicking the overlay.

        The overlay becomes visible when the sidebar is open on mobile.

        Raises:
            TimeoutException: If the overlay is not clickable.
        """
        overlay = self.wait_for_clickable(self.OVERLAY)
        overlay.click()

    def get_health_status(self) -> str:
        """Return the text of the health indicator in the sidebar.

        Returns:
            The health status text (e.g., "All systems operational",
            "Backend offline", or individual subsystem names).

        Raises:
            TimeoutException: If the health indicator is not found.
        """
        health = self.wait_for_element(self.HEALTH_INDICATOR)
        return health.text.strip()
