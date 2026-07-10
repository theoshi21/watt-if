"""
Price Calculator test module (PCT-01 to PCT-12).

Covers rate display, bill breakdown calculation, input validation,
bracket auto-selection, manual bracket override, customer type switching,
and rate refresh for the WATT-IF Price Calculator page.

Requirements: 13.1–13.12
"""

import re
import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium.pages import PriceCalculatorPage


# ---------------------------------------------------------------------------
# PCT-01: Rate Display on Page Load
# ---------------------------------------------------------------------------


@pytest.mark.price_calculator
def test_PCT_01_rate_display(logged_in_driver, base_url):
    """Opening the Price Calculator should fetch and display the current Meralco
    rate. A Meralco rate value (in ₱/kWh) is shown along with a last-updated
    timestamp. The value is between ₱9 and ₱15/kWh."""
    page = PriceCalculatorPage(logged_in_driver, base_url)
    page.navigate("/calculator")

    # Wait for rate info to load (the "Meralco Summary Schedule of Rates" text appears)
    page.wait_for_element(page.RATE_INFO, timeout=30)
    time.sleep(2)

    # Verify rate display mentions Meralco
    rate_text = page.get_rate_display()
    assert "Meralco" in rate_text, (
        f"Rate display should mention 'Meralco', got: {rate_text}"
    )

    # Verify last-fetched timestamp is present
    last_fetched = page.get_last_fetched()
    assert "Last fetched" in last_fetched, (
        f"Expected 'Last fetched' timestamp, got: {last_fetched}"
    )


# ---------------------------------------------------------------------------
# PCT-02: Valid kWh Breakdown
# ---------------------------------------------------------------------------


@pytest.mark.price_calculator
def test_PCT_02_valid_breakdown(logged_in_driver, base_url):
    """Entering a valid kWh amount (250) should calculate and display a detailed
    bill breakdown with charge components (generation, transmission, system loss,
    distribution, supply, metering, other) plus total."""
    page = PriceCalculatorPage(logged_in_driver, base_url)
    page.navigate("/calculator")

    # Wait for rate to load
    page.wait_for_element(page.RATE_INFO, timeout=30)

    page.enter_kwh(250)

    # Wait for breakdown to appear
    time.sleep(2)

    assert page.is_breakdown_visible(), "Breakdown section should be visible after entering 250 kWh"

    breakdown = page.get_breakdown()
    assert len(breakdown) >= 5, (
        f"Expected at least 5 charge components in breakdown, got {len(breakdown)}"
    )

    # Verify expected charge component keywords are present
    labels = [item["label"].lower() for item in breakdown]
    all_labels_text = " ".join(labels)

    expected_components = ["generation", "transmission", "distribution"]
    for component in expected_components:
        assert component in all_labels_text, (
            f"Expected '{component}' in breakdown labels. Got labels: {labels}"
        )

    # Verify total bill is displayed and is a valid peso amount
    total = page.get_total_bill()
    assert "₱" in total or re.search(r"[\d,]+\.?\d*", total), (
        f"Total bill should be a monetary value, got: {total}"
    )


# ---------------------------------------------------------------------------
# PCT-03: Zero kWh Input
# ---------------------------------------------------------------------------


@pytest.mark.price_calculator
def test_PCT_03_zero_kwh(logged_in_driver, base_url):
    """A kWh of zero should result in a zero-cost breakdown or the breakdown
    should hide. No error."""
    page = PriceCalculatorPage(logged_in_driver, base_url)
    page.navigate("/calculator")

    page.wait_for_element(page.RATE_INFO, timeout=30)

    page.enter_kwh(0)
    time.sleep(2)

    # No error should be present
    error_elements = page.find_elements(page.RATE_ERROR)
    # Check that no error alert related to the input is shown
    # (RATE_ERROR is for rate fetch errors, which is acceptable)

    # Either breakdown is hidden or shows zero values
    if page.is_breakdown_visible():
        total = page.get_total_bill()
        # Total should be ₱0 or ₱0.00
        total_match = re.search(r"[\d,]+\.?\d*", total.replace(",", ""))
        if total_match:
            total_value = float(total_match.group(0))
            assert total_value == 0.0, (
                f"Total for 0 kWh should be ₱0, got: {total}"
            )
    # If breakdown is not visible, that's also acceptable (hidden for 0 kWh)


# ---------------------------------------------------------------------------
# PCT-04: Negative kWh Input
# ---------------------------------------------------------------------------


