# Implementation Plan: Selenium Automation Tests

## Overview

This plan implements a Python Selenium automation test suite for the WATT-IF application, automating 133 manual test cases across 7 modules using pytest, Selenium WebDriver with ChromeDriver, and the Page Object Model pattern. Tasks 1 and 2 (project structure and page objects) are already completed. The remaining work focuses on implementing the 7 test module files, fixture CSV creation, manual test stubs, and integration verification.

## Tasks

- [x] 1. Set up project structure, dependencies, and configuration
  - Created `tests/selenium/` directory structure with `pages/`, `fixtures/`, and `reports/` subdirectories
  - Created `requirements.txt` with pinned versions (selenium==4.25.0, pytest==8.3.4, pytest-html==4.1.1, webdriver-manager==4.0.2, requests==2.32.3)
  - Created `pytest.ini` with testpaths, markers (account, data_management, forecast_dashboard, chat, price_calculator, settings, system, manual), and addopts for HTML reporting
  - Created `tests/selenium/conftest.py` with all shared fixtures: `driver`, `logged_in_driver`, `default_account_driver`, `unauthenticated_driver`, `second_user_driver`, `test_csv_path`, `base_url`, `api_url`, `pytest_addoption` for --headless, and screenshot-on-failure hook
  - _Requirements: 1.1–1.9, 2.1–2.7, 3.1–3.5, 16.1–16.6_

- [x] 2. Implement Page Object classes
  - Created `tests/selenium/pages/__init__.py` with all exports
  - Created `tests/selenium/pages/base_page.py` with BasePage class (navigate, wait_for_element, get/set/remove localStorage, get_current_url)
  - Created `tests/selenium/pages/login_page.py` with LoginPage (login, get_error_message, is_submit_enabled)
  - Created `tests/selenium/pages/register_page.py` with RegisterPage (register, get_error_message, is_submit_enabled)
  - Created `tests/selenium/pages/dashboard_page.py` with DashboardPage (get_stat_cards, has_anomaly_card, has_forecast_chart, is_empty_state)
  - Created `tests/selenium/pages/forecast_page.py` with ForecastPage (select_horizon, get_bar_count, get_line_point_count, hover_bar, get_tooltip_text, get_error_message)
  - Created `tests/selenium/pages/ask_page.py` with AskPage (send_message, get_messages, clear_chat, is_send_enabled, get_input_length)
  - Created `tests/selenium/pages/data_entry_page.py` with DataEntryPage (add_entry, get_entry_rows, get_entry_count, edit_entry, delete_entry, confirm_dialog, cancel_dialog, upload_csv, train_model, get_training_status, clear_all_data, get_pagination_controls, click_next_page)
  - Created `tests/selenium/pages/price_calculator_page.py` with PriceCalculatorPage (enter_kwh, get_breakdown, get_rate_display, get_selected_bracket, select_bracket, change_customer_type, refresh_rate)
  - Created `tests/selenium/pages/account_settings_page.py` with AccountSettingsPage (change_password, get_success_message, get_error_message, set_customer_type, set_forecast_horizon, set_rate_override, clear_rate_override, set_chat_max_history, toggle_auto_clear, set_notification_thresholds, toggle_auto_retrain, set_min_data_points)
  - Created `tests/selenium/pages/sidebar.py` with Sidebar (navigate_to, get_active_link, click_logout, is_visible, open_mobile_menu, close_mobile_menu)
  - Created `tests/selenium/pages/top_bar.py` with TopBar (toggle_dark_mode, is_dark_mode, click_settings_icon, get_health_status)
  - _Requirements: 1.3_

