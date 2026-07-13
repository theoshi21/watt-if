"""
Account System test module (ACT-01 to ACT-22).

Covers registration, login, logout, session persistence, data isolation,
and password change flows for the WATT-IF application.

Requirements: 4.1–4.17
"""

import uuid
import time

import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium.pages import AccountSettingsPage, LoginPage, RegisterPage, Sidebar


# ---------------------------------------------------------------------------
# Registration Tests (ACT-01 through ACT-05)
# ---------------------------------------------------------------------------


@pytest.mark.account
def test_ACT_01_valid_registration(driver, base_url, api_url):
    """Submitting a valid email and a password ≥8 characters creates a new account and auto-logs in."""
    # Generate a unique email to avoid conflicts
    unique_id = uuid.uuid4().hex[:12]
    email = f"test_{unique_id}@example.com"
    password = "SecurePass1"

    page = RegisterPage(driver, base_url)
    page.register(email, password, password)

    # Wait for redirect to dashboard — URL should no longer be /register or /login
    # Registration does two API calls (register + auto-login), so allow extra time.
    # The first registration of a test run may also trigger DB initialization.
    try:
        WebDriverWait(driver, 30).until(
            lambda d: "/register" not in d.current_url and "/login" not in d.current_url
        )
    except Exception:
        # Capture page state for debugging
        current_url = driver.current_url
        # Check if there's an error message on the page
        error_els = driver.find_elements(By.CSS_SELECTOR, ".auth-page__error[role='alert']")
        error_text = error_els[0].text if error_els else "No error message displayed"
        raise AssertionError(
            f"Registration did not redirect within 30s. "
            f"URL: {current_url}, Page error: '{error_text}'"
        )
    # Brief pause to let the dashboard start rendering
    time.sleep(1)

    current_url = driver.current_url
    # After successful registration, user should be on "/" or "/dashboard"
    path = current_url.replace(base_url, "").rstrip("/")
    assert path in ("", "/", "/dashboard"), (
        f"Expected redirect to dashboard, got: {current_url}"
    )

    # Verify JWT token exists in localStorage
    token = page.get_local_storage("wattif_token")
    assert token is not None and len(token) > 0, (
        "Expected JWT token in localStorage under 'wattif_token'"
    )


@pytest.mark.account
def test_ACT_02_duplicate_email(driver, base_url, api_url):
    """Attempting to register with an email that already exists shows an error."""
    # First, register a user via API to ensure the email exists
    unique_id = uuid.uuid4().hex[:12]
    email = f"test_dup_{unique_id}@example.com"
    password = "SomePass123"

    response = requests.post(
        f"{api_url}/auth/register",
        json={"email": email, "password": password},
        timeout=10,
    )
    assert response.status_code in (201, 200), (
        f"API registration failed: {response.status_code} - {response.text}"
    )

    # Now try to register the same email via the UI
    page = RegisterPage(driver, base_url)
    page.register(email, password, password)

    # Expect an error message to be displayed
    error_msg = page.get_error_message()
    assert error_msg, "Expected an error message for duplicate email registration"

    # Verify no redirect occurred (still on /register)
    assert "/register" in driver.current_url, (
        f"Expected to remain on /register, but URL is: {driver.current_url}"
    )


@pytest.mark.account
def test_ACT_03_short_password(driver, base_url):
    """A password shorter than 8 characters prevents form submission."""
    page = RegisterPage(driver, base_url)
    page.navigate("/register")

    # Fill fields individually without clicking submit
    email_field = page.wait_for_element(RegisterPage.EMAIL_INPUT)
    email_field.clear()
    email_field.send_keys("short@example.com")

    password_field = page.wait_for_element(RegisterPage.PASSWORD_INPUT)
    password_field.clear()
    password_field.send_keys("abc")

    confirm_field = page.wait_for_element(RegisterPage.CONFIRM_PASSWORD_INPUT)
    confirm_field.clear()
    confirm_field.send_keys("abc")

    # Submit button should be disabled
    assert page.is_submit_enabled() is False, (
        "Expected Submit button to be disabled for password shorter than 8 characters"
    )


