"""
Chat Assistant test module (CHT-01 to CHT-11).

Covers message submission, streaming responses, input validation,
chat persistence, navigation persistence, and clear functionality
for the WATT-IF Ask page ChatPanel component.

Requirements: 12.1–12.10
"""

import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium.pages import AskPage, Sidebar


# ---------------------------------------------------------------------------
# CHT-01: Valid Question Submission
# ---------------------------------------------------------------------------


@pytest.mark.chat
def test_CHT_01_valid_question(logged_in_driver, base_url):
    """Submit a valid question and verify the user bubble appears and a streaming
    response completes without error within 30 seconds."""
    page = AskPage(logged_in_driver, base_url)
    page.navigate("/ask")

    # Wait for history loading to finish (empty state or messages visible)
    WebDriverWait(logged_in_driver, 10).until(
        lambda d: page.get_empty_state_text() is not None
        or len(page.get_messages()) > 0
    )

    question = "What is my predicted electricity usage next month?"
    page.send_message(question)

    # Wait for the streaming response to complete (up to 30s)
    page.wait_for_response(timeout=30)

    # Verify messages contain the user bubble and an assistant response
    messages = page.get_messages()
    user_messages = [m for m in messages if m["role"] == "user"]
    assistant_messages = [m for m in messages if m["role"] == "assistant"]

    assert len(user_messages) >= 1, "Expected at least one user message bubble"
    assert question in user_messages[-1]["text"], (
        f"User bubble should contain the question text, got: {user_messages[-1]['text']}"
    )
    assert len(assistant_messages) >= 1, "Expected at least one assistant response"
    assert len(assistant_messages[-1]["text"]) > 0, (
        "Assistant response should not be empty"
    )


# ---------------------------------------------------------------------------
# CHT-02: Forecast Context Response
# ---------------------------------------------------------------------------


@pytest.mark.chat
def test_CHT_02_forecast_context_response(logged_in_driver, base_url):
    """Submit a question about a specific forecast month and verify the response
    references relevant forecast data (kWh, bill, or month name)."""
    page = AskPage(logged_in_driver, base_url)
    page.navigate("/ask")

    WebDriverWait(logged_in_driver, 10).until(
        lambda d: page.get_empty_state_text() is not None
        or len(page.get_messages()) > 0
    )

    question = "What is my forecasted electricity consumption for January 2026?"
    page.send_message(question)
    page.wait_for_response(timeout=30)

    messages = page.get_messages()
    assistant_messages = [m for m in messages if m["role"] == "assistant"]
    assert len(assistant_messages) >= 1, "Expected an assistant response"

    response_text = assistant_messages[-1]["text"].lower()
    # The response should reference forecast-related data
    forecast_keywords = ["kwh", "forecast", "january", "2026", "bill", "consumption", "usage", "predict"]
    has_forecast_reference = any(kw in response_text for kw in forecast_keywords)
    assert has_forecast_reference, (
        f"Response should reference forecast data. Got: {assistant_messages[-1]['text'][:200]}"
    )


# ---------------------------------------------------------------------------
# CHT-03: Out-of-Scope Question
# ---------------------------------------------------------------------------


@pytest.mark.chat
def test_CHT_03_out_of_scope_question(logged_in_driver, base_url):
    """Submit a question unrelated to electricity and verify the assistant
    declines with a message indicating it only handles electricity/billing topics."""
    page = AskPage(logged_in_driver, base_url)
    page.navigate("/ask")

    WebDriverWait(logged_in_driver, 10).until(
        lambda d: page.get_empty_state_text() is not None
        or len(page.get_messages()) > 0
    )

    question = "What is the capital of France?"
    page.send_message(question)
    page.wait_for_response(timeout=30)

    messages = page.get_messages()
    assistant_messages = [m for m in messages if m["role"] == "assistant"]
    assert len(assistant_messages) >= 1, "Expected an assistant response"

    response_text = assistant_messages[-1]["text"].lower()
    # Should contain a decline or scope-limiting message
    decline_keywords = [
        "electricity", "billing", "forecast", "energy",
        "can't help", "cannot help", "only", "unable",
        "outside", "scope", "don't have", "not able",
        "electric", "watt", "power", "consumption",
    ]
    has_decline = any(kw in response_text for kw in decline_keywords)
    assert has_decline, (
        f"Expected decline message about electricity topics. Got: {assistant_messages[-1]['text'][:200]}"
    )