- [x] 3. Implement Account System test module (test_account.py — ACT-01 to ACT-22)
  - [x] 3.1 Implement registration tests (ACT-01 to ACT-05)
    - `test_ACT_01_valid_registration`: Valid email/password → redirect to Dashboard, JWT in localStorage
    - `test_ACT_02_duplicate_email`: Duplicate email → error message, no redirect
    - `test_ACT_03_short_password`: Password <8 chars → Submit button disabled
    - `test_ACT_04_password_mismatch`: Mismatched confirm → Submit button disabled
    - `test_ACT_05_invalid_email_format`: Invalid email → error message displayed
    - Uses `driver` and `RegisterPage`; each test creates a fresh browser session
    - _Requirements: 4.1–4.5_

  - [x] 3.2 Implement login tests (ACT-06 to ACT-08)
    - `test_ACT_06_valid_login`: Valid credentials → redirect to Dashboard, JWT stored
    - `test_ACT_07_wrong_password`: Wrong password → "Invalid credentials" error, no token
    - `test_ACT_08_nonexistent_email`: Non-existent email → "Invalid credentials" error, no token
    - Uses `driver` and `LoginPage`
    - _Requirements: 4.6–4.7_

  - [x] 3.3 Implement session and auth tests (ACT-10, ACT-12, ACT-14, ACT-19, ACT-20)
    - `test_ACT_10_logout`: Click logout → token removed, redirect to Login
    - `test_ACT_12_session_persistence`: Refresh after login → remains on Dashboard
    - `test_ACT_14_invalid_token_redirect`: Set invalid JWT via JS → redirect to Login on protected navigation
    - `test_ACT_19_unauthenticated_protected_route`: Navigate to protected route without auth → redirect to Login
    - `test_ACT_20_authenticated_login_redirect`: Authenticated user visits /login or /register → redirect to Dashboard
    - Uses `logged_in_driver`, `unauthenticated_driver`, `Sidebar`, `LoginPage`
    - _Requirements: 4.8–4.10, 4.14–4.15_

  - [x] 3.4 Implement data isolation tests (ACT-15 to ACT-18)
    - `test_ACT_15_data_isolation_entries`: User A creates entries → User B cannot see them
    - `test_ACT_16_chat_isolation`: User A sends chat messages → User B cannot see them
    - `test_ACT_17_api_cross_user_forbidden`: User B targets User A's entry via API → 403 Forbidden
    - `test_ACT_18_model_isolation`: User A has trained model → User B sees "no model" state
    - Uses `logged_in_driver`, `second_user_driver`, `DataEntryPage`, `AskPage`, `ForecastPage`
    - _Requirements: 4.11–4.13_

  - [x] 3.5 Implement password change tests (ACT-21, ACT-22)
    - `test_ACT_21_valid_password_change`: Valid current + new password → success message, re-login with new password works
    - `test_ACT_22_wrong_current_password`: Incorrect current password → error message, password unchanged
    - Uses `logged_in_driver`, `AccountSettingsPage`, `LoginPage`, `Sidebar`
    - _Requirements: 4.16–4.17_

