"""Page object for the Dashboard page (route '/')."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.selenium.pages.base_page import BasePage


class DashboardPage(BasePage):
    """Page object encapsulating locators and actions for the Dashboard page.

    The Dashboard displays stat cards (This Month, Daily Average, Avg Temp,
    Avg Humidity), an optional anomaly card, and a forecast chart when
    forecast data is available. Shows an empty state or error state otherwise.
    """

    # ── Locators ────────────────────────────────────────────────────────────
    STAT_GRID = (By.CSS_SELECTOR, ".stat-grid")
    STAT_CARDS = (By.CSS_SELECTOR, ".stat-grid .card")
    STAT_CARD_LABEL = (By.CSS_SELECTOR, "dt")
    STAT_CARD_VALUE = (By.CSS_SELECTOR, "dd")
    STAT_CARD_UNIT = (By.CSS_SELECTOR, "dd span")
    FORECAST_CHART = (By.CSS_SELECTOR, "[aria-label='Forecast charts']")
    PAGE_CONTENT = (By.CSS_SELECTOR, ".page-content")

    def __init__(self, driver: WebDriver, base_url: str):
        """Initialize DashboardPage.

        Args:
            driver: Selenium WebDriver instance.
            base_url: Base URL of the application.
        """
        super().__init__(driver, base_url)

    def get_stat_cards(self) -> list[dict]:
        """Get all stat cards displayed on the dashboard.

        Returns:
            A list of dicts with keys 'label', 'value', and 'unit' for each
            stat card in the stat grid.
        """
        self.wait_for_element(self.STAT_GRID)
        cards = self.find_elements(self.STAT_CARDS)
        result = []
        for card in cards:
            label_el = card.find_element(*self.STAT_CARD_LABEL)
            value_el = card.find_element(*self.STAT_CARD_VALUE)
            # Unit is inside a <span> within the <dd>
            unit_els = card.find_elements(*self.STAT_CARD_UNIT)
            unit = unit_els[0].text if unit_els else ""
            # The value text includes the unit span text; strip it out
            full_text = value_el.text
            value_text = full_text.replace(unit, "").strip() if unit else full_text.strip()
            result.append({
                "label": label_el.text.strip(),
                "value": value_text,
                "unit": unit.strip(),
            })
        return result

    def has_anomaly_card(self) -> bool:
        """Check whether the anomaly card is displayed on the dashboard.

        The anomaly card contains text 'Anomaly Detected:' and appears when
        the first forecast month exceeds 110% of the mean.

        Returns:
            True if the anomaly card is visible, False otherwise.
        """
        elements = self.driver.find_elements(
            By.XPATH, "//*[contains(text(), 'Anomaly Detected:')]"
        )
        return len(elements) > 0 and elements[0].is_displayed()

    def has_forecast_chart(self) -> bool:
        """Check whether the forecast chart container is visible.

        Returns:
            True if the chart container with aria-label 'Forecast charts'
            is present and visible, False otherwise.
        """
        elements = self.find_elements(self.FORECAST_CHART)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_empty_state(self) -> bool:
        """Check whether the empty state message is displayed.

        The empty state shows 'No forecast data yet.' when no forecast
        data is available.

        Returns:
            True if the empty state text is visible, False otherwise.
        """
        elements = self.driver.find_elements(
            By.XPATH, "//*[contains(text(), 'No forecast data yet.')]"
        )
        return len(elements) > 0 and elements[0].is_displayed()

    def is_error_state(self) -> bool:
        """Check whether the error state is displayed.

        The error state shows 'Could not load forecast' when data loading fails.

        Returns:
            True if the error state text is visible, False otherwise.
        """
        elements = self.driver.find_elements(
            By.XPATH, "//*[contains(text(), 'Could not load forecast')]"
        )
        return len(elements) > 0 and elements[0].is_displayed()

    def get_stat_value(self, label: str) -> str | None:
        """Get the value string for a stat card matching the given label.

        Args:
            label: The stat card label to search for (e.g., 'This Month',
                   'Daily Average', 'Avg Temp', 'Avg Humidity').
                   Comparison is case-insensitive.

        Returns:
            The value string (without unit) if a card with the label is found,
            or None if no matching card exists.
        """
        cards = self.get_stat_cards()
        for card in cards:
            if card["label"].lower() == label.lower():
                return card["value"]
        return None