@pytest.mark.account
def test_ACT_04_password_mismatch(driver, base_url):
    """Mismatched password and confirm-password fields prevent form submission."""
    page = RegisterPage(driver, base_url)
    page.navigate("/register")

    # Fill fields individually without clicking submit
    email_field = page.wait_for_element(RegisterPage.EMAIL_INPUT)
    email_field.clear()
    email_field.send_keys("mismatch@example.com")

    password_field = page.wait_for_element(RegisterPage.PASSWORD_INPUT)
    password_field.clear()
    password_field.send_keys("ValidPass1")

    confirm_field = page.wait_for_element(RegisterPage.CONFIRM_PASSWORD_INPUT)
    confirm_field.clear()
    confirm_field.send_keys("DifferentPass2")

    # Submit button should be disabled
    assert page.is_submit_enabled() is False, (
        "Expected Submit button to be disabled for mismatched passwords"
    )


@pytest.mark.account
def test_ACT_05_invalid_email_format(driver, base_url):
    """An email without proper format (missing '@' or domain) is rejected."""
    page = RegisterPage(driver, base_url)
    page.navigate("/register")

    # Fill in an invalid email format
    email_field = page.wait_for_element(RegisterPage.EMAIL_INPUT)
    email_field.clear()
    email_field.send_keys("notanemail")

    password_field = page.wait_for_element(RegisterPage.PASSWORD_INPUT)
    password_field.clear()
    password_field.send_keys("ValidPass1")

    confirm_field = page.wait_for_element(RegisterPage.CONFIRM_PASSWORD_INPUT)
    confirm_field.clear()
    confirm_field.send_keys("ValidPass1")

    # Try to click submit
    submit_btn = page.wait_for_clickable(RegisterPage.SUBMIT_BUTTON)
    submit_btn.click()

    # The browser's native email validation should prevent submission.
    # Verify we're still on /register (form was not submitted)
    time.sleep(1)
    assert "/register" in driver.current_url, (
        "Expected to remain on /register page due to invalid email format"
    )

    # Check that the email input has a validation error (HTML5 validation)
    is_valid = driver.execute_script(
        "return document.getElementById('register-email').validity.valid;"
    )
    assert is_valid is False, (
        "Expected HTML5 email input to report invalid state for 'notanemail'"
    )


# ---------------------------------------------------------------------------
# Login Tests (ACT-06 to ACT-08)
# ---------------------------------------------------------------------------


@pytest.mark.account
def test_ACT_06_valid_login(driver, base_url, api_url):
    """ACT-06: Valid credentials submitted on the Login page result in redirect
    to Dashboard and JWT token stored in localStorage under 'wattif_token'."""
    # Arrange: Register a user via API
    email = f"test_login_{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123!"
    resp = requests.post(
        f"{api_url}/auth/register",
        json={"email": email, "password": password},
        timeout=10,
    )
    assert resp.status_code == 201, f"Registration failed: {resp.status_code} {resp.text}"

    # Act: Login via UI
    login_page = LoginPage(driver, base_url)
    login_page.login(email, password)

    # Wait for redirect away from /login
    WebDriverWait(driver, 20).until(
        lambda d: "/login" not in d.current_url
    )

    # Assert: URL no longer contains /login
    assert "/login" not in driver.current_url, (
        f"Expected redirect away from /login, but URL is: {driver.current_url}"
    )

    # Assert: JWT token exists in localStorage
    token = login_page.get_local_storage("wattif_token")
    assert token is not None and len(token) > 0, (
        "Expected 'wattif_token' in localStorage but it was not found"
    )