- [x] 4. Implement Data Management test module (test_data_management.py — DM-01 to DM-40)
  - [x] 4.1 Implement manual entry tests (DM-01 to DM-12)
    - `test_DM_01_valid_entry`: Valid month + kWh → success message, row appears in history
    - `test_DM_02_blank_kwh`: Empty kWh → error message, no new row
    - `test_DM_03_zero_kwh`: kWh=0 → error message, no new row
    - `test_DM_04_negative_kwh`: kWh=-100 → error message, no new row
    - `test_DM_05_non_numeric_kwh`: kWh="abc" → rejected or error, no entry created
    - `test_DM_06_minimum_valid_kwh`: kWh=1 → success, row with 1 kWh
    - `test_DM_07_maximum_valid_kwh`: kWh=1000000 → success, row with 1000000 kWh
    - `test_DM_08_exceeds_maximum_kwh`: kWh=1000001 → error message, no new row
    - `test_DM_09_kwh_with_bill_amount`: kWh + bill amount → both values in history row
    - `test_DM_10_kwh_with_rate_override`: kWh + rate override → entry saved with custom rate
    - `test_DM_11_bill_preview`: Type kWh → bill preview with ₱ appears within 5 seconds
    - `test_DM_12_duplicate_month`: Same month re-submitted → error, single row for that month
    - Uses `logged_in_driver`, `DataEntryPage`
    - _Requirements: 5.1–5.12_

  - [x] 4.2 Implement CSV upload tests (DM-13 to DM-21)
    - `test_DM_13_upload_valid_csv`: Valid 3-row CSV → success, 3 rows in history
    - `test_DM_14_upload_full_dataset`: Upload synthetic_2022_2025.csv (48 rows) → success, all rows visible
    - `test_DM_15_upload_non_csv`: .txt file → error message, no entries added
    - `test_DM_16_missing_column`: CSV missing "kwh" column → error, no entries
    - `test_DM_17_blank_kwh_values`: CSV with blank kWh → handled gracefully without crash
    - `test_DM_18_duplicate_months_csv`: CSV with duplicate months → only one row per month
    - `test_DM_19_invalid_date_format`: YYYY/MM format → error, no entries added
    - `test_DM_20_duplicate_upload`: Same CSV uploaded twice → entry count unchanged
    - `test_DM_21_upload_count_verification`: After upload → entry count label matches expected total
    - Uses `logged_in_driver`, `DataEntryPage`, `test_csv_path`, fixture CSV files
    - _Requirements: 6.1–6.9_

  - [x] 4.3 Implement edit and delete tests (DM-22 to DM-31)
    - `test_DM_22_edit_mode_display`: Click Edit → editable fields + Save/Cancel visible
    - `test_DM_23_edit_valid_kwh`: Enter 500, Save → row shows 500
    - `test_DM_24_edit_invalid_zero`: Enter 0, Save → error, original value preserved
    - `test_DM_25_edit_exceeds_max`: Enter 1000001, Save → error, original preserved
    - `test_DM_26_edit_cancel`: Click Cancel → original value unchanged
    - `test_DM_27_single_edit_mode`: Edit second row while first editing → only one editable
    - `test_DM_28_delete_confirmation`: Click Delete → confirmation dialog appears
    - `test_DM_29_delete_confirmed`: Accept delete → row removed, count decreases
    - `test_DM_30_delete_cancelled`: Cancel delete → row remains, count unchanged
    - `test_DM_31_delete_last_entry`: Delete only entry → empty state message shown
    - Uses `logged_in_driver`, `DataEntryPage`
    - _Requirements: 7.1–7.10_

  - [x] 4.4 Implement pagination tests (DM-32 to DM-35)
    - `test_DM_32_first_page_ten_rows`: >10 entries → first page shows exactly 10 rows
    - `test_DM_33_next_page_different_rows`: Click Next → different row set displayed
    - `test_DM_34_no_pagination_few_entries`: ≤10 entries → no pagination controls
    - `test_DM_35_entry_count_label`: Page load → count label matches total entries
    - Uses `logged_in_driver`, `DataEntryPage` (requires pre-seeded data via CSV upload fixture)
    - _Requirements: 8.1–8.4_

  - [x] 4.5 Implement model training and clear data tests (DM-36 to DM-40)
    - `test_DM_36_train_model_success`: ≥14 entries + Train → status: Idle → Training → Done (60s timeout)
    - `test_DM_37_train_empty_database`: No data + Train → error message, no status change
    - `test_DM_38_train_insufficient_data`: <14 entries + Train → error, training doesn't start
    - `test_DM_39_train_button_disabled_during_training`: While training → button disabled
    - `test_DM_40_clear_all_data`: Clear All + confirm → history empty, Forecast shows "no model"
    - Uses `logged_in_driver`, `DataEntryPage`, `ForecastPage`
    - _Requirements: 9.1–9.5_