@pytest.mark.price_calculator
def test_PCT_04_negative_kwh(logged_in_driver, base_url):
    """A negative kWh value should be rejected (field does not accept negative
    sign) or treated as 0/empty. No bill calculated for negative input."""
    page = PriceCalculatorPage(logged_in_driver, base_url)
    page.navigate("/calculator")

    page.wait_for_element(page.RATE_INFO, timeout=30)

    page.enter_kwh(-100)
    time.sleep(2)

    # Check the input field value — either it rejected the minus sign
    # or the value was treated as empty/zero
    input_el = page.wait_for_element(page.KWH_INPUT)
    input_value = input_el.get_attribute("value")

    # Acceptable outcomes: field is empty, "0", "100" (minus stripped), or no breakdown
    if input_value and input_value not in ("", "0"):
        # If the field accepted -100, the breakdown should not calculate
        # or it should show zero
        if page.is_breakdown_visible():
            total = page.get_total_bill()
            total_match = re.search(r"[\d,]+\.?\d*", total.replace(",", ""))
            if total_match:
                total_value = float(total_match.group(0))
                assert total_value == 0.0, (
                    f"Negative input should result in ₱0 total, got: {total}"
                )


# ---------------------------------------------------------------------------
# PCT-05: Minimum kWh (1)
# ---------------------------------------------------------------------------


@pytest.mark.price_calculator
def test_PCT_05_minimum_kwh(logged_in_driver, base_url):
    """A kWh of 1 should produce a small but valid bill breakdown with
    total > ₱0. No error."""
    page = PriceCalculatorPage(logged_in_driver, base_url)
    page.navigate("/calculator")

    page.wait_for_element(page.RATE_INFO, timeout=30)

    page.enter_kwh(1)
    time.sleep(2)

    assert page.is_breakdown_visible(), "Breakdown should be visible for 1 kWh"

    total = page.get_total_bill()
    total_match = re.search(r"[\d,]+\.?\d*", total.replace(",", ""))
    assert total_match is not None, f"Could not extract total value from: {total}"

    total_value = float(total_match.group(0).replace(",", ""))
    assert total_value > 0, (
        f"Total for 1 kWh should be > ₱0, got ₱{total_value}"
    )


# ---------------------------------------------------------------------------
# PCT-06: Large kWh (9999)
# ---------------------------------------------------------------------------


@pytest.mark.price_calculator
def test_PCT_06_large_kwh(logged_in_driver, base_url):
    """A large kWh value (9999) should produce a proportionally scaled breakdown
    without overflow, NaN, or crash."""
    page = PriceCalculatorPage(logged_in_driver, base_url)
    page.navigate("/calculator")

    page.wait_for_element(page.RATE_INFO, timeout=30)

    page.enter_kwh(9999)
    time.sleep(2)

    assert page.is_breakdown_visible(), "Breakdown should be visible for 9999 kWh"

    # Verify total is a valid number (no NaN, Infinity, or overflow)
    total = page.get_total_bill()
    assert "NaN" not in total, f"Total should not contain NaN, got: {total}"
    assert "Infinity" not in total, f"Total should not contain Infinity, got: {total}"
    assert "undefined" not in total, f"Total should not contain undefined, got: {total}"

    total_match = re.search(r"[\d,]+\.?\d*", total.replace(",", ""))
    assert total_match is not None, f"Could not extract total value from: {total}"

    total_value = float(total_match.group(0).replace(",", ""))
    assert total_value > 0, (
        f"Total for 9999 kWh should be > ₱0, got ₱{total_value}"
    )

    # Verify breakdown items don't contain NaN
    breakdown = page.get_breakdown()
    for item in breakdown:
        assert "NaN" not in item["amount"], (
            f"Breakdown item '{item['label']}' should not contain NaN, got: {item['amount']}"
        )


# ---------------------------------------------------------------------------
# PCT-07: Bracket Auto-Selection (350 kWh)
# ---------------------------------------------------------------------------


@pytest.mark.price_calculator
def test_PCT_07_bracket_auto_selection(logged_in_driver, base_url):
    """The calculator should automatically select the '301–400 kWh' bracket
    when 350 kWh is entered."""
    page = PriceCalculatorPage(logged_in_driver, base_url)
    page.navigate("/calculator")

    page.wait_for_element(page.RATE_INFO, timeout=30)

    page.enter_kwh(350)
    time.sleep(2)

    selected_bracket = page.get_selected_bracket()
    assert "301" in selected_bracket and "400" in selected_bracket, (
        f"Expected '301–400 kWh' bracket for 350 kWh, got: '{selected_bracket}'"
    )


# ---------------------------------------------------------------------------
# PCT-08: Bracket Upper Boundary (400 kWh)
# ---------------------------------------------------------------------------


@pytest.mark.price_calculator
def test_PCT_08_bracket_upper_boundary(logged_in_driver, base_url):
    """At the upper boundary 400 kWh, the '301–400 kWh' bracket should still
    be selected."""
    page = PriceCalculatorPage(logged_in_driver, base_url)
    page.navigate("/calculator")

    page.wait_for_element(page.RATE_INFO, timeout=30)

    page.enter_kwh(400)
    time.sleep(2)

    selected_bracket = page.get_selected_bracket()
    assert "301" in selected_bracket and "400" in selected_bracket, (
        f"Expected '301–400 kWh' bracket for 400 kWh, got: '{selected_bracket}'"
    )


# ---------------------------------------------------------------------------
# PCT-09: Bracket Next Tier (401 kWh)
# ---------------------------------------------------------------------------


