# Test Fixes Reference

This document tracks known issues discovered during test automation that apply across all test modules. Reference this before running or debugging any test module.

**Status:** All fixes below have been applied globally to all test modules and page objects.

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

## Fix 6: No Success Toast for Manual Entry (Data Management)

**Problem:** All DM-01 through DM-12 tests called `page.get_success_message()` after submitting a manual entry, but the page never renders a success toast or `[role='status']` element for manual form submissions.

**Root Cause:** The `DataEntryPage.tsx` form submission handler (`handleSubmit`) simply prepends the new row to the table state and clears the form fields. It does NOT display any toast, banner, or `role="status"` element. Success is communicated solely by the new row appearing in the Entry History table.

The `SUCCESS_MESSAGE` locator (`.toast--success, [role='status'], .success-message`) was waiting for an element that never appears, causing a `TimeoutException` on every manual entry test.

**Note:** The `UploadPanel` component DOES render `role="status"` on success — so CSV upload tests (`get_success_message()`) work correctly. Only manual entry tests are affected.

**Fix Pattern:** Verify success by checking the entry appeared in the table:
```python
# BAD — times out, no success toast exists for manual entry
success_msg = page.get_success_message()
assert success_msg

# GOOD — verify the entry appeared in the table
time.sleep(2)  # Wait for API response
rows = page.get_entry_rows()
assert len(rows) > initial_rows, "Expected a new row in entry history"
```

**Applies to:** DM-01, DM-06, DM-07, DM-09, DM-10, DM-12, and DM-22 through DM-31 (edit/delete tests that create entries as setup).

---

## Fix 7: kWh Input Max Boundary Mismatch

**Problem:** Tests DM-07 and DM-08 assumed the maximum valid kWh was 1,000,000 (matching the backend schema `le=1_000_000`), but the frontend input clamps at **99,999**.

**Root Cause:** The `DataEntryPage.tsx` kWh input has:
- `max={99999}` HTML attribute
- An `onChange` handler that clamps: `if (!isNaN(num) && num > 99999) { setKwh('99999'); return }`

So typing any value above 99,999 gets silently clamped to 99,999 by the UI before form submission. The backend's `le=1_000_000` constraint is unreachable from the UI.

**Fix Pattern:**
```python
# DM-07: Test the actual UI maximum (99999, not 1000000)
page.add_entry("2030-07", 99999)
time.sleep(2)
rows = page.get_entry_rows()
assert len(rows) > initial_rows

# DM-08: Verify the input gets clamped rather than expecting an error
kwh_input = page.wait_for_element(page.KWH_INPUT)
kwh_input.clear()
kwh_input.send_keys("100001")
time.sleep(0.5)
actual_value = kwh_input.get_attribute("value")
assert actual_value == "99999"  # Clamped by onChange handler
```

**Applies to:** DM-07 (maximum valid), DM-08 (exceeds maximum).

---

## Fix 8: Registration Timeout (First Test of Session)

**Problem:** ACT-01 (valid registration) times out waiting for redirect after form submission, while all other auth tests pass.

**Root Cause:** Registration performs two sequential API calls:
1. `POST /auth/register` — bcrypt hash with cost factor 12 (~300ms)
2. `POST /auth/login` (auto-login) — bcrypt verify (~300ms)

On the first test of a session, the backend may still be warming up (DB initialization, first import of pipeline modules). Combined with the frontend's own `initAuth()` check (`GET /auth/has-users`), total time can exceed 20s.

**Fix Pattern:**
```python
# Increase timeout to 30s for registration (two API calls + backend warmup)
try:
    WebDriverWait(driver, 30).until(
        lambda d: "/register" not in d.current_url and "/login" not in d.current_url
    )
except Exception:
    # Capture diagnostics: current URL and any visible error
    error_els = driver.find_elements(By.CSS_SELECTOR, ".auth-page__error[role='alert']")
    error_text = error_els[0].text if error_els else "No error message displayed"
    raise AssertionError(
        f"Registration did not redirect within 30s. URL: {current_url}, Error: '{error_text}'"
    )
```

**Applies to:** ACT-01 (first registration test), and potentially any test that is the first to hit the backend in a session.

---

## General Rules for All Test Modules

1. **Don't assert exact error wording** — use partial matches (`"invalid" in msg.lower()`) since frontend messages may differ from backend.
2. **Allow 15-20s for element waits** — pages with API calls need breathing room.
3. **Add sleep after navigation to data-heavy pages** — forecast, dashboard, settings, data entry (after upload/train).
4. **Browser-native validation** — any `type="email"`, `type="number"`, `required` attributes will block form submission before the app logic runs. Test these via HTML5 validity API.
5. **Each test is self-contained** — registers its own user, doesn't depend on prior tests running.
6. **Don't assume success toasts exist** — the manual entry form confirms success by showing the new row, not a toast. CSV upload does show `role="status"`. Always verify against what the actual frontend renders.
7. **Test against the UI boundary, not the API boundary** — the frontend may clamp or transform values before they reach the backend (e.g., kWh clamped to 99999 in the input handler).