- [x] 5. Implement Forecasting & Dashboard test module (test_forecast_dashboard.py — FD-01 to FD-20)
  - [x] 5.1 Implement forecasting tests (FD-01 to FD-11)
    - `test_FD_01_default_forecast`: Trained model → 3-bar kWh chart + 3-point bill line chart
    - `test_FD_02_horizon_one_month`: Select 1 month → 1 bar
    - `test_FD_03_horizon_six_months`: Select 6 months → 6 bars
    - `test_FD_04_horizon_nine_months`: Select 9 months → 9 bars
    - `test_FD_05_horizon_twelve_months`: Select 12 months → 12 bars
    - `test_FD_06_forecast_start_month`: Latest data Dec 2025 → first bar labelled "Jan 2026"
    - `test_FD_07_error_bars_visible`: Bars have visible error bars for 95% CI
    - `test_FD_08_confidence_band`: Bill chart has shaded confidence interval band
    - `test_FD_09_tooltip_on_hover`: Hover bar → tooltip with kWh value and CI bounds
    - `test_FD_10_no_model_error`: No trained model → error message instead of chart
    - `test_FD_11_empty_database_guidance`: Empty DB → guidance message to add data
    - Uses `default_account_driver` (trained model) and `logged_in_driver` (no model state), `ForecastPage`
    - _Requirements: 10.1–10.11_

  - [x] 5.2 Implement dashboard tests (FD-12 to FD-20)
    - `test_FD_12_stat_cards_displayed`: Trained model → 4 stat cards (This Month, Daily Average, Avg Temp, Avg Humidity)
    - `test_FD_13_this_month_value`: "This Month" card shows numeric kWh matching forecast
    - `test_FD_14_daily_average_value`: "Daily Average" ≈ This Month / 30 (±1 tolerance)
    - `test_FD_15_weather_values_range`: Temp 25–38°C, Humidity 50–95%
    - `test_FD_16_no_forecast_empty_state`: No model → empty state message directing to upload data
    - `test_FD_17_anomaly_card_visible`: Forecast > 110% mean → anomaly card/banner visible
    - `test_FD_18_no_anomaly_card`: Forecast ≤ 110% mean → no anomaly card in DOM
    - `test_FD_19_forecast_chart_container`: Forecast exists → chart container (canvas/SVG) visible
    - Uses `default_account_driver`, `logged_in_driver`, `DashboardPage`
    - _Requirements: 11.1–11.8_

- [x] 6. Implement Chat Assistant test module (test_chat.py — CHT-01 to CHT-11)
  - [x] 6.1 Implement chat tests (CHT-01 to CHT-11)
    - `test_CHT_01_valid_question`: Submit question → user bubble + streaming response within 30s
    - `test_CHT_02_forecast_context_response`: Question about forecast month → response references forecast data
    - `test_CHT_03_out_of_scope_question`: Unrelated question → decline message about electricity topics only
    - `test_CHT_04_empty_message_disabled`: Empty/whitespace input → Ask button disabled
    - `test_CHT_05_max_length_accepted`: 500-char message → accepted, response generated
    - `test_CHT_06_exceeds_max_length`: >500 chars → input stops accepting or counter red + button disabled
    - `test_CHT_07_navigation_persistence`: Navigate away and back → messages still displayed in order
    - `test_CHT_08_clear_chat`: Click Clear → all messages removed, empty state shown
    - `test_CHT_09_clear_persistence`: Clear + navigate away + return → chat remains empty
    - `test_CHT_11_history_on_refresh`: Hard refresh → previous messages loaded from DB in order
    - Uses `logged_in_driver`, `AskPage`, `Sidebar`
    - _Requirements: 12.1–12.10_

