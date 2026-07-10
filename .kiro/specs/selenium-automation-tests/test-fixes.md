# Test Fixes Reference

This document tracks known issues discovered during Task 14 (final checkpoint) that apply across all test modules. Reference this before running or debugging any test module.

---

## Fix 1: Error Message Wording Mismatch

**Problem:** Tests assert exact error text like `"invalid credentials"` but the frontend displays `"Invalid email or password"`.

**Root Cause:** The frontend's LoginPage.tsx catches the API error and shows its own generic message (`'Invalid email or password'`) rather than forwarding the backend's `"Invalid credentials"` detail.

**Fix Pattern:** Use partial/flexible matching instead of exact strings:
```python
# BAD — brittle, breaks if wording changes
assert "invalid credentials" in error_msg.lower()

# GOOD — checks the key word that conveys meaning
assert "invalid" in error_msg.lower()
```

**Applies to:** Any test that checks login error messages (ACT-07, ACT-08, and any test using `LoginPage.get_error_message()`).

---

## Fix 2: HTML5 Email Validation Blocks Form Submission

**Problem:** Tests that submit invalid email formats (e.g., `"notanemail"`) via `<input type="email">` never reach the backend because the browser's native validation blocks submission.

**Root Cause:** HTML5 `type="email"` inputs have built-in validation. Selenium's `click()` on submit triggers the browser tooltip "Please include an '@' in the email address" rather than a custom app error.

**Fix Pattern:** Check HTML5 validity API instead of expecting a custom error message:
```python
# Navigate, fill fields, click submit
submit_btn.click()
time.sleep(1)

# Verify form was NOT submitted (still on same page)
assert "/register" in driver.current_url

# Check HTML5 validation state
is_valid = driver.execute_script(
    "return document.getElementById('register-email').validity.valid;"
)
assert is_valid is False
```

**Applies to:** ACT-05, and any test submitting invalid email to a `type="email"` input.

---

## Fix 3: Page Load Timeouts (API Latency)

**Problem:** Tests timeout waiting for elements on pages that make API calls on load (forecast, account settings, dashboard).

**Root Cause:** The backend takes time to respond, especially for forecast (model inference), health checks (Ollama ping), and settings (multiple DB queries).

**Fix Pattern:**
- Default `wait_for_element` timeout increased to 15s (BasePage)
- All `WebDriverWait` in test_account.py increased to 20s
- Add `time.sleep(3-5)` after navigating to data-heavy pages before interacting
- Session-level health check fixture waits up to 60s for backend to be operational

**Applies to:** Any test navigating to `/forecast`, `/account`, `/` (dashboard), or pages that fetch data on mount.

---

## Fix 4: ChromeDriver Download Latency

**Problem:** `ChromeDriverManager().install()` called per test caused 3+ minute gaps between tests.

**Root Cause:** webdriver-manager hits the network on every call to verify/download the driver.

**Fix Pattern:** Removed webdriver-manager entirely. Using Selenium 4's built-in Selenium Manager:
```python
# Just use webdriver.Chrome(options=...) — no Service or ChromeDriverManager needed
browser = webdriver.Chrome(options=chrome_options)
```

**Applies to:** conftest.py driver fixture (already fixed globally).

---

## Fix 5: Backend Must Be Running

**Problem:** Tests fail with `ConnectionError: No connection could be made` if backend isn't started.

**Fix Pattern:** Session-scoped `_wait_for_backend` fixture in conftest.py polls `/health` for up to 60s before any tests execute. If backend never responds, all tests skip.

**Applies to:** All tests (global fixture, already applied).

---

## General Rules for All Test Modules

1. **Don't assert exact error wording** — use partial matches (`"invalid" in msg.lower()`) since frontend messages may differ from backend.
2. **Allow 15-20s for element waits** — pages with API calls need breathing room.
3. **Add sleep after navigation to data-heavy pages** — forecast, dashboard, settings, data entry (after upload/train).
4. **Browser-native validation** — any `type="email"`, `type="number"`, `required` attributes will block form submission before the app logic runs. Test these via HTML5 validity API.
5. **Each test is self-contained** — registers its own user, doesn't depend on prior tests running.
