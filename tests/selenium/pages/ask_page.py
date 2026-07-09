"""Page object for the Ask page (/ask) containing the ChatPanel component."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium.pages.base_page import BasePage


class AskPage(BasePage):
    """Page object encapsulating the Ask (Chat) page locators and interactions.

    Provides methods to send messages, read conversation history, clear chat,
    check input state, and wait for assistant responses on the /ask route.
    """

    # Locators
    CHAT_SECTION = (By.CSS_SELECTOR, "section.card[aria-label='Chat']")
    MESSAGE_INPUT = (By.CSS_SELECTOR, "input[aria-label='Question input']")
    SEND_BUTTON = (By.CSS_SELECTOR, "button[aria-label='Submit question']")
    CLEAR_BUTTON = (By.CSS_SELECTOR, "button[aria-label='Clear conversation']")
    MESSAGE_LOG = (By.CSS_SELECTOR, "div[role='log'][aria-label='Conversation']")
    USER_BUBBLE = (By.CSS_SELECTOR, "div[role='article'][aria-label='user']")
    ASSISTANT_BUBBLE = (By.CSS_SELECTOR, "div[role='article'][aria-label='assistant']")
    ERROR_BUBBLE = (By.CSS_SELECTOR, "div[role='article'][aria-label='error']")
    EMPTY_STATE = (
        By.XPATH,
        "//div[@role='log']//p[contains(text(),'Ask a question about your electricity forecast')]",
    )
    CHAR_COUNTER = (By.CSS_SELECTOR, "div[aria-live='polite']")
    LOADING_INDICATOR = (
        By.XPATH,
        "//div[@role='log']//span[contains(text(),'Generating answer')]",
    )

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        """Initialize AskPage.

        Args:
            driver: Selenium WebDriver instance.
            base_url: Base URL of the application.
        """
        super().__init__(driver, base_url)

    def send_message(self, text: str) -> None:
        """Clear the input field, type a message, and click the submit button.

        Does NOT wait for an assistant response after submission.

        Args:
            text: The message text to send.
        """
        input_field = self.wait_for_element(self.MESSAGE_INPUT)
        input_field.clear()
        input_field.send_keys(text)
        send_btn = self.wait_for_clickable(self.SEND_BUTTON)
        send_btn.click()

    def get_messages(self) -> list[dict]:
        """Return all visible message bubbles as a list of dicts.

        Each dict has 'role' ("user", "assistant", or "error") and 'text' keys.

        Returns:
            A list of message dictionaries in display order.
        """
        bubbles = self.find_elements(
            (By.CSS_SELECTOR, "div[role='article']")
        )
        messages = []
        for bubble in bubbles:
            role = bubble.get_attribute("aria-label")
            text = bubble.text.strip()
            if role in ("user", "assistant", "error"):
                messages.append({"role": role, "text": text})
        return messages

    def clear_chat(self) -> None:
        """Click the 'Clear conversation' button to remove all messages."""
        clear_btn = self.wait_for_clickable(self.CLEAR_BUTTON)
        clear_btn.click()

    def is_send_enabled(self) -> bool:
        """Check whether the submit (Ask) button is currently enabled.

        Returns:
            True if the submit button is enabled, False if disabled.
        """
        send_btn = self.wait_for_element(self.SEND_BUTTON)
        return send_btn.is_enabled()

    def get_input_length(self) -> int:
        """Return the current character count of the input field.

        Returns:
            The number of characters currently in the question input.
        """
        input_field = self.wait_for_element(self.MESSAGE_INPUT)
        value = input_field.get_attribute("value") or ""
        return len(value)

    def wait_for_response(self, timeout: int = 30) -> None:
        """Wait until a new assistant bubble appears or the loading indicator disappears.

        This method waits for the streaming response to complete by checking
        that the loading indicator ("Generating answer…") is no longer visible.

        Args:
            timeout: Maximum seconds to wait for the response (default 30).

        Raises:
            TimeoutException: If no response arrives within the timeout.
        """
        wait = WebDriverWait(self.driver, timeout)
        # Wait for loading indicator to disappear (response finished streaming)
        wait.until(EC.invisibility_of_element_located(self.LOADING_INDICATOR))
        # Ensure at least one assistant bubble is present
        wait.until(
            EC.presence_of_element_located(self.ASSISTANT_BUBBLE)
        )

    def get_empty_state_text(self) -> str | None:
        """Return the empty state text if visible, None otherwise.

        Returns:
            The empty state paragraph text, or None if not displayed.
        """
        elements = self.find_elements(self.EMPTY_STATE)
        if elements and elements[0].is_displayed():
            return elements[0].text.strip()
        return None