- [x] 7. Implement Price Calculator test module (test_price_calculator.py — PCT-01 to PCT-13)
  - [x] 7.1 Implement price calculator tests (PCT-01 to PCT-12)
    - `test_PCT_01_rate_display`: Page loads → Meralco rate in ₱/kWh (₱9–₱15) + timestamp
    - `test_PCT_02_valid_breakdown`: Enter 250 kWh → breakdown table with charge components + total
    - `test_PCT_03_zero_kwh`: Enter 0 → all zeros or hidden, no error
    - `test_PCT_04_negative_kwh`: Negative input → rejected or treated as zero
    - `test_PCT_05_minimum_kwh`: Enter 1 → breakdown with values > ₱0
    - `test_PCT_06_large_kwh`: Enter 9999 → proportional values, no overflow/NaN
    - `test_PCT_07_bracket_auto_selection`: Enter 350 → "301–400 kWh" bracket selected
    - `test_PCT_08_bracket_upper_boundary`: Enter 400 → "301–400 kWh" bracket (upper boundary)
    - `test_PCT_09_bracket_next_tier`: Enter 401 → "Over 400 kWh" bracket
    - `test_PCT_10_manual_bracket_recalculates`: Manually change bracket → breakdown recalculates
    - `test_PCT_11_customer_type_change`: Change customer type → brackets update, breakdown recalculates
    - `test_PCT_12_refresh_rate`: Click Refresh Rate → timestamp changes, breakdown recalculates
    - Uses `logged_in_driver`, `PriceCalculatorPage`
    - _Requirements: 13.1–13.12_

- [x] 8. Implement Settings test module (test_settings.py — SET-01 to SET-16)
  - [x] 8.1 Implement settings tests (SET-01 to SET-16)
    - `test_SET_01_navigate_via_bell_icon`: Click bell icon → navigates to /account
    - `test_SET_02_navigate_via_user_icon`: Click user icon → navigates to /account
    - `test_SET_03_customer_type_change`: Change customer type → confirmation, Price Calculator reflects change
    - `test_SET_04_default_forecast_horizon`: Change horizon → confirmation, persisted
    - `test_SET_05_valid_rate_override`: Enter 0.01–100 → confirmation, value retained
    - `test_SET_06_rate_override_max_clamp`: Enter >100 → clamped to 100
    - `test_SET_07_rate_override_clear`: Click Clear → input empty, override removed
    - `test_SET_08_max_chat_history`: Set 10–500 → confirmation, value persists
    - `test_SET_09_auto_clear_chat_on_logout`: Enable toggle, logout, login → Ask page has no messages
    - `test_SET_10_clear_chat_history_button`: Click Clear Chat + confirm → Ask page empty
    - `test_SET_11_clear_all_data_cancelled`: Clear All + cancel → Data Entry still has entries
    - `test_SET_12_kwh_budget_threshold_alert`: Set threshold (e.g., 200) → Forecast shows budget alert banner
    - `test_SET_13_threshold_max_clamp`: Enter >99999 → clamped to 99999
    - `test_SET_14_auto_retrain_toggle_persistence`: Enable auto-retrain → persists after reload
    - `test_SET_15_min_data_points`: Set 3–60 → saved, training rejected when below minimum
    - `test_SET_16_no_hamburger_desktop`: Viewport >767px → hamburger not visible, no overlay
    - Uses `logged_in_driver`, `AccountSettingsPage`, `TopBar`, `Sidebar`, `AskPage`, `DataEntryPage`, `ForecastPage`, `PriceCalculatorPage`
    - _Requirements: 14.1–14.15_

- [x] 9. Implement System & Infrastructure test module (test_system.py — SYS-01 to SYS-11)
  - [x] 9.1 Implement system tests (SYS-01 to SYS-09)
    - `test_SYS_01_dark_mode_toggle`: Click dark toggle → dark theme class applied
    - `test_SYS_02_light_mode_toggle`: Click light toggle from dark → dark class removed
    - `test_SYS_03_dark_mode_persistence`: Activate dark mode, refresh → dark class still present
    - `test_SYS_04_sidebar_navigation`: Click each nav link → URL updates, page content visible within 5s
    - `test_SYS_05_active_link_indicator`: Active page → corresponding link has active class/aria-current
    - `test_SYS_06_mobile_hamburger_menu`: Resize ≤767px → sidebar hidden, hamburger shown; click → sidebar visible
    - `test_SYS_07_mobile_overlay_close`: Click overlay while mobile sidebar open → sidebar closes
    - `test_SYS_08_mobile_escape_close`: Press Escape while mobile sidebar open → sidebar closes
    - `test_SYS_09_health_indicator_operational`: All services running → health indicator shows green/operational
    - Uses `logged_in_driver`, `TopBar`, `Sidebar`, `DashboardPage`
    - _Requirements: 15.1–15.10_

