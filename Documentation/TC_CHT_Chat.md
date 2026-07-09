# Test Cases — Chat Assistant

**Module:** Module 4 — Chat Assistant (RAG Questions, Streaming, History)  
**Prefix:** CHT  
**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

**Pre-condition:** The backend is running. Ollama is running with `qwen3:1.7b` pulled. A forecast has been generated.
**Dependencies:** Ollama service must be reachable at `http://localhost:11434`.
**Test Priority:** High

---

### CHT-01: Submit a question — response streams in
**Summary:** Sending a question should trigger a streaming response from the assistant.
**Test Steps:**
1. Go to **Ask WATT-IF**.
2. Type: `What will my electricity usage be next month?`
3. Click **Ask** (or press Enter).
**Test Data:** Question: `What will my electricity usage be next month?`
**Expected Result:** The question appears in the chat. A response begins streaming in below it. The full response completes without error.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CHT-02: Ask about a specific forecast month
**Summary:** Asking about a specific month should return a relevant answer based on the forecast data.
**Test Steps:**
1. Ensure a 6-month forecast has been generated.
2. Type: `How much will my bill be in March 2026?`
3. Click **Ask**.
**Test Data:** Question: `How much will my bill be in March 2026?`
**Expected Result:** The response mentions a bill amount or kWh figure for March 2026. The answer is grounded in the forecast data.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CHT-03: Ask an out-of-scope question — politely declined
**Summary:** A question unrelated to electricity should be declined without crashing.
**Test Steps:**
1. Type: `Give me a recipe for adobo.`
2. Click **Ask**.
**Test Data:** Question: `Give me a recipe for adobo.`
**Expected Result:** The assistant politely declines and explains it can only answer questions about electricity and billing. No recipe is provided.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CHT-04: Submit empty message — Ask button is disabled
**Summary:** The Ask button should be disabled when the input is empty.
**Test Steps:**
1. Go to **Ask WATT-IF**.
2. Ensure the message field is empty.
3. Attempt to click **Ask**.
**Expected Result:** The Ask button is visually disabled (greyed out) and nothing happens when clicked. No empty message appears in the chat.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CHT-05: Submit a question at exactly 500 characters (boundary — maximum valid)
**Summary:** A question at the character limit should be accepted and processed normally.
**Test Steps:**
1. Type exactly 500 characters in the message field (use a repeated sentence to reach the limit).
2. Click **Ask**.
**Test Data:** A 500-character message about electricity
**Expected Result:** The message is sent and a response is generated. No character limit error is shown.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CHT-06: Type more than 500 characters — limit enforced
**Summary:** Typing beyond 500 characters should trigger a warning or prevent extra input.
**Test Steps:**
1. Paste a message longer than 500 characters into the input field.
2. Observe the character counter and field behavior.
**Test Data:** A message longer than 500 characters
**Expected Result:** Either the field stops accepting characters after 500, or the counter turns red and the Ask button is disabled.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CHT-07: Chat history persists after navigating away and returning
**Summary:** Messages should still be visible after leaving and coming back to the Ask page.
**Test Steps:**
1. Send a question and wait for the response to complete.
2. Navigate to a different page (e.g., Dashboard).
3. Navigate back to **Ask WATT-IF**.
**Expected Result:** The previous question and response are still visible in the chat. Nothing is lost on navigation.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CHT-08: Click Clear Chat — conversation is wiped
**Summary:** Clicking Clear Chat should remove all messages from the chat view and the database.
**Test Steps:**
1. Ensure at least one message exchange exists in the chat.
2. Click **Clear chat**.
**Expected Result:** All messages disappear. An empty-state prompt is shown (e.g., "Ask me about your electricity usage.").
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CHT-09: Chat remains empty after clearing and navigating away
**Summary:** A cleared chat should stay empty even after returning to the page.
**Test Steps:**
1. Clear the chat (CHT-08).
2. Navigate to a different page.
3. Navigate back to **Ask WATT-IF**.
**Expected Result:** The chat is still empty. No previous messages have reappeared.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CHT-10: Chat with Ollama offline — error message shown
**Summary:** If Ollama is not running, the app should show a clear error instead of hanging indefinitely.
**Test Steps:**
1. Stop the Ollama service.
2. Go to **Ask WATT-IF**.
3. Type a question and click **Ask**.
**Expected Result:** An error message appears (e.g., "LLM service unavailable. Please ensure Ollama is running."). The app does not hang or crash.
**Post-condition:** Restart Ollama after this test.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CHT-11: Previous chat history loads on page mount
**Summary:** Existing chat history from the database should load when the page first opens.
**Test Steps:**
1. Send at least 2 question-and-answer exchanges.
2. Close and reopen the browser (or hard-refresh with Ctrl+Shift+R).
3. Navigate to **Ask WATT-IF**.
**Expected Result:** The previous messages are loaded and displayed in the correct chronological order.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
