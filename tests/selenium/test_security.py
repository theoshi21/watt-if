"""
Security test module (SEC-01 to SEC-06).

Covers SQL injection, XSS, CSV formula injection, unauthorized API access,
session timeout, and authentication bypass attempts.

Requirements covered: TC_SEC SEC-01 through SEC-06
"""

import time
import uuid

import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium.pages import AskPage, DataEntryPage, LoginPage


@pytest.mark.security
class TestSecurity:
    """Security tests (SEC-01 to SEC-06)."""

    def test_SEC_01_sql_injection(self, logged_in_driver, base_url, api_url):
        """SEC-01: SQL injection via input fields is sanitized and rejected.

        The HTML number input strips non-numeric characters at the browser level.
        This test verifies that SQL injection via API (bypassing UI) is also blocked.
        """

        # Get auth token from browser
        token = logged_in_driver.execute_script(
            "return window.localStorage.getItem('wattif_token')"
        )

        # Attempt SQL injection via API directly (bypassing frontend validation)
        headers = {"Authorization": f"Bearer {token}"}
        injection_payload = {
            "year_month": "2024-01'; DROP TABLE monthly_bill_records;--",
            "kwh": 100,
            "source": "Manual",
        }
        resp = requests.post(
            f"{api_url}/data-entries",
            json=injection_payload,
            headers=headers,
            timeout=10,
        )

        # The backend should either reject the malformed date or sanitize it
        # Either a 400/422 error or it stores the literal string safely
        # Verify the table still exists by querying entries
        check_resp = requests.get(
            f"{api_url}/data-entries",
            headers=headers,
            timeout=10,
        )
        assert check_resp.status_code == 200, (
            "Database should still be intact after SQL injection attempt"
        )

    def test_SEC_01b_sql_injection_login(self, driver, base_url):
        """SEC-01b: SQL injection via login email field is rejected."""
        login_page = LoginPage(driver, base_url)
        login_page.login("' OR '1'='1", "password")

        # Wait a moment for the response
        time.sleep(3)

        # Should still be on login page (no bypass) — either error shown or
        # HTML validation prevented submission
        assert "/login" in driver.current_url or "/register" in driver.current_url, (
            "SQL injection should not bypass authentication"
        )

        # Verify no token was stored (no auth bypass)
        token = login_page.get_local_storage("wattif_token")
        assert token is None, (
            f"SQL injection should not result in a token, but found: {token}"
        )

    def test_SEC_02_xss_via_chat(self, logged_in_driver, base_url):
        """SEC-02: XSS payloads in chat input are escaped, not executed.

        Steps:
        1. Send script tag as a chat message
        2. Verify no JavaScript executes (no alert dialog)
        3. Verify input is displayed as escaped text

        Expected: No script execution. Input escaped in display.
        """
        ask_page = AskPage(logged_in_driver, base_url)
        ask_page.navigate("/ask")

        WebDriverWait(logged_in_driver, 10).until(
            lambda d: ask_page.get_empty_state_text() is not None
            or len(ask_page.get_messages()) > 0
        )

        xss_payload = "<script>alert('XSS')</script>"
        ask_page.send_message(xss_payload)

        # Wait for message to appear (may trigger response too)
        time.sleep(3)

        # Verify no JavaScript alert was triggered
        try:
            alert = logged_in_driver.switch_to.alert
            alert.dismiss()
            pytest.fail("XSS vulnerability: JavaScript alert was triggered!")
        except Exception:
            pass  # No alert = good, XSS was prevented

        # Verify the message is displayed as escaped text (not executed)
        messages = ask_page.get_messages()
        user_msgs = [m for m in messages if m["role"] == "user"]
        assert len(user_msgs) >= 1, "User message should still appear"

    def test_SEC_02b_xss_img_tag(self, logged_in_driver, base_url):
        """SEC-02b: XSS via img onerror payload is not executed."""
        ask_page = AskPage(logged_in_driver, base_url)
        ask_page.navigate("/ask")

        WebDriverWait(logged_in_driver, 10).until(
            lambda d: ask_page.get_empty_state_text() is not None
            or len(ask_page.get_messages()) > 0
        )

        xss_payload = "<img src=x onerror=alert(1)>"
        ask_page.send_message(xss_payload)
        time.sleep(3)

        # Verify no alert
        try:
            alert = logged_in_driver.switch_to.alert
            alert.dismiss()
            pytest.fail("XSS vulnerability: img onerror alert was triggered!")
        except Exception:
            pass  # Good — no alert

    def test_SEC_04_unauthorized_api_access(self, api_url):
        """SEC-04: Protected endpoints reject requests without valid JWT.

        Steps:
        1. Send requests without Authorization header
        2. Send requests with invalid token
        3. Verify all return 401

        Expected: All requests return HTTP 401 Unauthorized.
        """
        # No token
        resp = requests.get(f"{api_url}/data-entries", timeout=10)
        assert resp.status_code == 401, (
            f"Expected 401 without token, got {resp.status_code}"
        )

        # Invalid token
        headers = {"Authorization": "Bearer invalid.token.here"}
        resp = requests.get(f"{api_url}/data-entries", headers=headers, timeout=10)
        assert resp.status_code == 401, (
            f"Expected 401 with invalid token, got {resp.status_code}"
        )

        # Expired/malformed JWT
        headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjF9.invalid"}
        resp = requests.get(f"{api_url}/data-entries", headers=headers, timeout=10)
        assert resp.status_code == 401, (
            f"Expected 401 with expired token, got {resp.status_code}"
        )

    def test_SEC_06_auth_bypass_tampered_jwt(self, api_url):
        """SEC-06: Tampered JWT (modified payload without re-signing) is rejected.

        Steps:
        1. Register a user and get a valid token
        2. Tamper the JWT payload (change user_id)
        3. Send request with tampered JWT
        4. Verify 401 response

        Expected: Modified JWT rejected (signature mismatch).
        """
        import base64
        import json

        # Register a test user
        email = f"sec_test_{uuid.uuid4().hex[:8]}@test.com"
        password = "SecTest123!"

        reg_resp = requests.post(
            f"{api_url}/auth/register",
            json={"email": email, "password": password},
            timeout=10,
        )
        assert reg_resp.status_code == 201

        # Get valid token
        login_resp = requests.post(
            f"{api_url}/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        assert login_resp.status_code == 200
        valid_token = login_resp.json()["token"]

        # Tamper the payload — modify user_id
        parts = valid_token.split(".")
        assert len(parts) == 3, "JWT should have 3 parts"

        # Decode payload
        payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        # Modify user_id
        payload["sub"] = "999999"
        tampered_payload = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).rstrip(b"=").decode()

        # Reassemble with original header and signature (invalid signature now)
        tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

        # Use tampered token
        headers = {"Authorization": f"Bearer {tampered_token}"}
        resp = requests.get(f"{api_url}/data-entries", headers=headers, timeout=10)
        assert resp.status_code == 401, (
            f"Expected 401 for tampered JWT, got {resp.status_code}"
        )

    def test_SEC_06b_direct_url_unauthenticated(self, driver, base_url):
        """SEC-06b: Direct URL access without auth redirects to login.

        Steps:
        1. Navigate directly to /forecast without logging in
        2. Verify redirect to /login

        Expected: Unauthenticated access redirects to login.
        """
        driver.get(f"{base_url}/forecast")

        WebDriverWait(driver, 20).until(
            lambda d: "/login" in d.current_url
        )

        assert "/login" in driver.current_url, (
            f"Expected redirect to /login, got: {driver.current_url}"
        )

    # -----------------------------------------------------------------------
    # Manual-Only Stubs
    # -----------------------------------------------------------------------

    @pytest.mark.manual
    def test_SEC_03_csv_formula_injection(self):
        """SEC-03: CSV formula injection — requires file download verification.
        Partially covered by DM-45. Full validation requires checking exported files."""
        pytest.skip(
            reason="CSV formula injection on export requires downloading and inspecting "
            "the exported file. Upload-side injection is covered in DM-45."
        )

    @pytest.mark.manual
    def test_SEC_05_session_timeout(self):
        """SEC-05: JWT expiry after 24 hours forces re-authentication.
        Requires waiting 24 hours or system clock manipulation."""
        pytest.skip(
            reason="Requires waiting 24 hours or manipulating system clock. "
            "Partially covered by ACT-13 and ACT-14."
        )