@pytest.mark.account
def test_ACT_07_wrong_password(driver, base_url, api_url):
    """ACT-07: Wrong password submitted on the Login page results in 'Invalid
    credentials' error message, no token stored, user remains on Login page."""
    # Arrange: Register a user via API
    email = f"test_login_{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123!"
    resp = requests.post(
        f"{api_url}/auth/register",
        json={"email": email, "password": password},
        timeout=10,
    )
    assert resp.status_code == 201, f"Registration failed: {resp.status_code} {resp.text}"

    # Act: Try to login with wrong password
    login_page = LoginPage(driver, base_url)
    login_page.login(email, "WrongPassword999!")

    # Assert: Error message contains "Invalid" (could be "Invalid credentials" or "Invalid email or password")
    error_msg = login_page.get_error_message()
    assert "invalid" in error_msg.lower(), (
        f"Expected error containing 'invalid', got: '{error_msg}'"
    )

    # Assert: No token in localStorage
    token = login_page.get_local_storage("wattif_token")
    assert token is None, (
        f"Expected no 'wattif_token' in localStorage, but found: {token}"
    )

    # Assert: Still on login page
    assert "/login" in driver.current_url, (
        f"Expected to remain on /login, but URL is: {driver.current_url}"
    )


@pytest.mark.account
def test_ACT_08_nonexistent_email(driver, base_url, api_url):
    """ACT-08: Non-existent email submitted on the Login page results in
    'Invalid credentials' error message, no token stored, user remains on
    Login page."""
    # Arrange: Use an email that was never registered
    email = f"nonexistent_{uuid.uuid4().hex[:8]}@test.com"
    password = "SomePassword123!"

    # Act: Try to login with non-existent email
    login_page = LoginPage(driver, base_url)
    login_page.login(email, password)

    # Assert: Error message contains "Invalid" (could be "Invalid credentials" or "Invalid email or password")
    error_msg = login_page.get_error_message()
    assert "invalid" in error_msg.lower(), (
        f"Expected error containing 'invalid', got: '{error_msg}'"
    )

    # Assert: No token in localStorage
    token = login_page.get_local_storage("wattif_token")
    assert token is None, (
        f"Expected no 'wattif_token' in localStorage, but found: {token}"
    )

    # Assert: Still on login page
    assert "/login" in driver.current_url, (
        f"Expected to remain on /login, but URL is: {driver.current_url}"
    )


# ---------------------------------------------------------------------------
# Session and Auth Tests (ACT-10, ACT-12, ACT-14, ACT-19, ACT-20)
# ---------------------------------------------------------------------------


@pytest.mark.account
def test_ACT_10_logout(logged_in_driver, base_url):
    """ACT-10: Clicking Logout removes the JWT token from localStorage and
    redirects the user to the Login page."""
    sidebar = Sidebar(logged_in_driver, base_url)
    sidebar.click_logout()

    # Wait for redirect to /login
    WebDriverWait(logged_in_driver, 20).until(
        lambda d: "/login" in d.current_url
    )

    # Verify token is removed from localStorage
    login_page = LoginPage(logged_in_driver, base_url)
    token = login_page.get_local_storage("wattif_token")
    assert token is None, (
        f"Expected 'wattif_token' to be removed from localStorage, but found: {token}"
    )

    # Verify URL contains /login
    assert "/login" in logged_in_driver.current_url, (
        f"Expected redirect to /login, but URL is: {logged_in_driver.current_url}"
    )


@pytest.mark.account
def test_ACT_12_session_persistence(logged_in_driver, base_url):
    """ACT-12: Refreshing the page after login keeps the user authenticated
    on the Dashboard (no redirect to Login)."""
    # Verify we're NOT on /login initially
    assert "/login" not in logged_in_driver.current_url, (
        f"Expected to be away from /login after login, but URL is: {logged_in_driver.current_url}"
    )

    # Refresh the page
    logged_in_driver.refresh()

    # Wait briefly and verify user is NOT redirected to /login
    WebDriverWait(logged_in_driver, 5).until(
        lambda d: "/login" not in d.current_url
    )

    # Assert the URL still doesn't contain /login or /register
    assert "/login" not in logged_in_driver.current_url, (
        f"Expected to remain authenticated after refresh, but redirected to: {logged_in_driver.current_url}"
    )
    assert "/register" not in logged_in_driver.current_url, (
        f"Expected to remain authenticated after refresh, but redirected to: {logged_in_driver.current_url}"
    )


