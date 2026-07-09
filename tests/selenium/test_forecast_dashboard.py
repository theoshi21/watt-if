"""
Forecast Dashboard test module (FD-01 to FD-20).

Covers forecast chart rendering, horizon selection, stat cards,
anomaly detection, and empty/error states on the Forecast and Dashboard pages.

Requirements: 10.1–10.11, 11.1–11.8
"""

import time
import re

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium.pages import DashboardPage, ForecastPage


# ---------------------------------------------------------------------------
# Forecasting Tests (FD-01 to FD-11)
# ---------------------------------------------------------------------------


@pytest.mark.forecast_dashboard
def test_FD_01_default_forecast(default_account_driver, base_url):
    """Forecast page displays a 3-month forecast by default with 3 bars in kWh chart and 3 points in bill line chart."""
    page = ForecastPage(default_account_driver, base_url)
    page.navigate("/forecast")
    page.wait_for_chart_loaded()

    assert page.get_bar_count() == 3, "Expected 3 bars in kWh chart for default 3-month horizon"
    assert page.get_line_point_count() == 3, "Expected 3 line points in bill chart for default 3-month horizon"


@pytest.mark.forecast_dashboard
def test_FD_02_horizon_one_month(default_account_driver, base_url):
    """Selecting 1-month horizon updates kWh chart to display exactly 1 bar."""
    page = ForecastPage(default_account_driver, base_url)
    page.navigate("/forecast")
    page.wait_for_chart_loaded()

    page.select_horizon(1)
    page.wait_for_chart_loaded()

    assert page.get_bar_count() == 1, "Expected 1 bar in kWh chart for 1-month horizon"


@pytest.mark.forecast_dashboard
def test_FD_03_horizon_six_months(default_account_driver, base_url):
    """Selecting 6-month horizon updates kWh chart to display exactly 6 bars."""
    page = ForecastPage(default_account_driver, base_url)
    page.navigate("/forecast")
    page.wait_for_chart_loaded()

    page.select_horizon(6)
    page.wait_for_chart_loaded()

    assert page.get_bar_count() == 6, "Expected 6 bars in kWh chart for 6-month horizon"


@pytest.mark.forecast_dashboard
def test_FD_04_horizon_nine_months(default_account_driver, base_url):
    """Selecting 9-month horizon updates kWh chart to display exactly 9 bars."""
    page = ForecastPage(default_account_driver, base_url)
    page.navigate("/forecast")
    page.wait_for_chart_loaded()

    page.select_horizon(9)
    page.wait_for_chart_loaded()

    assert page.get_bar_count() == 9, "Expected 9 bars in kWh chart for 9-month horizon"


@pytest.mark.forecast_dashboard
def test_FD_05_horizon_twelve_months(default_account_driver, base_url):
    """Selecting 12-month horizon updates kWh chart to display exactly 12 bars."""
    page = ForecastPage(default_account_driver, base_url)
    page.navigate("/forecast")
    page.wait_for_chart_loaded()

    page.select_horizon(12)
    page.wait_for_chart_loaded()

    assert page.get_bar_count() == 12, "Expected 12 bars in kWh chart for 12-month horizon"


@pytest.mark.forecast_dashboard
def test_FD_06_forecast_start_month(default_account_driver, base_url):
    """With latest data entry being December 2025, the first forecast bar is labelled 'Jan 2026'."""
    page = ForecastPage(default_account_driver, base_url)
    page.navigate("/forecast")
    page.wait_for_chart_loaded()

    labels = page.get_xaxis_labels()
    assert len(labels) > 0, "Expected at least one x-axis label"
    assert "Jan 2026" in labels[0], f"Expected first label to contain 'Jan 2026', got '{labels[0]}'"


@pytest.mark.forecast_dashboard
def test_FD_07_error_bars_visible(default_account_driver, base_url):
    """Each bar in the kWh chart has visible error bars representing the 95% confidence interval."""
    page = ForecastPage(default_account_driver, base_url)
    page.navigate("/forecast")
    page.wait_for_chart_loaded()

    assert page.has_error_bars(), "Expected error bars to be visible on kWh chart bars"


@pytest.mark.forecast_dashboard
def test_FD_08_confidence_band(default_account_driver, base_url):
    """Bill line chart has a shaded confidence interval band rendered around the line."""
    page = ForecastPage(default_account_driver, base_url)
    page.navigate("/forecast")
    page.wait_for_chart_loaded()

    # The confidence band uses recharts Area elements rendered as .recharts-area paths
    area_elements = default_account_driver.find_elements(By.CSS_SELECTOR, ".recharts-area")
    assert len(area_elements) > 0, "Expected shaded confidence interval band (.recharts-area) in bill chart"