# ---------------------------------------------------------------------------
# CHT-04: Empty Message — Ask Button Disabled
# ---------------------------------------------------------------------------


@pytest.mark.chat
def test_CHT_04_empty_message_disabled(logged_in_driver, base_url):
    """Verify the Ask button is disabled when the input field is empty or
    contains only whitespace, and clicking it produces no effect."""
    page = AskPage(logged_in_driver, base_url)
    page.navigate("/ask")

    WebDriverWait(logged_in_driver, 10).until(
        lambda d: page.get_empty_state_text() is not None
        or len(page.get_messages()) > 0
    )

    # With empty input, button should be disabled
    assert not page.is_send_enabled(), "Ask button should be disabled with empty input"

    # Type only whitespace
    input_field = page.wait_for_element(page.MESSAGE_INPUT)
    input_field.clear()
    input_field.send_keys("   ")

    # Button should still be disabled (input.trim().length === 0)
    assert not page.is_send_enabled(), (
        "Ask button should be disabled with whitespace-only input"
    )

    # Try clicking the disabled button — no messages should be sent
    send_btn = page.wait_for_element(page.SEND_BUTTON)
    send_btn.click()

    # Brief pause to allow any unintended action to occur
    time.sleep(1)

    # Verify no messages were sent
    messages = page.get_messages()
    user_messages = [m for m in messages if m["role"] == "user"]
    assert len(user_messages) == 0, (
        "No user messages should appear after clicking disabled Ask button"
    )


# ---------------------------------------------------------------------------
# CHT-05: Max Length (500 chars) Accepted
# ---------------------------------------------------------------------------


@pytest.mark.chat
def test_CHT_05_max_length_accepted(logged_in_driver, base_url):
    """Submit a message at exactly 500 characters and verify it is accepted
    and a response is generated without a character limit error."""
    page = AskPage(logged_in_driver, base_url)
    page.navigate("/ask")

    WebDriverWait(logged_in_driver, 10).until(
        lambda d: page.get_empty_state_text() is not None
        or len(page.get_messages()) > 0
    )

    # Create a 500-character message (valid question padded to exactly 500 chars)
    base_question = "What is my electricity forecast?"
    padding = "a" * (500 - len(base_question))
    message_500 = base_question + padding
    assert len(message_500) == 500, f"Message should be 500 chars, got {len(message_500)}"

    page.send_message(message_500)
    page.wait_for_response(timeout=30)

    messages = page.get_messages()
    user_messages = [m for m in messages if m["role"] == "user"]
    assistant_messages = [m for m in messages if m["role"] == "assistant"]

    assert len(user_messages) >= 1, "Expected user message to be accepted"
    assert len(assistant_messages) >= 1, "Expected an assistant response for 500-char message"

    # Verify no error occurred
    error_messages = [m for m in messages if m["role"] == "error"]
    assert len(error_messages) == 0, (
        "No error messages should appear for a 500-character input"
    )


# ---------------------------------------------------------------------------
# CHT-06: Exceeds Max Length (>500 chars)
# ---------------------------------------------------------------------------


@pytest.mark.chat
def test_CHT_06_exceeds_max_length(logged_in_driver, base_url):
    """Enter >500 characters and verify the input field stops accepting
    characters beyond 500 (enforced by HTML maxLength attribute)."""
    page = AskPage(logged_in_driver, base_url)
    page.navigate("/ask")

    WebDriverWait(logged_in_driver, 10).until(
        lambda d: page.get_empty_state_text() is not None
        or len(page.get_messages()) > 0
    )

    # Attempt to type a 600-character message
    long_message = "x" * 600
    input_field = page.wait_for_element(page.MESSAGE_INPUT)
    input_field.clear()
    input_field.send_keys(long_message)

    # The HTML input has maxLength=500, so the browser should truncate
    actual_length = page.get_input_length()
    assert actual_length <= 500, (
        f"Input should not accept more than 500 characters, got {actual_length}"
    )

    # Verify the character counter shows 500/500
    counter_el = page.wait_for_element(page.CHAR_COUNTER)
    counter_text = counter_el.text.strip()
    assert "500/500" in counter_text, (
        f"Character counter should show 500/500, got: {counter_text}"
    )


