"""
System & Infrastructure test module (SYS-01 to SYS-09).

Covers dark mode toggling and persistence, sidebar navigation,
active link indicators, mobile responsive behavior (hamburger menu,
overlay close, Escape close), and the health indicator widget.

Requirements: 15.1–15.10
"""

import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium.pages import TopBar, Sidebar, DashboardPage


# ---------------------------------------------------------------------------
# SYS-01: Dark Mode Toggle
# ---------------------------------------------------------------------------


@pytest.mark.system
def test_SYS_01_dark_mode_toggle(logged_in_driver, base_url):
    """Click the dark mode toggle and verify data-theme="dark" is applied
    to the <html> element."""
    topbar = TopBar(logged_in_driver, base_url)

    # Ensure we start on a loaded page
    WebDriverWait(logged_in_driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "header.topbar-compact"))
    )

    # If already in dark mode, toggle to light first
    if topbar.is_dark_mode():
        topbar.toggle_dark_mode()
        time.sleep(0.3)

    # Now toggle to dark mode
    topbar.toggle_dark_mode()
    time.sleep(0.3)

    # Verify data-theme="dark" is set on <html>
    theme = logged_in_driver.execute_script(
        "return document.documentElement.getAttribute('data-theme');"
    )
    assert theme == "dark", (
        f"Expected data-theme='dark' on <html>, got '{theme}'"
    )


# ---------------------------------------------------------------------------
# SYS-02: Light Mode Toggle
# ---------------------------------------------------------------------------


@pytest.mark.system
def test_SYS_02_light_mode_toggle(logged_in_driver, base_url):
    """Activate dark mode, then toggle back to light mode and verify
    data-theme becomes 'light' (dark removed)."""
    topbar = TopBar(logged_in_driver, base_url)

    # Ensure we start on a loaded page
    WebDriverWait(logged_in_driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "header.topbar-compact"))
    )

    # Ensure dark mode is active first
    if not topbar.is_dark_mode():
        topbar.toggle_dark_mode()
        time.sleep(0.3)

    assert topbar.is_dark_mode(), "Should be in dark mode before toggling to light"

    # Toggle back to light mode
    topbar.toggle_dark_mode()
    time.sleep(0.3)

    # Verify data-theme is "light" (not "dark")
    theme = logged_in_driver.execute_script(
        "return document.documentElement.getAttribute('data-theme');"
    )
    assert theme == "light", (
        f"Expected data-theme='light' on <html>, got '{theme}'"
    )


# ---------------------------------------------------------------------------
# SYS-03: Dark Mode Persistence
# ---------------------------------------------------------------------------


@pytest.mark.system
def test_SYS_03_dark_mode_persistence(logged_in_driver, base_url):
    """Activate dark mode, refresh the page, and verify data-theme='dark'
    persists (stored in localStorage key 'wattif-theme')."""
    topbar = TopBar(logged_in_driver, base_url)

    # Ensure page is loaded
    WebDriverWait(logged_in_driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "header.topbar-compact"))
    )

    # Activate dark mode
    if not topbar.is_dark_mode():
        topbar.toggle_dark_mode()
        time.sleep(0.3)

    assert topbar.is_dark_mode(), "Dark mode should be active before refresh"

    # Verify localStorage has the theme saved
    stored_theme = logged_in_driver.execute_script(
        "return window.localStorage.getItem('wattif-theme');"
    )
    assert stored_theme == "dark", (
        f"Expected localStorage 'wattif-theme' to be 'dark', got '{stored_theme}'"
    )

    # Refresh the page
    logged_in_driver.refresh()

    # Wait for page to reload
    WebDriverWait(logged_in_driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "header.topbar-compact"))
    )

    # Verify dark mode persisted after refresh
    theme = logged_in_driver.execute_script(
        "return document.documentElement.getAttribute('data-theme');"
    )
    assert theme == "dark", (
        f"Expected data-theme='dark' after refresh, got '{theme}'"
    )


# ---------------------------------------------------------------------------
# SYS-04: Sidebar Navigation
# ---------------------------------------------------------------------------