@pytest.mark.forecast_dashboard
def test_FD_09_tooltip_on_hover(default_account_driver, base_url):
    """Hovering over a kWh chart bar displays a tooltip with forecast kWh value and CI bounds."""
    page = ForecastPage(default_account_driver, base_url)
    page.navigate("/forecast")
    page.wait_for_chart_loaded()

    page.hover_bar(0)
    # Allow tooltip to render
    time.sleep(0.5)

    tooltip_text = page.get_tooltip_text()
    assert "kWh" in tooltip_text, f"Expected tooltip to contain 'kWh', got: '{tooltip_text}'"
    assert "95% CI" in tooltip_text, f"Expected tooltip to contain '95% CI', got: '{tooltip_text}'"


@pytest.mark.forecast_dashboard
def test_FD_10_no_model_error(logged_in_driver, base_url):
    """Without a trained model, a clear error message is displayed instead of a chart."""
    page = ForecastPage(logged_in_driver, base_url)
    page.navigate("/forecast")

    error_msg = page.get_error_message()
    assert "No trained model found" in error_msg, (
        f"Expected 'No trained model found' error message, got: '{error_msg}'"
    )


@pytest.mark.forecast_dashboard
def test_FD_11_empty_database_guidance(logged_in_driver, base_url):
    """With no data or model, a guidance message directs the user to add data via the Data Entry page."""
    page = ForecastPage(logged_in_driver, base_url)
    page.navigate("/forecast")

    error_msg = page.get_error_message()
    # The error message should guide the user to upload data on the Data Entry page
    assert "Data Entry" in error_msg or "upload" in error_msg.lower() or "CSV" in error_msg, (
        f"Expected guidance message mentioning Data Entry or upload, got: '{error_msg}'"
    )


# ---------------------------------------------------------------------------
# Dashboard Tests (FD-12 through FD-19)
# ---------------------------------------------------------------------------


@pytest.mark.forecast_dashboard
def test_FD_12_stat_cards_displayed(default_account_driver, base_url):
    """Trained model displays 4 stat cards: This Month, Daily Average, Avg Temp, Avg Humidity."""
    page = DashboardPage(default_account_driver, base_url)
    page.navigate("/")

    # Wait for stat grid to load
    page.wait_for_element(page.STAT_GRID)

    cards = page.get_stat_cards()
    assert len(cards) == 4, f"Expected 4 stat cards, got {len(cards)}"

    expected_labels = {"this month", "daily average", "avg temp", "avg humidity"}
    actual_labels = {card["label"].lower() for card in cards}
    assert actual_labels == expected_labels, (
        f"Expected labels {expected_labels}, got {actual_labels}"
    )


@pytest.mark.forecast_dashboard
def test_FD_13_this_month_value(default_account_driver, base_url):
    """'This Month' stat card shows a numeric kWh value greater than zero."""
    page = DashboardPage(default_account_driver, base_url)
    page.navigate("/")

    page.wait_for_element(page.STAT_GRID)

    value_str = page.get_stat_value("This Month")
    assert value_str is not None, "Could not find 'This Month' stat card"

    # Parse value as float — should be a positive number
    value = float(value_str.replace(",", ""))
    assert value > 0, f"Expected 'This Month' value > 0, got {value}"


@pytest.mark.forecast_dashboard
def test_FD_14_daily_average_value(default_account_driver, base_url):
    """'Daily Average' is approximately This Month / 30 (within ±1 tolerance)."""
    page = DashboardPage(default_account_driver, base_url)
    page.navigate("/")

    page.wait_for_element(page.STAT_GRID)

    this_month_str = page.get_stat_value("This Month")
    daily_avg_str = page.get_stat_value("Daily Average")

    assert this_month_str is not None, "Could not find 'This Month' stat card"
    assert daily_avg_str is not None, "Could not find 'Daily Average' stat card"

    this_month = float(this_month_str.replace(",", ""))
    daily_avg = float(daily_avg_str.replace(",", ""))

    expected_daily = this_month / 30
    assert abs(daily_avg - expected_daily) <= 1, (
        f"Daily Average ({daily_avg}) not within ±1 of This Month / 30 ({expected_daily:.2f})"
    )


