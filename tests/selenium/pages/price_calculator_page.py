"""Page object for the Price Calculator page (/calculator)."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import Select

from tests.selenium.pages.base_page import BasePage


class PriceCalculatorPage(BasePage):
    """Page object encapsulating the Price Calculator page locators and interactions.

    Provides methods to enter kWh values, select customer types and brackets,
    retrieve bill breakdowns, and interact with rate display/refresh on the
    /calculator route.
    """

    # Locators
    KWH_INPUT = (By.CSS_SELECTOR, "input#calc-kwh")
    CUSTOMER_TYPE_SELECT = (By.CSS_SELECTOR, "select#customer-type")
    BRACKET_SELECT = (By.CSS_SELECTOR, "select#bracket-select")
    REFRESH_BUTTON = (By.XPATH, '//button[contains(text(),"Refresh Rate") or contains(text(),"Refreshing")]')
    BREAKDOWN_SECTION = (By.CSS_SELECTOR, 'section[aria-labelledby="breakdown-heading"]')
    TOTAL_CARD = (By.XPATH, '//span[contains(text(),"Estimated Bill")]/parent::div')
    RATE_STATUS = (By.CSS_SELECTOR, 'p[role="status"]')
    RATE_ERROR = (By.CSS_SELECTOR, 'div.card[role="alert"]')
    RATE_INFO = (By.XPATH, '//p[contains(text(),"Meralco Summary Schedule of Rates")]')
    INPUT_SECTION = (By.CSS_SELECTOR, 'section[aria-labelledby="input-heading"]')

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        """Initialize PriceCalculatorPage.

        Args:
            driver: Selenium WebDriver instance.
            base_url: Base URL of the application.
        """
        super().__init__(driver, base_url)

    def enter_kwh(self, value: str | int) -> None:
        """Type a kWh value into the monthly consumption input field.

        Clears any existing value before typing the new one.

        Args:
            value: The kWh value to enter (string or integer).
        """
        input_el = self.wait_for_element(self.KWH_INPUT)
        input_el.clear()
        input_el.send_keys(str(value))

    def get_breakdown(self) -> list[dict]:
        """Retrieve bill breakdown line items from the breakdown section.

        Returns:
            A list of dicts with 'label' and 'amount' keys for each charge line.
            Returns an empty list if no breakdown is displayed.
        """
        section = self.wait_for_element(self.BREAKDOWN_SECTION)
        # Each BillLine is a flex div with label span and amount span
        line_divs = section.find_elements(
            By.CSS_SELECTOR,
            'div[style*="justify-content: space-between"]'
        )
        items = []
        for line in line_divs:
            spans = line.find_elements(By.CSS_SELECTOR, "span")
            if len(spans) >= 2:
                # First span in the first child div is the label
                label_div = line.find_elements(By.CSS_SELECTOR, "div > span:first-child")
                amount_spans = line.find_elements(By.XPATH, "./span")
                label = label_div[0].text if label_div else ""
                # The amount is the last direct span child of the line div
                amount = amount_spans[0].text if amount_spans else ""
                if not amount:
                    # Fallback: get all spans and take the last one
                    all_spans = line.find_elements(By.CSS_SELECTOR, "span")
                    amount = all_spans[-1].text if all_spans else ""
                items.append({"label": label, "amount": amount})
        return items

    def get_rate_display(self) -> str:
        """Return the rate info text including effective month and live/fallback status.

        Returns:
            The text content of the rate subtitle paragraph (e.g.,
            "Meralco Summary Schedule of Rates · June 2026 Live").
        """
        # The rate info is in the header paragraph containing "Meralco Summary Schedule of Rates"
        info_el = self.wait_for_element(self.RATE_INFO)
        return info_el.text

    def get_selected_bracket(self) -> str:
        """Return the currently active bracket text.

        If bracket is set to "auto", reads the auto-detected bracket from
        the label hint "(auto: XXX)". Otherwise returns the selected option text.

        Returns:
            The bracket label text (e.g., "301 TO 400 KWH").
        """
        select_el = self.wait_for_element(self.BRACKET_SELECT)
        select = Select(select_el)
        selected_text = select.first_selected_option.text

        # If auto is selected, look for the "(auto: ...)" hint in the label
        if "auto" in selected_text.lower():
            hints = self.driver.find_elements(
                By.XPATH, '//label[@for="bracket-select"]//span'
            )
            for hint in hints:
                text = hint.text
                if "auto:" in text.lower():
                    # Extract the bracket name from "(auto: 301 TO 400 KWH)"
                    return text.replace("(auto:", "").replace(")", "").strip()
            return selected_text

        return selected_text

    def select_bracket(self, bracket_key: str) -> None:
        """Select a specific bracket from the bracket dropdown by value.

        Args:
            bracket_key: The option value attribute to select
                         (e.g., "301 TO 400 KWH" or "auto").
        """
        select_el = self.wait_for_element(self.BRACKET_SELECT)
        select = Select(select_el)
        select.select_by_value(bracket_key)

    def change_customer_type(self, type_key: str) -> None:
        """Select a customer type from the customer type dropdown by value.

        Args:
            type_key: The customer type value to select
                      (e.g., "Residential", "General Service A", "General Service B").
        """
        select_el = self.wait_for_element(self.CUSTOMER_TYPE_SELECT)
        select = Select(select_el)
        select.select_by_value(type_key)

    def refresh_rate(self) -> None:
        """Click the Refresh Rate button to reload rate data.

        Waits for the button to be clickable before clicking.
        """
        btn = self.wait_for_clickable(self.REFRESH_BUTTON)
        btn.click()

    def get_total_bill(self) -> str:
        """Return the total bill amount text from the Estimated Bill card.

        Returns:
            The total bill amount text string (e.g., "₱2,345.67").
        """
        # The total card has "Estimated Bill" label and a large peso value
        card = self.wait_for_element(self.TOTAL_CARD)
        # The large value is the second span (font-size 2rem, font-mono)
        spans = card.find_elements(By.CSS_SELECTOR, "span")
        # Find the span that contains ₱ (the actual value)
        for span in spans:
            text = span.text.strip()
            if "₱" in text and len(text) > 1:
                return text
        # Fallback: return the second span's text (index 1 = the big number)
        if len(spans) >= 2:
            return spans[1].text
        return card.text

    def is_breakdown_visible(self) -> bool:
        """Check whether the breakdown section has line items displayed.

        Returns:
            True if the breakdown section contains at least one bill line item,
            False otherwise.
        """
        try:
            section = self.wait_for_element(self.BREAKDOWN_SECTION, timeout=3)
            lines = section.find_elements(
                By.CSS_SELECTOR,
                'div[style*="justify-content: space-between"]'
            )
            return len(lines) > 0
        except Exception:
            return False

    def get_last_fetched(self) -> str:
        """Return the 'Last fetched' timestamp text.

        Returns:
            The text of the span containing the last fetched date/time
            (e.g., "Last fetched: Jan 15, 2026, 10:30 AM").
        """
        last_fetched = self.driver.find_element(
            By.XPATH, '//span[contains(text(),"Last fetched:")]'
        )
        return last_fetched.text