@pytest.mark.system
def test_SYS_04_sidebar_navigation(logged_in_driver, base_url):
    """Click each navigation link in the sidebar and verify the URL updates
    and page content is visible within 5 seconds."""
    sidebar = Sidebar(logged_in_driver, base_url)

    # Ensure page is loaded
    WebDriverWait(logged_in_driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "nav[aria-label='Main navigation']"))
    )

    nav_links = [
        ("Dashboard", "/"),
        ("Forecast", "/forecast"),
        ("Ask WATT-IF", "/ask"),
        ("Price Calculator", "/calculator"),
        ("Data Entry", "/data-entry"),
    ]

    for link_text, expected_path in nav_links:
        sidebar.navigate_to(link_text)

        # Wait for URL to update (within 5 seconds)
        WebDriverWait(logged_in_driver, 5).until(
            lambda d, path=expected_path: d.current_url.rstrip("/").endswith(
                path.rstrip("/")
            ) if path != "/" else (
                d.current_url.rstrip("/") == base_url.rstrip("/")
                or d.current_url.rstrip("/").endswith("/")
            )
        )

        # Verify page content is visible (main content area is present)
        WebDriverWait(logged_in_driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".app-shell__main"))
        )

        # Verify current URL contains expected path
        current_url = logged_in_driver.current_url
        if expected_path == "/":
            # Dashboard is at root — URL should be base_url or base_url/
            assert current_url.rstrip("/") == base_url.rstrip("/") or current_url.endswith("/"), (
                f"Expected URL to be root for Dashboard, got '{current_url}'"
            )
        else:
            assert expected_path in current_url, (
                f"Expected '{expected_path}' in URL after clicking '{link_text}', got '{current_url}'"
            )


# ---------------------------------------------------------------------------
# SYS-05: Active Link Indicator
# ---------------------------------------------------------------------------


@pytest.mark.system
def test_SYS_05_active_link_indicator(logged_in_driver, base_url):
    """Navigate to a page and verify the corresponding sidebar link has the
    CSS class 'nav-item--active'."""
    sidebar = Sidebar(logged_in_driver, base_url)

    # Ensure page is loaded
    WebDriverWait(logged_in_driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "nav[aria-label='Main navigation']"))
    )

    nav_pages = [
        ("Forecast", "/forecast"),
        ("Ask WATT-IF", "/ask"),
        ("Price Calculator", "/calculator"),
        ("Data Entry", "/data-entry"),
        ("Dashboard", "/"),
    ]

    for link_text, expected_path in nav_pages:
        sidebar.navigate_to(link_text)

        # Wait for navigation to complete
        if expected_path == "/":
            WebDriverWait(logged_in_driver, 5).until(
                lambda d: d.current_url.rstrip("/") == base_url.rstrip("/")
                or d.current_url.endswith("/")
            )
        else:
            WebDriverWait(logged_in_driver, 5).until(
                lambda d, path=expected_path: path in d.current_url
            )

        # Brief pause for React Router to update active class
        time.sleep(0.3)

        # Verify the active link matches the clicked page
        active_link_text = sidebar.get_active_link()
        assert active_link_text == link_text, (
            f"Expected active link to be '{link_text}', got '{active_link_text}'"
        )


# ---------------------------------------------------------------------------
# SYS-06: Mobile Hamburger Menu
# ---------------------------------------------------------------------------


@pytest.mark.system
def test_SYS_06_mobile_hamburger_menu(logged_in_driver, base_url):
    """Resize viewport to ≤767px → sidebar hidden, hamburger button shown;
    click hamburger → sidebar becomes visible (class app-shell__sidebar--open)."""
    topbar = TopBar(logged_in_driver, base_url)

    # Ensure page is loaded at desktop size first
    WebDriverWait(logged_in_driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "header.topbar-compact"))
    )

    try:
        # Resize to mobile viewport
        logged_in_driver.set_window_size(375, 812)
        time.sleep(0.5)  # Wait for CSS media query to apply

        # Verify hamburger button is visible
        hamburger = WebDriverWait(logged_in_driver, 5).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "button.topbar-menu-btn[aria-label='Open navigation menu']")
            )
        )
        assert hamburger.is_displayed(), "Hamburger button should be visible on mobile"

        # Verify sidebar is hidden (not open)
        sidebar_wrappers = logged_in_driver.find_elements(
            By.CSS_SELECTOR, ".app-shell__sidebar--open"
        )
        assert len(sidebar_wrappers) == 0, (
            "Sidebar should not have --open class before hamburger click"
        )

        # Click hamburger to open sidebar
        topbar.open_mobile_menu()
        time.sleep(0.3)  # Wait for animation

        # Verify sidebar is now open
        WebDriverWait(logged_in_driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".app-shell__sidebar--open")
            )
        )

        open_sidebar = logged_in_driver.find_elements(
            By.CSS_SELECTOR, ".app-shell__sidebar--open"
        )
        assert len(open_sidebar) > 0, (
            "Sidebar should have app-shell__sidebar--open class after hamburger click"
        )

    finally:
        # Restore desktop viewport
        logged_in_driver.set_window_size(1920, 1080)


# ---------------------------------------------------------------------------
# SYS-07: Mobile Overlay Close
# ---------------------------------------------------------------------------