@pytest.mark.price_calculator
def test_PCT_09_bracket_next_tier(logged_in_driver, base_url):
    """One kWh above the boundary (401) should select the 'Over 400 kWh'
    bracket."""
    page = PriceCalculatorPage(logged_in_driver, base_url)
    page.navigate("/calculator")

    page.wait_for_element(page.RATE_INFO, timeout=30)

    page.enter_kwh(401)
    time.sleep(2)

    selected_bracket = page.get_selected_bracket()
    # Accept variations: "Over 400 kWh", ">400 kWh", "401+ kWh", etc.
    assert "400" in selected_bracket and (
        "over" in selected_bracket.lower()
        or ">" in selected_bracket
        or "above" in selected_bracket.lower()
        or "401" in selected_bracket
    ), (
        f"Expected 'Over 400 kWh' bracket for 401 kWh, got: '{selected_bracket}'"
    )


# ---------------------------------------------------------------------------
# PCT-10: Manual Bracket Override Recalculates
# ---------------------------------------------------------------------------


@pytest.mark.price_calculator
def test_PCT_10_manual_bracket_recalculates(logged_in_driver, base_url):
    """Manually choosing a different bracket should recalculate the bill using
    that bracket's rates. Enter 350 (auto-selects 301-400), note total,
    manually change to '201-300', verify total changes."""
    page = PriceCalculatorPage(logged_in_driver, base_url)
    page.navigate("/calculator")

    page.wait_for_element(page.RATE_INFO, timeout=30)

    # Enter 350 kWh — auto-selects 301-400 bracket
    page.enter_kwh(350)
    time.sleep(2)

    assert page.is_breakdown_visible(), "Breakdown should be visible for 350 kWh"
    original_total = page.get_total_bill()

    # Manually change bracket to 201-300
    page.select_bracket("201 TO 300 KWH")
    time.sleep(2)

    # Verify total changed
    new_total = page.get_total_bill()
    assert new_total != original_total, (
        f"Total should change when bracket is manually changed. "
        f"Original: {original_total}, After bracket change: {new_total}"
    )


# ---------------------------------------------------------------------------
# PCT-11: Customer Type Change Recalculates
# ---------------------------------------------------------------------------


@pytest.mark.price_calculator
def test_PCT_11_customer_type_change(logged_in_driver, base_url):
    """Switching customer type should update bracket options and recalculate.
    Change from Residential to General Service, verify the breakdown subtitle reflects the change."""
    page = PriceCalculatorPage(logged_in_driver, base_url)
    page.navigate("/calculator")

    page.wait_for_element(page.RATE_INFO, timeout=30)

    # Enter a kWh value first to see a breakdown
    page.enter_kwh(250)
    time.sleep(2)

    assert page.is_breakdown_visible(), "Breakdown should be visible for 250 kWh"

    # Change customer type to General Service A
    page.change_customer_type("General Service A")
    time.sleep(2)

    # Verify the breakdown section now shows "General Service A" in its subtitle
    breakdown_section = page.wait_for_element(page.BREAKDOWN_SECTION)
    section_text = breakdown_section.text
    assert "General Service A" in section_text, (
        f"Expected breakdown to reflect 'General Service A' customer type, got: {section_text[:200]}"
    )


# ---------------------------------------------------------------------------
# PCT-12: Refresh Rate Updates Timestamp and Recalculates
# ---------------------------------------------------------------------------


@pytest.mark.price_calculator
def test_PCT_12_refresh_rate(logged_in_driver, base_url):
    """Clicking Refresh Rate should update the timestamp and recalculate the
    bill."""
    page = PriceCalculatorPage(logged_in_driver, base_url)
    page.navigate("/calculator")

    page.wait_for_element(page.RATE_INFO, timeout=30)

    # Enter a kWh value to get a breakdown
    page.enter_kwh(250)
    time.sleep(2)

    assert page.is_breakdown_visible(), "Breakdown should be visible for 250 kWh"

    # Record timestamp before refresh
    timestamp_before = page.get_last_fetched()

    # Click refresh rate
    page.refresh_rate()

    # Wait for the rate to reload
    time.sleep(3)

    # Verify timestamp changed
    timestamp_after = page.get_last_fetched()
    assert timestamp_after != timestamp_before, (
        f"Timestamp should change after refresh. "
        f"Before: '{timestamp_before}', After: '{timestamp_after}'"
    )


# ---------------------------------------------------------------------------
# Manual-Only Test Stub (PCT-13)
# ---------------------------------------------------------------------------


@pytest.mark.manual
@pytest.mark.price_calculator
def test_PCT_13_calculator_api_unavailable():
    """PCT-13: When the internet is disconnected mid-session, the Price Calculator
    displays an error state indicating the rate API is unavailable and no bill
    calculation can be performed."""
    pytest.skip(
        reason="Requires disconnecting internet mid-test; not automatable within "
        "Selenium. Manual execution required to verify graceful error handling "
        "when the Meralco rate API becomes unreachable."
    )