# ---------------------------------------------------------------------------
# CHT-07: Navigation Persistence
# ---------------------------------------------------------------------------


@pytest.mark.chat
def test_CHT_07_navigation_persistence(logged_in_driver, base_url):
    """Send a message, navigate away via sidebar, then return and verify all
    previous messages are still displayed in their original order."""
    page = AskPage(logged_in_driver, base_url)
    sidebar = Sidebar(logged_in_driver, base_url)
    page.navigate("/ask")

    WebDriverWait(logged_in_driver, 10).until(
        lambda d: page.get_empty_state_text() is not None
        or len(page.get_messages()) > 0
    )

    # Send a message and wait for response
    question = "How much electricity did I use last month?"
    page.send_message(question)
    page.wait_for_response(timeout=30)

    # Capture messages before navigating away
    messages_before = page.get_messages()
    assert len(messages_before) >= 2, "Should have at least user + assistant messages"

    # Navigate away using sidebar
    sidebar.navigate_to("Dashboard")
    WebDriverWait(logged_in_driver, 10).until(
        lambda d: "/ask" not in d.current_url
    )

    # Navigate back to Ask page
    sidebar.navigate_to("Ask WATT-IF")
    WebDriverWait(logged_in_driver, 10).until(
        EC.presence_of_element_located(page.MESSAGE_INPUT)
    )

    # Wait for history to load
    WebDriverWait(logged_in_driver, 10).until(
        lambda d: len(page.get_messages()) > 0
    )

    # Verify messages are preserved in order
    messages_after = page.get_messages()
    assert len(messages_after) >= len(messages_before), (
        f"Expected at least {len(messages_before)} messages after returning, got {len(messages_after)}"
    )

    # Check that the original messages are present in order
    for i, msg in enumerate(messages_before):
        assert messages_after[i]["role"] == msg["role"], (
            f"Message {i} role mismatch: expected {msg['role']}, got {messages_after[i]['role']}"
        )
        assert msg["text"] in messages_after[i]["text"], (
            f"Message {i} text mismatch: expected '{msg['text'][:50]}...' in '{messages_after[i]['text'][:50]}...'"
        )


# ---------------------------------------------------------------------------
# CHT-08: Clear Chat
# ---------------------------------------------------------------------------


@pytest.mark.chat
def test_CHT_08_clear_chat(logged_in_driver, base_url):
    """Send a message, click Clear, and verify all messages are removed and
    the empty-state prompt is displayed."""
    page = AskPage(logged_in_driver, base_url)
    page.navigate("/ask")

    WebDriverWait(logged_in_driver, 10).until(
        lambda d: page.get_empty_state_text() is not None
        or len(page.get_messages()) > 0
    )

    # Send a message to have something to clear
    page.send_message("What is my bill prediction?")
    page.wait_for_response(timeout=30)

    messages = page.get_messages()
    assert len(messages) >= 2, "Should have messages before clearing"

    # Clear the chat
    page.clear_chat()

    # Wait for messages to be removed
    WebDriverWait(logged_in_driver, 10).until(
        lambda d: len(page.get_messages()) == 0
    )

    # Verify empty state is shown
    empty_text = page.get_empty_state_text()
    assert empty_text is not None, "Empty state prompt should be displayed after clearing"
    assert "ask a question" in empty_text.lower(), (
        f"Empty state should prompt user to ask a question, got: {empty_text}"
    )


# ---------------------------------------------------------------------------
# CHT-09: Clear Persistence
# ---------------------------------------------------------------------------