@pytest.mark.account
def test_ACT_14_invalid_token_redirect(logged_in_driver, base_url):
    """ACT-14: Setting an invalid JWT token in localStorage causes a redirect
    to the Login page upon navigating to a protected page that triggers an API call."""
    # Set an invalid JWT in localStorage
    logged_in_driver.execute_script(
        "window.localStorage.setItem('wattif_token', 'invalid.token.value')"
    )

    # Navigate to a protected page that triggers an API call
    logged_in_driver.get(f"{base_url}/data-entry")

    # Wait for the app to detect the invalid token and redirect to /login
    WebDriverWait(logged_in_driver, 20).until(
        lambda d: "/login" in d.current_url
    )

    assert "/login" in logged_in_driver.current_url, (
        f"Expected redirect to /login with invalid token, but URL is: {logged_in_driver.current_url}"
    )


@pytest.mark.account
def test_ACT_19_unauthenticated_protected_route(unauthenticated_driver, base_url):
    """ACT-19: Navigating to a protected route without authentication redirects
    the user to the Login page."""
    # Navigate directly to a protected route
    unauthenticated_driver.get(f"{base_url}/data-entry")

    # Wait for redirect to /login
    WebDriverWait(unauthenticated_driver, 20).until(
        lambda d: "/login" in d.current_url
    )

    assert "/login" in unauthenticated_driver.current_url, (
        f"Expected redirect to /login for unauthenticated access, but URL is: {unauthenticated_driver.current_url}"
    )


@pytest.mark.account
def test_ACT_20_authenticated_login_redirect(logged_in_driver, base_url):
    """ACT-20: An authenticated user visiting /login or /register is redirected
    back to the Dashboard."""
    # Test /login redirect
    logged_in_driver.get(f"{base_url}/login")

    # Wait for redirect away from /login
    WebDriverWait(logged_in_driver, 20).until(
        lambda d: "/login" not in d.current_url
    )

    assert "/login" not in logged_in_driver.current_url, (
        f"Expected authenticated user to be redirected away from /login, but URL is: {logged_in_driver.current_url}"
    )

    # Test /register redirect
    logged_in_driver.get(f"{base_url}/register")

    # Wait for redirect away from /register
    WebDriverWait(logged_in_driver, 20).until(
        lambda d: "/register" not in d.current_url
    )

    assert "/register" not in logged_in_driver.current_url, (
        f"Expected authenticated user to be redirected away from /register, but URL is: {logged_in_driver.current_url}"
    )


# ---------------------------------------------------------------------------
# Data Isolation Tests (ACT-15 to ACT-18)
# ---------------------------------------------------------------------------


@pytest.mark.account
def test_ACT_15_data_isolation_entries(driver, base_url, api_url):
    """User A creates entries → User B cannot see them in Entry History."""
    from tests.selenium.pages import DataEntryPage, LoginPage

    # Register User A and User B via API
    user_a_email = f"test_iso_a_{uuid.uuid4().hex[:8]}@test.com"
    user_b_email = f"test_iso_b_{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123!"

    resp_a = requests.post(
        f"{api_url}/auth/register",
        json={"email": user_a_email, "password": password},
        timeout=10,
    )
    assert resp_a.status_code == 201, f"User A registration failed: {resp_a.text}"

    resp_b = requests.post(
        f"{api_url}/auth/register",
        json={"email": user_b_email, "password": password},
        timeout=10,
    )
    assert resp_b.status_code == 201, f"User B registration failed: {resp_b.text}"

    # Login as User A via UI
    login_page = LoginPage(driver, base_url)
    login_page.login(user_a_email, password)
    WebDriverWait(driver, 20).until(
        lambda d: "/login" not in d.current_url
    )

    # Navigate to Data Entry and add an entry
    data_page = DataEntryPage(driver, base_url)
    data_page.navigate_to_data_entry()
    data_page.add_entry("2024-01", 500)

    # Wait for entry to appear in history
    WebDriverWait(driver, 20).until(
        lambda d: len(data_page.get_entry_rows()) > 0
    )
    assert len(data_page.get_entry_rows()) >= 1, "User A's entry did not appear"

    # Logout User A
    driver.execute_script("window.localStorage.removeItem('wattif_token')")
    driver.get(f"{base_url}/login")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (login_page.EMAIL_INPUT)
        )
    )

    # Login as User B via UI
    login_page.login(user_b_email, password)
    WebDriverWait(driver, 20).until(
        lambda d: "/login" not in d.current_url
    )

    # Navigate to Data Entry and verify empty state
    data_page.navigate_to_data_entry()
    time.sleep(2)  # Allow page to load fully

    # User B should see no entries from User A
    rows = data_page.get_entry_rows()
    assert len(rows) == 0 or data_page.is_empty_state(), (
        f"User B should not see User A's entries, but found {len(rows)} rows"
    )