@pytest.mark.system
def test_SYS_07_mobile_overlay_close(logged_in_driver, base_url):
    """Click the overlay while the mobile sidebar is open and verify the
    sidebar closes (open class removed)."""
    topbar = TopBar(logged_in_driver, base_url)

    # Ensure page is loaded
    WebDriverWait(logged_in_driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "header.topbar-compact"))
    )

    try:
        # Resize to mobile viewport
        logged_in_driver.set_window_size(375, 812)
        time.sleep(0.5)

        # Open the mobile sidebar
        topbar.open_mobile_menu()
        time.sleep(0.3)

        # Verify sidebar is open
        WebDriverWait(logged_in_driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".app-shell__sidebar--open")
            )
        )

        # Click the overlay to close sidebar
        overlay = WebDriverWait(logged_in_driver, 5).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".app-shell__overlay--visible")
            )
        )
        overlay.click()
        time.sleep(0.3)  # Wait for animation

        # Verify sidebar is closed (open class removed)
        WebDriverWait(logged_in_driver, 5).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, ".app-shell__overlay--visible")
            )
        )

        open_sidebar = logged_in_driver.find_elements(
            By.CSS_SELECTOR, ".app-shell__sidebar--open"
        )
        assert len(open_sidebar) == 0, (
            "Sidebar should not have --open class after clicking overlay"
        )

    finally:
        # Restore desktop viewport
        logged_in_driver.set_window_size(1920, 1080)


# ---------------------------------------------------------------------------
# SYS-08: Mobile Escape Close
# ---------------------------------------------------------------------------


@pytest.mark.system
def test_SYS_08_mobile_escape_close(logged_in_driver, base_url):
    """Press Escape while the mobile sidebar is open and verify the sidebar
    closes (open class removed)."""
    topbar = TopBar(logged_in_driver, base_url)

    # Ensure page is loaded
    WebDriverWait(logged_in_driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "header.topbar-compact"))
    )

    try:
        # Resize to mobile viewport
        logged_in_driver.set_window_size(375, 812)
        time.sleep(0.5)

        # Open the mobile sidebar
        topbar.open_mobile_menu()
        time.sleep(0.3)

        # Verify sidebar is open
        WebDriverWait(logged_in_driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".app-shell__sidebar--open")
            )
        )

        # Press Escape to close the sidebar
        logged_in_driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)  # Wait for animation

        # Verify sidebar is closed (open class removed)
        WebDriverWait(logged_in_driver, 5).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, ".app-shell__sidebar--open")) == 0
        )

        open_sidebar = logged_in_driver.find_elements(
            By.CSS_SELECTOR, ".app-shell__sidebar--open"
        )
        assert len(open_sidebar) == 0, (
            "Sidebar should not have --open class after pressing Escape"
        )

    finally:
        # Restore desktop viewport
        logged_in_driver.set_window_size(1920, 1080)


# ---------------------------------------------------------------------------
# SYS-09: Health Indicator Operational
# ---------------------------------------------------------------------------


@pytest.mark.system
def test_SYS_09_health_indicator_operational(logged_in_driver, base_url):
    """When all services are running, verify the health indicator shows
    'All systems operational' text with a green indicator."""
    sidebar = Sidebar(logged_in_driver, base_url)

    # Ensure page is loaded
    WebDriverWait(logged_in_driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "nav[aria-label='Main navigation']"))
    )

    # Wait for health indicator to appear and load (it polls the /health endpoint)
    health_aside = WebDriverWait(logged_in_driver, 15).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "aside[aria-label='System health']")
        )
    )

    # Wait for the health indicator to finish its initial check
    # It starts as "Connecting…" then becomes either operational or degraded
    WebDriverWait(logged_in_driver, 15).until(
        lambda d: "Connecting" not in d.find_element(
            By.CSS_SELECTOR, "aside[aria-label='System health']"
        ).text
    )

    # Get the health status text
    health_text = sidebar.get_health_status()

    assert "All systems operational" in health_text, (
        f"Expected 'All systems operational' in health indicator, got '{health_text}'"
    )


# ---------------------------------------------------------------------------
# Manual-Only Test Stubs (SYS-10, SYS-11)
# ---------------------------------------------------------------------------


@pytest.mark.manual
@pytest.mark.system
def test_SYS_10_health_degraded_ollama_offline():
    """SYS-10: When the Ollama service is stopped, the health indicator shows
    a degraded/warning state indicating partial system unavailability."""
    pytest.skip(
        reason="Requires stopping Ollama service; not automatable within Selenium. "
        "Manual execution required to verify health indicator reflects degraded state."
    )


@pytest.mark.manual
@pytest.mark.system
def test_SYS_11_offline_banner():
    """SYS-11: When the network is disconnected, an offline banner appears at the
    top of the page indicating the application has lost connectivity."""
    pytest.skip(
        reason="Requires disconnecting the network; Chrome DevTools Protocol can "
        "simulate this but is not standard Selenium. Manual execution required."
    )