@pytest.mark.chat
def test_CHT_09_clear_persistence(logged_in_driver, base_url):
    """Clear the chat, navigate away via sidebar and return, then verify
    the chat remains empty with no previous messages reappearing."""
    page = AskPage(logged_in_driver, base_url)
    sidebar = Sidebar(logged_in_driver, base_url)
    page.navigate("/ask")

    WebDriverWait(logged_in_driver, 10).until(
        lambda d: page.get_empty_state_text() is not None
        or len(page.get_messages()) > 0
    )

    # Send a message so we have something to clear
    page.send_message("Test message for clear persistence")
    page.wait_for_response(timeout=30)

    # Clear the chat
    page.clear_chat()

    # Wait for messages to be removed
    WebDriverWait(logged_in_driver, 10).until(
        lambda d: len(page.get_messages()) == 0
    )

    # Navigate away
    sidebar.navigate_to("Dashboard")
    WebDriverWait(logged_in_driver, 10).until(
        lambda d: "/ask" not in d.current_url
    )

    # Return to Ask page
    sidebar.navigate_to("Ask WATT-IF")
    WebDriverWait(logged_in_driver, 10).until(
        EC.presence_of_element_located(page.MESSAGE_INPUT)
    )

    # Wait for history loading to complete
    time.sleep(2)

    # Verify chat remains empty
    messages = page.get_messages()
    assert len(messages) == 0, (
        f"Chat should remain empty after clear + navigation, found {len(messages)} messages"
    )

    # Verify empty state is still shown
    empty_text = page.get_empty_state_text()
    assert empty_text is not None, (
        "Empty state prompt should be displayed after returning to cleared chat"
    )


# ---------------------------------------------------------------------------
# CHT-11: History on Refresh
# ---------------------------------------------------------------------------


@pytest.mark.chat
def test_CHT_11_history_on_refresh(logged_in_driver, base_url):
    """Send messages, perform a hard refresh, and verify previous messages are
    loaded from the database and displayed in chronological order."""
    page = AskPage(logged_in_driver, base_url)
    page.navigate("/ask")

    WebDriverWait(logged_in_driver, 10).until(
        lambda d: page.get_empty_state_text() is not None
        or len(page.get_messages()) > 0
    )

    # Send a message and wait for response
    question = "What is my electricity forecast for this month?"
    page.send_message(question)
    page.wait_for_response(timeout=30)

    # Capture messages before refresh
    messages_before = page.get_messages()
    assert len(messages_before) >= 2, "Should have at least user + assistant messages"

    # Perform a hard refresh
    logged_in_driver.refresh()

    # Wait for the page to reload and history to be fetched
    WebDriverWait(logged_in_driver, 15).until(
        EC.presence_of_element_located(page.MESSAGE_INPUT)
    )

    # Wait for chat history to load from backend
    WebDriverWait(logged_in_driver, 15).until(
        lambda d: len(page.get_messages()) > 0
    )

    # Verify messages are loaded in chronological order
    messages_after = page.get_messages()
    assert len(messages_after) >= 2, (
        f"Expected at least 2 messages after refresh, got {len(messages_after)}"
    )

    # Verify messages maintain their order (user first, then assistant)
    # The first message should be the user's question
    user_msgs_after = [m for m in messages_after if m["role"] == "user"]
    assistant_msgs_after = [m for m in messages_after if m["role"] == "assistant"]

    assert len(user_msgs_after) >= 1, "User messages should persist after refresh"
    assert len(assistant_msgs_after) >= 1, "Assistant messages should persist after refresh"

    # Verify ordering: check that user message appears before assistant in the list
    first_user_idx = next(
        i for i, m in enumerate(messages_after) if m["role"] == "user"
    )
    first_assistant_idx = next(
        i for i, m in enumerate(messages_after) if m["role"] == "assistant"
    )
    assert first_user_idx < first_assistant_idx, (
        "User message should appear before assistant message (chronological order)"
    )


# ---------------------------------------------------------------------------
# Manual-Only Test Stub (CHT-10)
# ---------------------------------------------------------------------------


@pytest.mark.manual
@pytest.mark.chat
def test_CHT_10_ollama_offline():
    """CHT-10: When the Ollama service is stopped/offline, submitting a question
    displays an error message indicating the AI service is unavailable."""
    pytest.skip(
        reason="Requires stopping an external service (Ollama); not automatable "
        "within Selenium alone. Manual execution required to verify error handling "
        "when the AI backend is unavailable."
    )