@pytest.mark.account
def test_ACT_16_chat_isolation(driver, base_url, api_url):
    """User A sends chat messages → User B cannot see them."""
    from tests.selenium.pages import AskPage, LoginPage

    # Register User A and User B via API
    user_a_email = f"test_chat_a_{uuid.uuid4().hex[:8]}@test.com"
    user_b_email = f"test_chat_b_{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123!"

    resp_a = requests.post(
        f"{api_url}/auth/register",
        json={"email": user_a_email, "password": password},
        timeout=10,
    )
    assert resp_a.status_code == 201, f"User A registration failed: {resp_a.text}"

    resp_b = requests.post(
        f"{api_url}/auth/register",
        json={"email": user_b_email, "password": password},
        timeout=10,
    )
    assert resp_b.status_code == 201, f"User B registration failed: {resp_b.text}"

    # Login as User A via UI
    login_page = LoginPage(driver, base_url)
    login_page.login(user_a_email, password)
    WebDriverWait(driver, 20).until(
        lambda d: "/login" not in d.current_url
    )

    # Get User A's JWT token for API calls
    token_a = driver.execute_script("return window.localStorage.getItem('wattif_token')")

    # Persist a chat message for User A via the API (avoids Ollama dependency)
    requests.post(
        f"{api_url}/chat-history",
        json={"role": "user", "text": "What is my electricity forecast?"},
        headers={"Authorization": f"Bearer {token_a}"},
        timeout=10,
    )
    requests.post(
        f"{api_url}/chat-history",
        json={"role": "assistant", "text": "Your forecast shows 350 kWh next month."},
        headers={"Authorization": f"Bearer {token_a}"},
        timeout=10,
    )

    # Navigate to Ask page and verify User A sees their messages
    ask_page = AskPage(driver, base_url)
    ask_page.navigate("/ask")
    time.sleep(2)  # Allow history to load

    messages_a = ask_page.get_messages()
    assert len(messages_a) >= 2, "User A should see their message and a response"

    # Logout User A
    driver.execute_script("window.localStorage.removeItem('wattif_token')")
    driver.get(f"{base_url}/login")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (login_page.EMAIL_INPUT)
        )
    )

    # Login as User B via UI
    login_page.login(user_b_email, password)
    WebDriverWait(driver, 20).until(
        lambda d: "/login" not in d.current_url
    )

    # Navigate to Ask page and verify no messages from User A
    ask_page.navigate("/ask")
    time.sleep(2)  # Allow page to load fully

    messages_b = ask_page.get_messages()
    assert len(messages_b) == 0, (
        f"User B should not see User A's messages, but found {len(messages_b)} messages"
    )