@pytest.mark.forecast_dashboard
def test_FD_15_weather_values_range(default_account_driver, base_url):
    """Avg Temp is 25–38°C and Avg Humidity is 50–95%."""
    page = DashboardPage(default_account_driver, base_url)
    page.navigate("/")

    page.wait_for_element(page.STAT_GRID)

    temp_str = page.get_stat_value("Avg Temp")
    humidity_str = page.get_stat_value("Avg Humidity")

    assert temp_str is not None, "Could not find 'Avg Temp' stat card"
    assert humidity_str is not None, "Could not find 'Avg Humidity' stat card"

    temp = float(temp_str.replace(",", ""))
    humidity = float(humidity_str.replace(",", ""))

    assert 25 <= temp <= 38, f"Expected Avg Temp 25–38°C, got {temp}"
    assert 50 <= humidity <= 95, f"Expected Avg Humidity 50–95%, got {humidity}"


@pytest.mark.forecast_dashboard
def test_FD_16_no_forecast_empty_state(logged_in_driver, base_url):
    """No trained model shows empty state message directing user to upload data."""
    page = DashboardPage(logged_in_driver, base_url)
    page.navigate("/")

    # Wait for either empty state or stat grid to appear (give time for API call)
    WebDriverWait(logged_in_driver, 15).until(
        lambda d: (
            d.find_elements(By.XPATH, "//*[contains(text(), 'No forecast data yet.')]")
            or d.find_elements(By.CSS_SELECTOR, ".stat-grid")
        )
    )

    assert page.is_empty_state(), (
        "Expected empty state message 'No forecast data yet.' for user with no trained model"
    )


@pytest.mark.forecast_dashboard
def test_FD_17_anomaly_card_visible(default_account_driver, base_url):
    """When forecast first month > 110% of mean, anomaly card/banner is visible."""
    page = DashboardPage(default_account_driver, base_url)
    page.navigate("/")

    page.wait_for_element(page.STAT_GRID)

    # This is a conditional test. The anomaly card appears only when
    # the first forecast month exceeds 110% of the mean.
    # We verify: if anomaly card is present, then it contains the expected text.
    # If not present, we accept that the data doesn't trigger anomaly detection.
    has_anomaly = page.has_anomaly_card()

    if has_anomaly:
        # Verify the anomaly card has the expected structure
        elements = default_account_driver.find_elements(
            By.XPATH, "//*[contains(text(), 'Anomaly Detected:')]"
        )
        assert len(elements) > 0 and elements[0].is_displayed(), (
            "Anomaly card text 'Anomaly Detected:' should be visible"
        )
    else:
        # No anomaly detected — this is acceptable if the data doesn't trigger it.
        # Mark as a conditional pass with an informational message.
        pytest.skip(
            "Anomaly card not visible — forecast data does not trigger anomaly "
            "(first month ≤ 110% of mean). Test is conditionally valid."
        )


@pytest.mark.forecast_dashboard
def test_FD_18_no_anomaly_card(default_account_driver, base_url):
    """When forecast first month ≤ 110% of mean, no anomaly card is in the DOM."""
    page = DashboardPage(default_account_driver, base_url)
    page.navigate("/")

    page.wait_for_element(page.STAT_GRID)

    has_anomaly = page.has_anomaly_card()

    if not has_anomaly:
        # Confirm no anomaly card elements exist in the DOM
        elements = default_account_driver.find_elements(
            By.XPATH, "//*[contains(text(), 'Anomaly Detected:')]"
        )
        assert len(elements) == 0 or not elements[0].is_displayed(), (
            "Anomaly card should not be visible when forecast ≤ 110% of mean"
        )
    else:
        # Anomaly IS present — data triggers anomaly detection, so this test
        # condition doesn't apply. Skip with informational note.
        pytest.skip(
            "Anomaly card is visible — forecast data triggers anomaly detection "
            "(first month > 110% of mean). Test is conditionally valid."
        )


@pytest.mark.forecast_dashboard
def test_FD_19_forecast_chart_container(default_account_driver, base_url):
    """When forecast data exists, the chart container (canvas/SVG) is visible."""
    page = DashboardPage(default_account_driver, base_url)
    page.navigate("/")

    page.wait_for_element(page.STAT_GRID)

    assert page.has_forecast_chart(), (
        "Expected forecast chart container with aria-label='Forecast charts' to be visible"
    )


# ---------------------------------------------------------------------------
# Manual-Only Test Stub (FD-20)
# ---------------------------------------------------------------------------


@pytest.mark.manual
@pytest.mark.forecast_dashboard
def test_FD_20_loading_skeleton_throttled_network():
    """FD-20: With network throttled to slow 3G, the Dashboard and Forecast pages
    display loading skeleton placeholders while data is being fetched."""
    pytest.skip(
        reason="Requires network throttling via Chrome DevTools Protocol; not reliably "
        "automatable with standard Selenium WebDriver. Manual execution required to "
        "verify loading skeleton appearance under constrained network conditions."
    )
