"""Base page object class with shared utilities for all page objects."""

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    """Base class for all page objects.

    Provides common navigation, wait, and localStorage utilities
    shared across all page-specific page objects.
    """

    def __init__(self, driver: WebDriver, base_url: str):
        """Initialize BasePage with a WebDriver instance and application base URL.

        Args:
            driver: Selenium WebDriver instance.
            base_url: Base URL of the application (e.g., "http://localhost:5173").
        """
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 30)

    def navigate(self, path: str) -> None:
        """Navigate to a path relative to the base URL.

        Args:
            path: Relative path to navigate to (e.g., "/login", "/dashboard").
        """
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        self.driver.get(url)

    def wait_for_element(self, locator: tuple, timeout: int = 30) -> WebElement:
        """Wait for an element to be visible and return it.

        Uses polling (WebDriverWait) — returns immediately once the element
        is visible. The timeout is the maximum wait, not a fixed delay.

        Args:
            locator: Tuple of (By strategy, locator string), e.g., (By.CSS_SELECTOR, "#id").
            timeout: Maximum seconds to wait (default 30).

        Returns:
            The located WebElement once visible.

        Raises:
            TimeoutException: If the element is not visible within the timeout.
        """
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.visibility_of_element_located(locator))

    def wait_for_element_invisible(self, locator: tuple, timeout: int = 10) -> bool:
        """Wait for an element to become invisible or absent from the DOM.

        Args:
            locator: Tuple of (By strategy, locator string).
            timeout: Maximum seconds to wait (default 10).

        Returns:
            True once the element is no longer visible.

        Raises:
            TimeoutException: If the element is still visible after the timeout.
        """
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.invisibility_of_element_located(locator))

    def wait_for_clickable(self, locator: tuple, timeout: int = 30) -> WebElement:
        """Wait for an element to be clickable and return it.

        Uses polling (WebDriverWait) — returns immediately once clickable.
        The timeout is the maximum wait, not a fixed delay.

        Args:
            locator: Tuple of (By strategy, locator string), e.g., (By.CSS_SELECTOR, "#btn").
            timeout: Maximum seconds to wait (default 30).

        Returns:
            The located WebElement once clickable.

        Raises:
            TimeoutException: If the element is not clickable within the timeout.
        """
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.element_to_be_clickable(locator))

    def find_elements(self, locator: tuple) -> list[WebElement]:
        """Find all elements matching a locator without waiting.

        Useful for counting elements that may or may not exist.

        Args:
            locator: Tuple of (By strategy, locator string).

        Returns:
            A list of matching WebElements (empty list if none found).
        """
        return self.driver.find_elements(*locator)

    def get_local_storage(self, key: str) -> str | None:
        """Retrieve a value from the browser's localStorage.

        Args:
            key: The localStorage key to retrieve.

        Returns:
            The stored value as a string, or None if the key does not exist.
        """
        return self.driver.execute_script(
            "return window.localStorage.getItem(arguments[0]);", key
        )

    def set_local_storage(self, key: str, value: str) -> None:
        """Set a key-value pair in the browser's localStorage.

        Args:
            key: The localStorage key to set.
            value: The value to store.
        """
        self.driver.execute_script(
            "window.localStorage.setItem(arguments[0], arguments[1]);", key, value
        )

    def remove_local_storage(self, key: str) -> None:
        """Remove a key from the browser's localStorage.

        Args:
            key: The localStorage key to remove.
        """
        self.driver.execute_script(
            "window.localStorage.removeItem(arguments[0]);", key
        )

    def get_current_url(self) -> str:
        """Get the current page URL.

        Returns:
            The current URL as a string.
        """
        return self.driver.current_url