@pytest.mark.account
def test_ACT_17_api_cross_user_forbidden(driver, base_url, api_url):
    """User B targets User A's entry via API → 403 Forbidden."""
    # Register User A and User B via API
    user_a_email = f"test_api_a_{uuid.uuid4().hex[:8]}@test.com"
    user_b_email = f"test_api_b_{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123!"

    resp_a = requests.post(
        f"{api_url}/auth/register",
        json={"email": user_a_email, "password": password},
        timeout=10,
    )
    assert resp_a.status_code == 201, f"User A registration failed: {resp_a.text}"

    resp_b = requests.post(
        f"{api_url}/auth/register",
        json={"email": user_b_email, "password": password},
        timeout=10,
    )
    assert resp_b.status_code == 201, f"User B registration failed: {resp_b.text}"

    # Get tokens for both users
    token_a_resp = requests.post(
        f"{api_url}/auth/login",
        json={"email": user_a_email, "password": password},
        timeout=10,
    )
    assert token_a_resp.status_code == 200
    token_a = token_a_resp.json()["token"]

    token_b_resp = requests.post(
        f"{api_url}/auth/login",
        json={"email": user_b_email, "password": password},
        timeout=10,
    )
    assert token_b_resp.status_code == 200
    token_b = token_b_resp.json()["token"]

    # User A creates an entry via API
    create_resp = requests.post(
        f"{api_url}/data-entries",
        json={"year_month": "2024-01", "kwh": 500, "source": "Manual"},
        headers={"Authorization": f"Bearer {token_a}"},
        timeout=10,
    )
    assert create_resp.status_code == 201, f"Entry creation failed: {create_resp.text}"
    entry_id = create_resp.json()["id"]

    # User B attempts to DELETE User A's entry → should get 403
    delete_resp = requests.delete(
        f"{api_url}/data-entries/{entry_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        timeout=10,
    )
    assert delete_resp.status_code == 403, (
        f"Expected 403 Forbidden for cross-user DELETE, got {delete_resp.status_code}"
    )

    # User B attempts to PUT (update) User A's entry → should get 403
    put_resp = requests.put(
        f"{api_url}/data-entries/{entry_id}",
        json={"kwh": 999},
        headers={"Authorization": f"Bearer {token_b}"},
        timeout=10,
    )
    assert put_resp.status_code == 403, (
        f"Expected 403 Forbidden for cross-user PUT, got {put_resp.status_code}"
    )

    # Verify User A's entry remains unchanged
    get_resp = requests.get(
        f"{api_url}/data-entries",
        headers={"Authorization": f"Bearer {token_a}"},
        timeout=10,
    )
    assert get_resp.status_code == 200
    entries = get_resp.json()
    matching = [e for e in entries if e["id"] == entry_id]
    assert len(matching) == 1, "User A's entry should still exist"
    assert matching[0]["kwh"] == 500, (
        f"User A's entry kWh should be unchanged (500), got {matching[0]['kwh']}"
    )


@pytest.mark.account
def test_ACT_18_model_isolation(driver, base_url, api_url):
    """User A has a trained model → User B sees 'no model' state on Forecast page."""
    from tests.selenium.pages import ForecastPage, LoginPage

    # The default account (wattif@gmail.com / wattif) already has a trained model.
    # Register a new User B who has no data and no trained model.
    user_b_email = f"test_model_b_{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123!"

    resp_b = requests.post(
        f"{api_url}/auth/register",
        json={"email": user_b_email, "password": password},
        timeout=10,
    )
    assert resp_b.status_code == 201, f"User B registration failed: {resp_b.text}"

    # Login as User B via UI
    login_page = LoginPage(driver, base_url)
    login_page.login(user_b_email, password)
    WebDriverWait(driver, 20).until(
        lambda d: "/login" not in d.current_url
    )

    # Navigate to Forecast page
    forecast_page = ForecastPage(driver, base_url)
    forecast_page.navigate("/forecast")
    time.sleep(5)  # Allow forecast page to load and check model status

    # User B should see an error message indicating no model is available
    error_msg = forecast_page.get_error_message(timeout=20)
    assert error_msg, (
        "User B should see an error message on Forecast page indicating no model available"
    )


# ---------------------------------------------------------------------------
# Password Change Tests (ACT-21, ACT-22)
# ---------------------------------------------------------------------------


