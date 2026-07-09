"""
Shared pytest fixtures and hooks for the WATT-IF Selenium automation test suite.

Provides:
- WebDriver lifecycle management (ChromeDriver via webdriver-manager)
- Screenshot-on-failure with HTML report embedding
- Authentication fixtures (logged_in_driver, default_account_driver, etc.)
- Test data fixtures (test_csv_path)

Requirements: 1.2, 1.7, 2.1–2.7, 3.1–3.5, 17.3, 17.5, 17.6
"""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Generator

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# ---------------------------------------------------------------------------
# CLI Options
# ---------------------------------------------------------------------------


def pytest_addoption(parser):
    """Add --headless CLI option for running Chrome without a visible window."""
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run Chrome in headless mode (no visible browser window).",
    )


# ---------------------------------------------------------------------------
# Session-Scoped Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _wait_for_backend(api_url):
    """Wait for the backend API to become operational before running any tests.

    Polls the /health endpoint for up to 60 seconds. If the backend doesn't
    respond with status 'ok', all tests are skipped.
    """
    url = f"{api_url}/health"
    max_wait = 60
    interval = 3
    elapsed = 0

    while elapsed < max_wait:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                return  # Backend is ready
        except (requests.ConnectionError, requests.Timeout):
            pass
        time.sleep(interval)
        elapsed += interval

    pytest.skip(f"Backend not operational after {max_wait}s (tried {url})")


@pytest.fixture(scope="session")
def base_url() -> str:
    """Application base URL from BASE_URL env var or default http://localhost:5173."""
    return os.environ.get("BASE_URL", "http://localhost:5173")


@pytest.fixture(scope="session")
def api_url() -> str:
    """API base URL from API_URL env var or default http://localhost:8000."""
    return os.environ.get("API_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def test_csv_path() -> Path:
    """Path to data/synthetic_2022_2025.csv for upload tests."""
    csv_path = Path(__file__).resolve().parents[2] / "data" / "synthetic_2022_2025.csv"
    assert csv_path.exists(), f"Test CSV not found at {csv_path}"
    return csv_path


# ---------------------------------------------------------------------------
# WebDriver Fixture (function-scoped)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def driver(request) -> Generator[webdriver.Chrome, None, None]:
    """
    Function-scoped ChromeDriver instance.

    - Uses Selenium's built-in driver manager (no network calls to CDN)
    - Window size 1920x1080 (Req 2.2)
    - Implicit wait 0s; tests use explicit waits with 10s default (Req 2.3)
    - Disables automation detection flags (Req 2.4)
    - Captures screenshot on failure (Req 2.5 — handled by pytest_runtest_makereport)
    - Quits browser on teardown (Req 2.6)
    - Skips tests if WebDriver init fails (Req 2.7)
    """
    chrome_options = Options()

    # Headless mode if --headless flag is passed
    if request.config.getoption("--headless"):
        chrome_options.add_argument("--headless=new")

    # Window size
    chrome_options.add_argument("--window-size=1920,1080")

    # Disable automation detection (Req 2.4)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Stability options
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    # Suppress Chrome popups (save password, default browser, etc.)
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    })

    try:
        # Use Selenium 4's built-in Selenium Manager — no webdriver-manager needed
        browser = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        pytest.skip(f"WebDriver initialization failed: {e}")

    # Implicit wait 0s — we rely on explicit waits (Req 2.3)
    browser.implicitly_wait(0)

    # Set page load timeout
    browser.set_page_load_timeout(30)

    yield browser

    # Teardown: quit browser (Req 2.6)
    browser.quit()


# ---------------------------------------------------------------------------
# Screenshot on Failure Hook
# ---------------------------------------------------------------------------


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Capture a screenshot when a test fails during the 'call' phase and embed
    it in the pytest-html report.

    Requirements: 2.5, 17.3, 17.5, 17.6
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        # Try to get the driver from the test's fixture values
        driver = item.funcargs.get("driver")
        if driver is None:
            # Check other fixtures that provide a driver
            for fixture_name in (
                "logged_in_driver",
                "default_account_driver",
                "unauthenticated_driver",
                "second_user_driver",
            ):
                driver = item.funcargs.get(fixture_name)
                if driver is not None:
                    break

        if driver is not None:
            try:
                # Create reports/screenshots directory if it doesn't exist
                screenshots_dir = Path(__file__).resolve().parents[2] / "reports" / "screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)

                # Generate screenshot filename from test name
                test_name = item.nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
                screenshot_path = screenshots_dir / f"{test_name}_FAILED.png"

                driver.save_screenshot(str(screenshot_path))

                # Embed in pytest-html report if available
                if hasattr(item.config, "_html"):
                    extra = getattr(report, "extras", [])
                    # Use pytest-html's extras to embed the screenshot
                    try:
                        from pytest_html import extras as html_extras

                        extra.append(html_extras.png(str(screenshot_path)))
                    except ImportError:
                        pass
                    report.extras = extra

            except Exception:
                # Don't let screenshot failure break the test report
                pass


# ---------------------------------------------------------------------------
# Authentication Helper Functions
# ---------------------------------------------------------------------------


