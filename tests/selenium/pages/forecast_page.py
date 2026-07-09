"""Page object for the Forecast page (/forecast)."""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver

from tests.selenium.pages.base_page import BasePage


class ForecastPage(BasePage):
    """Page object encapsulating the Forecast page locators and interactions.

    Provides methods to select forecast horizons, inspect chart elements,
    hover for tooltips, and check error/loading states on the /forecast route.
    """

    # Locators
    HORIZON_GROUP = (By.CSS_SELECTOR, 'div[role="group"][aria-label="Forecast horizon"]')
    BAR_CHART_CONTAINER = (By.CSS_SELECTOR, 'div[aria-label="Forecast charts"]')
    BARS = (By.CSS_SELECTOR, ".recharts-bar-rectangle")
    LINE_DOTS = (By.CSS_SELECTOR, ".recharts-line-dot")
    ERROR_BARS = (By.CSS_SELECTOR, ".recharts-errorBar line")
    TOOLTIP = (By.CSS_SELECTOR, ".recharts-tooltip-wrapper")
    ERROR_MESSAGE = (By.CSS_SELECTOR, 'p[role="alert"]')
    LOADING = (By.CSS_SELECTOR, 'span[role="status"]')
    XAXIS_LABELS = (By.CSS_SELECTOR, ".recharts-xAxis .recharts-cartesian-axis-tick-value")
    BUDGET_ALERT = (By.CSS_SELECTOR, 'div[role="alert"]')

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        """Initialize ForecastPage.

        Args:
            driver: Selenium WebDriver instance.
            base_url: Base URL of the application.
        """
        super().__init__(driver, base_url)

    @staticmethod
    def _horizon_button_locator(n: int) -> tuple:
        """Build a locator for a specific horizon button by month value.

        Args:
            n: The horizon month value (1, 3, 6, 9, or 12).

        Returns:
            A (By, selector) tuple targeting the button with matching text.
        """
        return (By.XPATH, f'//div[@role="group"][@aria-label="Forecast horizon"]//button[contains(text(),"{n} Mo")]')

    def select_horizon(self, n: int) -> None:
        """Select a forecast horizon by clicking the corresponding button.

        Args:
            n: The horizon month value (1, 3, 6, 9, or 12).
        """
        locator = self._horizon_button_locator(n)
        btn = self.wait_for_clickable(locator)
        btn.click()

    def get_bar_count(self) -> int:
        """Count the number of bar rectangles in the kWh chart.

        Returns:
            The number of bar elements currently rendered.
        """
        bars = self.find_elements(self.BARS)
        return len(bars)

    def get_line_point_count(self) -> int:
        """Count the number of dots (data points) in the bill line chart.

        Returns:
            The number of line dot elements currently rendered.
        """
        dots = self.find_elements(self.LINE_DOTS)
        return len(dots)

    def hover_bar(self, index: int) -> None:
        """Hover over a bar at the given index using ActionChains.

        Args:
            index: Zero-based index of the bar to hover over.

        Raises:
            IndexError: If the index is out of range of available bars.
        """
        bars = self.find_elements(self.BARS)
        if index >= len(bars):
            raise IndexError(f"Bar index {index} out of range (found {len(bars)} bars)")
        ActionChains(self.driver).move_to_element(bars[index]).perform()

    def get_tooltip_text(self) -> str:
        """Return the text content of the visible tooltip.

        Should be called after hovering over a chart element.

        Returns:
            The tooltip text content.

        Raises:
            TimeoutException: If the tooltip does not become visible.
        """
        tooltip = self.wait_for_element(self.TOOLTIP)
        return tooltip.text

    def get_error_message(self) -> str:
        """Wait for the error message element and return its text.

        Returns:
            The text content of the error alert paragraph.

        Raises:
            TimeoutException: If no error message appears within the timeout.
        """
        error_el = self.wait_for_element(self.ERROR_MESSAGE)
        return error_el.text

    def get_xaxis_labels(self) -> list[str]:
        """Return a list of x-axis label texts from the chart.

        Returns:
            List of label strings (e.g., ["Jan 2026", "Feb 2026", "Mar 2026"]).
        """
        elements = self.find_elements(self.XAXIS_LABELS)
        return [el.text for el in elements]

    def has_error_bars(self) -> bool:
        """Check whether error bar elements are present in the chart.

        Returns:
            True if at least one error bar line element exists, False otherwise.
        """
        error_bars = self.find_elements(self.ERROR_BARS)
        return len(error_bars) > 0

    def is_loading(self) -> bool:
        """Check whether the loading indicator is currently visible.

        Returns:
            True if the loading status element is present, False otherwise.
        """
        loading_elements = self.find_elements(self.LOADING)
        return len(loading_elements) > 0

    def wait_for_chart_loaded(self, timeout: int = 15) -> None:
        """Wait for the loading indicator to disappear and chart to render.

        Args:
            timeout: Maximum seconds to wait for loading to finish.

        Raises:
            TimeoutException: If loading doesn't finish within the timeout.
        """
        self.wait_for_element_invisible(self.LOADING, timeout)
        self.wait_for_element(self.BAR_CHART_CONTAINER, timeout)

    def has_budget_alert(self) -> bool:
        """Check whether a budget alert banner is displayed.

        Returns:
            True if a budget alert div[role='alert'] is present, False otherwise.
        """
        alerts = self.find_elements(self.BUDGET_ALERT)
        return len(alerts) > 0