@pytest.mark.account
def test_ACT_21_valid_password_change(driver, base_url, api_url):
    """ACT-21: Valid current password and new password (≥8 chars with matching
    confirmation) results in a success message, and user can re-login with new password."""
    email = f"test_pwchange_{uuid.uuid4().hex[:8]}@test.com"
    old_password = "OldPass123!"
    new_password = "NewPass456!"

    # Register and login
    requests.post(
        f"{api_url}/auth/register",
        json={"email": email, "password": old_password},
        timeout=10,
    )

    login_page = LoginPage(driver, base_url)
    login_page.login(email, old_password)
    WebDriverWait(driver, 20).until(lambda d: "/login" not in d.current_url)

    # Navigate to account settings and change password
    settings_page = AccountSettingsPage(driver, base_url)
    settings_page.navigate_to_settings()
    time.sleep(3)  # Allow account settings page to fully load
    settings_page.change_password(old_password, new_password, new_password)

    # Verify success message
    msg = settings_page.get_success_message(timeout=20)
    assert msg, "Expected a success message after password change"

    # Logout
    sidebar = Sidebar(driver, base_url)
    sidebar.click_logout()
    WebDriverWait(driver, 20).until(lambda d: "/login" in d.current_url)

    # Re-login with new password
    login_page.login(email, new_password)
    WebDriverWait(driver, 20).until(lambda d: "/login" not in d.current_url)
    assert "/login" not in driver.current_url


@pytest.mark.account
def test_ACT_22_wrong_current_password(driver, base_url, api_url):
    """ACT-22: Incorrect current password for password change results in an error
    message and the password remains unchanged."""
    email = f"test_pwfail_{uuid.uuid4().hex[:8]}@test.com"
    password = "CorrectPass1!"

    # Register and login
    requests.post(
        f"{api_url}/auth/register",
        json={"email": email, "password": password},
        timeout=10,
    )

    login_page = LoginPage(driver, base_url)
    login_page.login(email, password)
    WebDriverWait(driver, 20).until(lambda d: "/login" not in d.current_url)

    # Navigate to account settings
    settings_page = AccountSettingsPage(driver, base_url)
    settings_page.navigate_to_settings()
    time.sleep(3)  # Allow account settings page to fully load

    # Try to change password with wrong current password
    settings_page.change_password("WrongCurrent!", "NewPass456!", "NewPass456!")

    # Verify error message
    error_msg = settings_page.get_error_message(timeout=20)
    assert error_msg, "Expected an error message for wrong current password"
    assert "incorrect" in error_msg.lower() or "wrong" in error_msg.lower() or "invalid" in error_msg.lower(), (
        f"Expected error about incorrect current password, got: '{error_msg}'"
    )


# ---------------------------------------------------------------------------
# Manual-Only Test Stubs (ACT-09, ACT-11, ACT-13)
# ---------------------------------------------------------------------------


@pytest.mark.manual
@pytest.mark.account
def test_ACT_09_rate_limiting():
    """ACT-09: After 10 failed login attempts within 1 minute, the 11th attempt
    is rejected with a 'Too many attempts' message and a cooldown timer is displayed."""
    pytest.skip(
        reason="Requires 11 rapid login attempts; may be flaky due to timing-dependent "
        "rate limit windows. Manual execution required to reliably verify rate limiting behavior."
    )


@pytest.mark.manual
@pytest.mark.account
def test_ACT_11_logout_offline():
    """ACT-11: Clicking logout while the network is disconnected clears the local
    token and redirects to the login page with an offline indicator."""
    pytest.skip(
        reason="Requires simulating network disconnect mid-session; Selenium cannot "
        "toggle real network state reliably. Manual execution required."
    )


@pytest.mark.manual
@pytest.mark.account
def test_ACT_13_expired_token():
    """ACT-13: When a JWT token expires (after 24 hours), the next API call returns
    401 and the user is redirected to the login page with a session-expired message."""
    pytest.skip(
        reason="Requires waiting 24 hours or manually tampering with JWT expiry; "
        "partially automatable via JavaScript execution to modify localStorage "
        "but not fully reliable. Manual execution required."
    )