- [x] 10. Create test fixture CSV files for negative testing
  - [x] 10.1 Create fixture CSV files in `tests/selenium/fixtures/`
    - `valid_3_rows.csv`: Minimal valid CSV with year_month, kwh, price columns and 3 data rows
    - `non_csv_file.txt`: Plain text file for DM-15
    - `missing_kwh_column.csv`: CSV with year_month and price but no kwh column for DM-16
    - `blank_kwh_values.csv`: CSV with empty kWh cells for DM-17
    - `duplicate_months.csv`: CSV with repeated year_month values for DM-18
    - `invalid_date_format.csv`: CSV using YYYY/MM format for DM-19
    - _Requirements: 6.1–6.9_

- [x] 11. Checkpoint - Ensure all test modules are syntactically correct
  - Run `pytest --collect-only` to verify all tests are discovered without import errors
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Add manual-only test stubs with @pytest.mark.manual
  - [x] 12.1 Add manual test stubs to respective test modules
    - Add `@pytest.mark.manual` decorated stub functions for ACT-09, ACT-11, ACT-13, CHT-10, SYS-10, SYS-11, FD-20, PCT-13
    - Each stub has `pytest.skip(reason="...")` with explanation of why manual execution is required
    - Place stubs in their corresponding module file (e.g., ACT stubs in test_account.py)
    - _Requirements: Automation Limitations section_

- [x] 13. Integration wiring and final verification
  - [x] 13.1 Update pages/__init__.py exports and verify import chain
    - Ensure all page object classes are properly exported
    - Verify each test module can import from `tests.selenium.pages`
    - _Requirements: 1.1, 1.3_

  - [x] 13.2 Update pytest.ini markers for module names
    - Verify all 8 markers present: account, data_management, forecast_dashboard, chat, price_calculator, settings, system, manual
    - _Requirements: 1.5, 16.2_

  - [x] 13.3 Run pytest --collect-only to verify all tests discovered
    - Execute collection and verify all ~125 automated tests + 8 manual stubs are found
    - _Requirements: 16.4_

  - [x] 13.4 Verify HTML report generation
    - Run a small subset of tests and confirm `reports/report.html` is generated
    - _Requirements: 16.1, 16.3, 16.5_

- [x] 14. Final checkpoint - Ensure full suite is ready
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks 1 and 2 are already completed (project structure, configuration, and all page objects are implemented)
- Each test function follows naming convention: `test_<PREFIX>_<ID>_<description>`
- Each test function includes the original manual test case summary as its docstring
- Tests use page objects imported from `tests.selenium.pages`
- Property-based testing does NOT apply to this suite (UI automation is example-based)
- Manual-only tests (8 total) are stubbed with `@pytest.mark.manual` and `pytest.skip()`
- Fixtures handle test data setup (user creation, CSV upload) to avoid inter-test dependencies
- The `default_account_driver` fixture (wattif@gmail.com) has pre-existing trained model data for forecast/dashboard tests

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["3.1", "3.2", "4.1", "4.2", "10.1"] },
    { "id": 1, "tasks": ["3.3", "3.4", "3.5", "4.3", "4.4", "4.5", "6.1", "7.1"] },
    { "id": 2, "tasks": ["5.1", "5.2", "8.1", "9.1"] },
    { "id": 3, "tasks": ["12.1"] },
    { "id": 4, "tasks": ["13.1", "13.2", "13.3", "13.4"] }
  ]
}
```