def _login_via_ui(driver: webdriver.Chrome, base_url: str, email: str, password: str) -> None:
    """
    Log in through the UI by navigating to /login and filling the form.

    Waits for redirect to Dashboard (URL no longer contains /login).
    """
    driver.get(f"{base_url}/login")

    wait = WebDriverWait(driver, 20)

    # Wait for login form to load
    email_input = wait.until(
        EC.presence_of_element_located((By.ID, "login-email"))
    )
    password_input = driver.find_element(By.ID, "login-password")
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'].btn-primary.auth-page__submit")

    # Fill credentials
    email_input.clear()
    email_input.send_keys(email)
    password_input.clear()
    password_input.send_keys(password)

    # Submit
    submit_button.click()

    # Wait for redirect away from /login (successful login redirects to /)
    wait.until(
        lambda d: "/login" not in d.current_url and "/register" not in d.current_url
    )


def _register_via_api(api_url: str, email: str, password: str) -> None:
    """Register a user via API POST /auth/register."""
    response = requests.post(
        f"{api_url}/auth/register",
        json={"email": email, "password": password},
        timeout=10,
    )
    # 201 = created, 409 = already exists (acceptable in some scenarios)
    if response.status_code not in (201, 409):
        raise RuntimeError(
            f"Failed to register test user {email}: "
            f"{response.status_code} - {response.text}"
        )


def _get_auth_token(api_url: str, email: str, password: str) -> str:
    """Get a JWT token via API POST /auth/login."""
    response = requests.post(
        f"{api_url}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to get token for {email}: "
            f"{response.status_code} - {response.text}"
        )
    return response.json()["token"]


def _cleanup_test_user(api_url: str, email: str, password: str) -> None:
    """
    Clean up test user data after a test.

    Attempts to delete the user's data via available API endpoints.
    Failures are logged but do not raise — cleanup is best-effort.
    """
    try:
        # Get a token for the test user
        token = _get_auth_token(api_url, email, password)
        headers = {"Authorization": f"Bearer {token}"}

        # Attempt to clear user's entries via API if endpoint exists
        requests.delete(f"{api_url}/entries", headers=headers, timeout=10)

        # Attempt to clear user's chat history if endpoint exists
        requests.delete(f"{api_url}/chat/history", headers=headers, timeout=10)

        # Attempt to delete the user account if endpoint exists
        requests.delete(f"{api_url}/auth/user", headers=headers, timeout=10)

    except Exception:
        # Cleanup failures are non-fatal; each test uses unique emails
        pass


# ---------------------------------------------------------------------------
# Authentication Fixtures (function-scoped)
# ---------------------------------------------------------------------------

# Default test password for generated test users
_TEST_PASSWORD = "TestPass123!"


@pytest.fixture(scope="function")
def logged_in_driver(
    driver: webdriver.Chrome, base_url: str, api_url: str
) -> Generator[webdriver.Chrome, None, None]:
    """
    WebDriver authenticated with a unique test user.

    - Registers a unique user via API (POST /auth/register)
    - Logs in through the UI
    - Yields the authenticated driver
    - Cleans up user data on teardown

    Requirements: 3.1, 3.3
    """
    # Generate unique test user credentials
    unique_id = uuid.uuid4().hex[:12]
    email = f"test_{unique_id}@test.com"
    password = _TEST_PASSWORD

    # Register the user via API
    _register_via_api(api_url, email, password)

    # Login via UI
    _login_via_ui(driver, base_url, email, password)

    yield driver

    # Teardown: clean up test user data (Req 3.3)
    _cleanup_test_user(api_url, email, password)


@pytest.fixture(scope="function")
def default_account_driver(
    driver: webdriver.Chrome, base_url: str
) -> Generator[webdriver.Chrome, None, None]:
    """
    WebDriver authenticated as the default account (wattif@gmail.com / wattif).

    Used for tests that require pre-existing data and a trained model.

    Requirement: 3.2
    """
    _login_via_ui(driver, base_url, "wattif@gmail.com", "wattif")

    yield driver


@pytest.fixture(scope="function")
def unauthenticated_driver(
    driver: webdriver.Chrome,
) -> Generator[webdriver.Chrome, None, None]:
    """
    WebDriver with no stored authentication token.

    Used for tests verifying unauthenticated access behavior.

    Requirement: 3.4
    """
    yield driver


@pytest.fixture(scope="function")
def second_user_driver(
    driver: webdriver.Chrome, base_url: str, api_url: str
) -> Generator[webdriver.Chrome, None, None]:
    """
    Second authenticated test user for data isolation tests.

    Creates a separate unique user account, distinct from logged_in_driver.

    Requirement: 3.5
    """
    # Generate a different unique test user
    unique_id = uuid.uuid4().hex[:12]
    email = f"test_second_{unique_id}@test.com"
    password = _TEST_PASSWORD

    # Register the user via API
    _register_via_api(api_url, email, password)

    # Login via UI
    _login_via_ui(driver, base_url, email, password)

    yield driver

    # Teardown: clean up second test user data
    _cleanup_test_user(api_url, email, password)
