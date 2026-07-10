# Requirements Document

## Introduction

This document defines the requirements for a Python Selenium automation testing suite with ChromeDriver for the WATT-IF application. The suite automates the existing manual black-box test cases documented in the project's `Documentation/` folder, covering all 7 consolidated test modules: Account System (ACT), Data Management (DM), Forecasting & Dashboard (FD), Chat Assistant (CHT), Price Calculator (PCT), Settings (SET), and System & Infrastructure (SYS). The suite uses pytest as the test runner, Selenium WebDriver with ChromeDriver for browser automation, and targets the locally-hosted WATT-IF application (frontend on port 5173, backend on port 8000). The total test coverage spans 133 test cases across 7 modules, with approximately 125 automated and 8 requiring manual execution.

## Reference Test Case Documents

The automation suite SHALL implement automated equivalents of the following pre-existing manual test case documents. Each automated test function SHALL reference the corresponding manual test case ID in its docstring or test name:

| Document | Prefix | Module | Test Cases |
|----------|--------|--------|------------|
| `Documentation/TC_ACT_AccountSystem.md` | ACT | Account System | ACT-01 through ACT-22 |
| `Documentation/TC_DM_DataManagement.md` | DM | Data Management | DM-01 through DM-40 |
| `Documentation/TC_FD_ForecastDashboard.md` | FD | Forecasting & Dashboard | FD-01 through FD-20 |
| `Documentation/TC_CHT_Chat.md` | CHT | Chat Assistant | CHT-01 through CHT-11 |
| `Documentation/TC_PCT_PriceCalculator.md` | PCT | Price Calculator | PCT-01 through PCT-13 |
| `Documentation/TC_SET_Settings.md` | SET | Settings | SET-01 through SET-16 |
| `Documentation/TC_SYS_SystemInfrastructure.md` | SYS | System & Infrastructure | SYS-01 through SYS-11 |

## Automation Limitations

The following test cases involve actions that cannot be fully automated using Selenium WebDriver with ChromeDriver and will be excluded or only partially covered:

| Test Case | Reason for Exclusion |
|-----------|---------------------|
| ACT-09 (Rate limiting) | Requires 11 rapid login attempts; may be flaky due to timing-dependent rate limit windows |
| ACT-11 (Logout offline) | Requires simulating network disconnect mid-session; Selenium cannot toggle real network state reliably |
| ACT-13 (Expired token) | Requires waiting 24 hours or manually tampering with JWT expiry; partially automatable via JavaScript execution to modify localStorage |
| CHT-10 (Ollama offline) | Requires stopping an external service (Ollama); not automatable within Selenium alone |
| SYS-10 (Health degraded — Ollama offline) | Requires stopping Ollama service; not automatable within Selenium |
| SYS-11 (Offline banner) | Requires disconnecting the network; Chrome DevTools Protocol can simulate this but is not standard Selenium |
| FD-20 (Loading skeleton with throttled network) | Requires network throttling via DevTools; not reliably automatable with standard Selenium |
| PCT-13 (Calculator with API unavailable) | Requires disconnecting internet mid-test; not automatable within Selenium |

These test cases remain in the manual test plan for human execution. The automation suite will include a `pytest.mark.manual` marker for skipped tests with a reason annotation explaining why they require manual execution.

## Glossary

- **Test_Suite**: The complete collection of pytest-based Selenium automation tests organized by module across 7 test files
- **Test_Runner**: The pytest framework responsible for discovering, executing, and reporting test results
- **WebDriver**: The Selenium ChromeDriver instance that controls the Chrome browser for test execution
- **Page_Object**: A class encapsulating element locators and interaction methods for a specific page of the WATT-IF application
- **Fixture**: A pytest fixture providing reusable setup and teardown logic (e.g., authenticated browser session, clean database state)
- **Base_URL**: The root URL of the WATT-IF frontend application, defaulting to `http://localhost:5173`
- **API_URL**: The root URL of the WATT-IF backend API, defaulting to `http://localhost:8000`
- **Test_User**: A user account created specifically for test execution, isolated from the Default Account
- **Default_Account**: The pre-existing account with email `wattif@gmail.com` and password `wattif`
- **Explicit_Wait**: A Selenium WebDriverWait condition that pauses execution until an element meets a specified condition or a timeout is reached
- **Headless_Mode**: A ChromeDriver configuration where the browser runs without a visible UI window, suitable for CI pipelines
- **Conftest**: The pytest conftest.py file containing shared fixtures and configuration hooks

## Requirements

### Requirement 1: Project Structure and Configuration

**User Story:** As a developer, I want a well-organized test project structure with proper configuration, so that tests are easy to discover, run, and maintain.

#### Acceptance Criteria

1. THE Test_Suite SHALL organize test files in a `tests/selenium/` directory at the project root with one test module file per consolidated module: `test_account.py` (ACT), `test_data_management.py` (DM), `test_forecast_dashboard.py` (FD), `test_chat.py` (CHT), `test_price_calculator.py` (PCT), `test_settings.py` (SET), `test_system.py` (SYS)
2. THE Test_Suite SHALL include a `tests/selenium/conftest.py` file containing shared pytest fixtures for WebDriver initialization (with configurable explicit wait of 10 seconds), authentication (login as the Default Account `wattif@gmail.com`/`wattif`), and test data setup (upload of `data/synthetic_2022_2025.csv` when required by a test module)
3. THE Test_Suite SHALL include a `tests/selenium/pages/` directory containing Page Object classes for each application page (LoginPage, RegisterPage, DashboardPage, ForecastPage, AskPage, DataEntryPage, PriceCalculatorPage, AccountSettingsPage)
4. THE Test_Suite SHALL include a `requirements.txt` file listing all Python dependencies with pinned versions (selenium, pytest, pytest-html, webdriver-manager)
5. THE Test_Suite SHALL include a `pytest.ini` or `pyproject.toml` configuration specifying the test path as `tests/selenium/`, markers for each module (`account`, `data_management`, `forecast_dashboard`, `chat`, `price_calculator`, `settings`, `system`, `manual`), and default options including HTML report generation and verbose output
6. WHEN the `--headless` command-line option is passed, THE WebDriver SHALL run Chrome in headless mode
7. IF the `BASE_URL` environment variable is not set, THEN THE Test_Suite SHALL default to `http://localhost:5173`; IF the `API_URL` environment variable is not set, THEN THE Test_Suite SHALL default to `http://localhost:8000`
8. THE Test_Suite SHALL name each test function using the format `test_<PREFIX>_<ID>_<description>` (e.g., `test_ACT_01_valid_registration`, `test_DM_13_upload_valid_csv`) to map directly to the pre-existing manual test case IDs in the Documentation/ folder
9. THE Test_Suite SHALL include the original test case summary from the Documentation/ files as the docstring of each automated test function

### Requirement 2: WebDriver Management and Browser Setup

**User Story:** As a tester, I want ChromeDriver to be automatically managed and configured, so that I do not need to manually download or update driver binaries.

#### Acceptance Criteria

1. THE WebDriver SHALL use webdriver-manager to automatically download and cache the correct ChromeDriver binary matching the installed Chrome version
2. THE WebDriver SHALL configure Chrome with a window size of 1920x1080 for desktop tests
3. THE WebDriver SHALL set an implicit wait of 0 seconds and rely on Explicit_Wait conditions with a default timeout of 10 seconds
4. THE WebDriver SHALL disable Chrome's automation detection flags (disable-blink-features=AutomationControlled)
5. WHEN a test fails, THE Fixture SHALL capture a screenshot as a PNG file and embed it in the HTML report
6. WHEN all tests in a session complete, THE WebDriver SHALL quit the browser and release all resources
7. IF WebDriver initialization fails (e.g., Chrome not installed, ChromeDriver incompatible), THEN THE Fixture SHALL skip all dependent tests with a clear error message rather than crashing the test run

### Requirement 3: Authentication Fixtures

**User Story:** As a tester, I want reusable authentication fixtures, so that tests requiring a logged-in session can share setup logic without duplicating login steps.

#### Acceptance Criteria

1. THE Conftest SHALL provide a `logged_in_driver` fixture that registers a unique Test_User via the API, logs in through the UI, and yields an authenticated WebDriver instance
2. THE Conftest SHALL provide a `default_account_driver` fixture that logs in as the Default_Account (wattif@gmail.com / wattif) through the UI
3. WHEN a test using `logged_in_driver` completes, THE Fixture SHALL clean up the Test_User's data via the API
4. THE Conftest SHALL provide an `unauthenticated_driver` fixture that yields a WebDriver with no stored authentication token
5. THE Conftest SHALL provide a `second_user_driver` fixture for data isolation tests, creating a separate Test_User account

### Requirement 4: Account System Tests (ACT-01 to ACT-22)

**User Story:** As a QA engineer, I want automated tests covering registration, login, logout, session persistence, data isolation, and password change (ACT-01 through ACT-22), so that authentication flows are verified on every test run.

#### Acceptance Criteria

1. WHEN valid registration credentials are submitted (email, password ≥8 chars, matching confirm password), THE Test_Suite SHALL verify the user is redirected to the Dashboard and a JWT token exists in localStorage under the key "wattif_token" (ACT-01)
2. WHEN a duplicate email is submitted for registration, THE Test_Suite SHALL verify an error message is displayed and no redirect occurs (ACT-02)
3. WHEN a password shorter than 8 characters is entered, THE Test_Suite SHALL verify the Submit button is disabled (ACT-03)
4. WHEN password and confirm-password fields do not match, THE Test_Suite SHALL verify the Submit button is disabled (ACT-04)
5. WHEN an invalid email format is submitted for registration, THE Test_Suite SHALL verify an error message is displayed (ACT-05)
6. WHEN valid credentials are submitted on the Login page, THE Test_Suite SHALL verify redirect to Dashboard and that a JWT token is stored in localStorage under the key "wattif_token" (ACT-06)
7. WHEN incorrect credentials are submitted on the Login page (wrong password or non-existent email), THE Test_Suite SHALL verify a generic "Invalid credentials" error message is displayed, no token is stored in localStorage, and the user remains on the Login page (ACT-07, ACT-08)
8. WHEN the Logout button is clicked, THE Test_Suite SHALL verify the "wattif_token" key is removed from localStorage and the browser is redirected to the Login page (ACT-10)
9. WHEN the page is refreshed after login, THE Test_Suite SHALL verify the user remains authenticated on the Dashboard (ACT-12)
10. WHEN an invalid token is manually set in localStorage via JavaScript execution, THE Test_Suite SHALL verify the user is redirected to the Login page upon navigating to a protected page that triggers an API call (ACT-14)
11. WHEN User A creates data entries and chat messages, THE Test_Suite SHALL verify User B cannot see User A's entries in Entry History nor User A's messages on the Ask page after logging in with a separate account (ACT-15, ACT-16)
12. WHEN User B sends a PUT or DELETE request targeting User A's data entry ID using User B's valid token, THE Test_Suite SHALL verify the API returns HTTP 403 Forbidden and User A's entry remains unchanged (ACT-17)
13. WHEN User A has a trained model and User B has no data, THE Test_Suite SHALL verify User B cannot access User A's forecast and instead sees an indication that no trained model is available (ACT-18)
14. WHEN an unauthenticated user navigates to a protected route, THE Test_Suite SHALL verify redirect to the Login page (ACT-19)
15. WHEN an authenticated user navigates to /login or /register, THE Test_Suite SHALL verify redirect back to the Dashboard (ACT-20)
16. WHEN valid current password and new password (≥8 chars with matching confirmation) are provided on the Account Settings page, THE Test_Suite SHALL verify a success message is displayed and the user can log out and log back in using the new password (ACT-21)
17. WHEN an incorrect current password is provided for password change, THE Test_Suite SHALL verify an error message indicating the current password is incorrect is displayed and the password remains unchanged (ACT-22)

### Requirement 5: Data Management Tests — Manual Entry (DM-01 to DM-12)

**User Story:** As a QA engineer, I want automated tests for manual data entry covering valid inputs, invalid inputs, and boundary values (DM-01 through DM-12), so that data entry validation is continuously verified.

#### Acceptance Criteria

1. WHEN a valid month (e.g., 2024-03) and kWh value (e.g., 350) are submitted on the Data Entry page, THE Test_Suite SHALL verify that a success message element is visible within 10 seconds and the Entry History table contains a row displaying the submitted month and kWh value (DM-01)
2. WHEN the kWh field is left blank and the form is submitted, THE Test_Suite SHALL verify an error message element is visible and the Entry History table row count has not increased (DM-02)
3. WHEN kWh is set to 0 and the form is submitted, THE Test_Suite SHALL verify the form displays an error message and no new entry appears in Entry History (DM-03)
4. WHEN kWh is set to -100 and the form is submitted, THE Test_Suite SHALL verify the form displays an error message and no new entry appears in Entry History (DM-04)
5. WHEN a non-numeric value (e.g., "abc") is entered in the kWh field and the form is submitted, THE Test_Suite SHALL verify that either the field value remains empty (input rejected at keystroke level) or an error message is displayed after submission, and no entry is created (DM-05)
6. WHEN kWh is set to 1 (minimum valid boundary) and a valid month is submitted, THE Test_Suite SHALL verify a success message appears and the Entry History table contains a row with 1 kWh (DM-06)
7. WHEN kWh is set to 1000000 (maximum valid boundary) and a valid month is submitted, THE Test_Suite SHALL verify a success message appears and the Entry History table contains a row with 1000000 kWh (DM-07)
8. WHEN kWh is set to 1000001 (exceeds maximum) and the form is submitted, THE Test_Suite SHALL verify the form displays an error message and no new entry appears in Entry History (DM-08)
9. WHEN a valid kWh and optional bill amount (e.g., 4500) are submitted together, THE Test_Suite SHALL verify both the kWh and bill amount values are displayed in the corresponding Entry History row (DM-09)
10. WHEN a valid kWh and rate override value (e.g., 11.50) are submitted together, THE Test_Suite SHALL verify the entry is saved using the custom rate (DM-10)
11. WHEN a valid kWh value (e.g., 250) is typed into the kWh field, THE Test_Suite SHALL verify that a bill preview element containing a currency value (₱) becomes visible within 5 seconds below the kWh input (DM-11)
12. WHEN a month that already has an entry in Entry History is submitted again, THE Test_Suite SHALL verify an error message indicating a duplicate record is displayed and Entry History still contains only one row for that month (DM-12)

### Requirement 6: Data Management Tests — CSV Upload (DM-13 to DM-21)

**User Story:** As a QA engineer, I want automated tests for CSV upload covering valid files, invalid files, and edge cases (DM-13 through DM-21), so that bulk data import is continuously verified.

#### Acceptance Criteria

1. WHEN a valid CSV with minimum required columns (year_month, kwh, price) and 3 data rows is uploaded, THE Test_Suite SHALL verify a success message is displayed and all 3 rows appear in Entry History (DM-13)
2. WHEN a valid CSV with all extended columns and 48 rows (`data/synthetic_2022_2025.csv`) is uploaded, THE Test_Suite SHALL verify a success message is displayed and all 48 rows are visible in Entry History (DM-14)
3. WHEN a non-CSV file (e.g., .txt) is uploaded, THE Test_Suite SHALL verify an error message is shown and no entries are added to Entry History (DM-15)
4. WHEN a CSV missing a required column (e.g., kwh) is uploaded, THE Test_Suite SHALL verify an error message indicating the missing column is displayed and no entries are added (DM-16)
5. WHEN a CSV with blank kWh values is uploaded, THE Test_Suite SHALL verify the application processes the file without crashing and handles the row gracefully (DM-17)
6. WHEN a CSV with duplicate months is uploaded, THE Test_Suite SHALL verify only one row per month exists in Entry History (DM-18)
7. WHEN a CSV with an invalid date format (e.g., YYYY/MM instead of YYYY-MM) is uploaded, THE Test_Suite SHALL verify an error message is displayed and no entries are added (DM-19)
8. WHEN the same CSV is uploaded a second time, THE Test_Suite SHALL verify the entry count in Entry History remains unchanged compared to after the first upload (DM-20)
9. WHEN a successful upload completes, THE Test_Suite SHALL verify all rows from the CSV appear in Entry History and the entry count label matches the expected total (DM-21)

### Requirement 7: Data Management Tests — Edit and Delete (DM-22 to DM-31)

**User Story:** As a QA engineer, I want automated tests for editing and deleting entries in the history table (DM-22 through DM-31), so that CRUD operations on individual records are verified.

#### Acceptance Criteria

1. WHEN the Edit button is clicked on a row, THE Test_Suite SHALL verify the row displays editable input fields for kWh and bill amount, along with Save and Cancel buttons (DM-22)
2. WHEN a valid kWh value (e.g., 500) is entered in the edit field and Save is clicked, THE Test_Suite SHALL verify the row exits edit mode and displays the updated kWh value (DM-23)
3. WHEN an invalid kWh value (0) is entered during edit and Save is clicked, THE Test_Suite SHALL verify an error message is shown and the original value is preserved (DM-24)
4. WHEN a kWh value exceeding maximum (1000001) is entered during edit and Save is clicked, THE Test_Suite SHALL verify an error message is shown and the original value is preserved (DM-25)
5. WHEN the Cancel button is clicked during an active edit, THE Test_Suite SHALL verify the row exits edit mode and displays the original kWh value unchanged (DM-26)
6. WHEN Edit is clicked on a second row while the first row is already in edit mode, THE Test_Suite SHALL verify only one row is editable at a time (DM-27)
7. WHEN the Delete button is clicked on a row, THE Test_Suite SHALL verify a confirmation dialog appears before any deletion occurs (DM-28)
8. WHEN the delete confirmation is accepted, THE Test_Suite SHALL verify the row is removed from Entry History and the total entry count decreases by 1 (DM-29)
9. WHEN the delete confirmation is cancelled, THE Test_Suite SHALL verify the row remains in Entry History and the entry count is unchanged (DM-30)
10. WHEN the last remaining entry is deleted and confirmed, THE Test_Suite SHALL verify Entry History displays an empty state message and no rows are shown (DM-31)

### Requirement 8: Data Management Tests — Pagination (DM-32 to DM-35)

**User Story:** As a QA engineer, I want automated tests for the pagination controls (DM-32 through DM-35), so that navigation through large data sets is verified.

#### Acceptance Criteria

1. WHEN more than 10 entries exist in Entry History, THE Test_Suite SHALL verify the first page displays exactly 10 rows (DM-32)
2. WHEN the Next Page button (›) is clicked, THE Test_Suite SHALL verify the table displays a different set of rows than the previous page (DM-33)
3. WHEN 10 or fewer entries exist in Entry History, THE Test_Suite SHALL verify pagination controls are not displayed (DM-34)
4. WHEN the Data Entry page is loaded, THE Test_Suite SHALL verify the entry count label displays the correct total number of entries matching the database (DM-35)

### Requirement 9: Data Management Tests — Model Training (DM-36 to DM-40)

**User Story:** As a QA engineer, I want automated tests for the model training and data clearing features (DM-36 through DM-40), so that training status transitions and destructive operations are verified.

#### Acceptance Criteria

1. WHEN at least 14 entries exist in Entry History and the Train Model button is clicked, THE Test_Suite SHALL verify the status transitions from "Idle" to "Training" to "Done" within 60 seconds (DM-36)
2. WHEN the database is empty and the Train Model button is clicked, THE Test_Suite SHALL verify an error message indicating insufficient data is displayed and the status does not change to "Training" (DM-37)
3. WHEN fewer than 14 entries exist and the Train Model button is clicked, THE Test_Suite SHALL verify an error message indicating insufficient data is displayed and training does not start (DM-38)
4. WHILE training is in progress (status shows "Training"), THE Test_Suite SHALL verify the Train Model button is disabled and cannot be clicked to start a concurrent training job (DM-39)
5. WHEN the Clear All Data button is clicked and confirmation is accepted, THE Test_Suite SHALL verify Entry History is empty and the Forecast page shows a "no model" error (DM-40)

### Requirement 10: Forecasting & Dashboard Tests — Forecasting (FD-01 to FD-11)

**User Story:** As a QA engineer, I want automated tests for the Forecast page covering horizon selection, chart rendering, and error states (FD-01 through FD-11), so that forecasting functionality is verified.

#### Acceptance Criteria

1. WHEN the Forecast page loads with a trained model, THE Test_Suite SHALL verify a kWh bar chart with 3 bars and a bill line chart with 3 data points are displayed by default (FD-01)
2. WHEN the 1-month horizon is selected, THE Test_Suite SHALL verify the kWh bar chart updates to display exactly 1 bar (FD-02)
3. WHEN the 6-month horizon is selected, THE Test_Suite SHALL verify the kWh bar chart updates to display exactly 6 bars (FD-03)
4. WHEN the 9-month horizon is selected, THE Test_Suite SHALL verify the kWh bar chart updates to display exactly 9 bars (FD-04)
5. WHEN the 12-month horizon is selected, THE Test_Suite SHALL verify the kWh bar chart updates to display exactly 12 bars (FD-05)
6. WHEN the Forecast page loads with the latest data entry being December 2025, THE Test_Suite SHALL verify the first forecast bar is labelled "Jan 2026" (FD-06)
7. WHEN the kWh bar chart is displayed, THE Test_Suite SHALL verify each bar has visible error bars representing the 95% confidence interval (FD-07)
8. WHEN the bill line chart is displayed, THE Test_Suite SHALL verify a shaded confidence interval band is rendered around the line (FD-08)
9. WHEN a kWh chart bar is hovered, THE Test_Suite SHALL verify a tooltip appears displaying the forecasted kWh value and the lower/upper CI bounds (FD-09)
10. IF no trained model exists, THEN THE Test_Suite SHALL verify an error message indicating no model is available is displayed instead of a chart (FD-10)
11. IF the database is completely empty with no data and no model, THEN THE Test_Suite SHALL verify a guidance message directing the user to add data is displayed (FD-11)

### Requirement 11: Forecasting & Dashboard Tests — Dashboard (FD-12 to FD-20)

**User Story:** As a QA engineer, I want automated tests for the Dashboard covering stat cards, anomaly detection, chart rendering, and empty states (FD-12 through FD-20), so that the main overview page is verified.

#### Acceptance Criteria

1. WHEN the Dashboard loads with a trained model, THE Test_Suite SHALL verify four stat cards are displayed with labels: This Month, Daily Average, Avg Temp, Avg Humidity, each containing a numeric value (FD-12)
2. WHEN the "This Month" card is displayed, THE Test_Suite SHALL verify it shows a numeric kWh value matching the first forecast month's predicted consumption (FD-13)
3. WHEN the "Daily Average" card is displayed, THE Test_Suite SHALL verify it shows a value approximately equal to the "This Month" kWh divided by 30 (within ±1 kWh/day rounding tolerance) (FD-14)
4. WHEN the Avg Temp and Avg Humidity cards are displayed, THE Test_Suite SHALL verify temperature is between 25–38°C and humidity is between 50–95% (FD-15)
5. WHEN no forecast data is available (no trained model exists), THE Test_Suite SHALL verify an empty state message element is displayed directing the user to upload data (FD-16)
6. WHEN the first forecast month kWh exceeds 110% of the mean across all forecast months, THE Test_Suite SHALL verify an anomaly card or banner element is visible on the Dashboard (FD-17)
7. WHEN the first forecast month kWh is at or below 110% of the mean, THE Test_Suite SHALL verify no anomaly card element is present in the DOM (FD-18)
8. WHEN a forecast exists, THE Test_Suite SHALL verify a forecast chart container element (canvas or SVG) is rendered and visible on the Dashboard (FD-19)

**Note:** FD-20 (Loading skeleton with throttled network) requires network throttling via DevTools and is excluded from automation. It remains a manual test.

### Requirement 12: Chat Assistant Tests (CHT-01 to CHT-11)

**User Story:** As a QA engineer, I want automated tests for the chat assistant covering message submission, response streaming, history persistence, and error handling (CHT-01 through CHT-11), so that the RAG chat feature is verified.

#### Acceptance Criteria

1. WHEN a valid question is submitted, THE Test_Suite SHALL verify the question appears in the chat as a user bubble and a streaming response completes without error within 30 seconds (CHT-01)
2. WHEN a question about a specific forecast month is submitted, THE Test_Suite SHALL verify the response references relevant forecast data (CHT-02)
3. WHEN an out-of-scope question unrelated to electricity is submitted, THE Test_Suite SHALL verify the assistant responds with a message declining to answer and indicating it can only help with electricity and billing topics (CHT-03)
4. WHEN the message input field is empty or contains only whitespace, THE Test_Suite SHALL verify the Ask button is disabled and clicking it produces no effect (CHT-04)
5. WHEN a message at exactly 500 characters is submitted, THE Test_Suite SHALL verify it is accepted and a response is generated without a character limit error (CHT-05)
6. WHEN a message exceeding 500 characters is entered, THE Test_Suite SHALL verify the input field stops accepting characters beyond the 500-character maximum or the counter turns red and the Ask button is disabled (CHT-06)
7. WHEN the user navigates away from the Ask page and returns without a full page reload, THE Test_Suite SHALL verify all previous question and response messages are still displayed in their original order (CHT-07)
8. WHEN the Clear Chat button is clicked, THE Test_Suite SHALL verify all messages are removed from the chat view and the empty-state prompt is displayed (CHT-08)
9. WHEN the chat has been cleared and the user navigates away and returns, THE Test_Suite SHALL verify the chat remains empty with no previous messages reappearing (CHT-09)
10. WHEN the page is loaded fresh via hard refresh with existing chat history in the database, THE Test_Suite SHALL verify previous messages are loaded and displayed in chronological order on page mount (CHT-11)

**Note:** CHT-10 (Ollama offline error) requires stopping an external service and is excluded from automation. It remains a manual test.

### Requirement 13: Price Calculator Tests (PCT-01 to PCT-13)

**User Story:** As a QA engineer, I want automated tests for the Price Calculator covering input handling, bracket logic, and bill breakdown (PCT-01 through PCT-13), so that billing calculations are verified.

#### Acceptance Criteria

1. WHEN the Price Calculator page loads, THE Test_Suite SHALL verify a Meralco rate value in ₱/kWh is displayed along with a last-updated timestamp, and the rate value is between ₱9.00 and ₱15.00 per kWh (PCT-01)
2. WHEN a valid kWh value of 250 is entered, THE Test_Suite SHALL verify a bill breakdown table appears showing individual charge components (generation, transmission, system loss, distribution, supply, metering, and other charges) plus a total bill amount (PCT-02)
3. WHEN 0 kWh is entered, THE Test_Suite SHALL verify the breakdown either shows all zero values or is hidden, and no error is thrown (PCT-03)
4. IF a negative kWh value is entered, THEN THE Test_Suite SHALL verify the input field does not accept the negative sign or the value is treated as zero with no bill calculated (PCT-04)
5. WHEN 1 kWh is entered, THE Test_Suite SHALL verify a breakdown is shown with charge values greater than ₱0 and no error occurs (PCT-05)
6. WHEN 9999 kWh is entered, THE Test_Suite SHALL verify the breakdown displays proportionally scaled values with no overflow, NaN values, or rendering errors (PCT-06)
7. WHEN 350 kWh is entered, THE Test_Suite SHALL verify the bracket selector automatically shows the "301–400 kWh" bracket selected (PCT-07)
8. WHEN 400 kWh is entered, THE Test_Suite SHALL verify the bracket selector still shows the "301–400 kWh" bracket selected (upper boundary) (PCT-08)
9. WHEN 401 kWh is entered, THE Test_Suite SHALL verify the bracket selector automatically changes to the "Over 400 kWh" tier (PCT-09)
10. WHEN a different bracket is manually selected while a kWh value is entered, THE Test_Suite SHALL verify the bill breakdown recalculates using the manually selected bracket's rates and the total bill amount changes (PCT-10)
11. WHEN the customer type is changed from the default, THE Test_Suite SHALL verify the bracket options list updates for the new customer type and the bill breakdown recalculates (PCT-11)
12. WHEN the Refresh Rate button is clicked, THE Test_Suite SHALL verify the rate last-updated timestamp changes and the bill breakdown recalculates with the refreshed rate (PCT-12)

**Note:** PCT-13 (Calculator with API unavailable) requires disconnecting internet mid-test and is excluded from automation. It remains a manual test.

### Requirement 14: Settings Page Tests (SET-01 to SET-16)

**User Story:** As a QA engineer, I want automated tests for the Settings page covering all user preferences, notification thresholds, model retraining, and data privacy actions (SET-01 through SET-16), so that application configuration is verified.

#### Acceptance Criteria

1. WHEN the bell icon or user icon in the top bar is clicked, THE Test_Suite SHALL verify the browser navigates to the Settings page URL (/account) and the settings sections are visible (SET-01, SET-02)
2. WHEN the customer type dropdown is changed, THE Test_Suite SHALL verify a confirmation message appears and the Price Calculator page pre-selects the chosen customer type (SET-03)
3. WHEN the default forecast horizon is changed, THE Test_Suite SHALL verify a confirmation message appears and the selection is persisted (SET-04)
4. WHEN a valid rate override value between 0.01 and 100 is entered and the input loses focus, THE Test_Suite SHALL verify a confirmation message appears and the value is retained in the input field (SET-05)
5. WHEN the rate override value exceeds 100, THE Test_Suite SHALL verify the input value is clamped to 100 (SET-06)
6. WHEN the rate override Clear button is clicked, THE Test_Suite SHALL verify the input field becomes empty and the override is removed (SET-07)
7. WHEN the max chat history value is set to a value between 10 and 500, THE Test_Suite SHALL verify a confirmation message appears and the value persists in the input (SET-08)
8. WHEN the auto-clear chat on logout toggle is enabled and the user logs out and back in, THE Test_Suite SHALL verify the Ask WATT-IF page shows no previous messages (SET-09)
9. WHEN the Clear Chat History button is clicked and the confirmation is accepted, THE Test_Suite SHALL verify the Ask WATT-IF page shows no messages (SET-10)
10. WHEN Clear All Data is triggered and the confirmation is cancelled, THE Test_Suite SHALL verify Data Entry page still shows existing entries (SET-11)
11. WHEN a kWh budget notification threshold is set (e.g., 200), THE Test_Suite SHALL verify the Forecast page shows a budget alert banner when the forecast exceeds the threshold (SET-12)
12. WHEN a notification threshold value exceeds 99,999 kWh, THE Test_Suite SHALL verify the value is clamped to 99,999 (SET-13)
13. WHEN the auto-retrain toggle is enabled, THE Test_Suite SHALL verify the setting persists after page reload with the toggle in the enabled state (SET-14)
14. WHEN the minimum data points value is set to a value between 3 and 60, THE Test_Suite SHALL verify the value is saved and training is rejected when data is below the minimum (SET-15)
15. WHILE the viewport width is greater than 767px, THE Test_Suite SHALL verify the hamburger menu button is not visible and no overlay element is displayed (SET-16)

### Requirement 15: System & Infrastructure Tests (SYS-01 to SYS-11)

**User Story:** As a QA engineer, I want automated tests for dark/light mode, sidebar navigation, mobile responsiveness, and the health indicator (SYS-01 through SYS-11), so that cross-cutting UI and system behaviors are verified.

#### Acceptance Criteria

1. WHEN the dark mode toggle is clicked, THE Test_Suite SHALL verify the page body or root element has a dark theme CSS class applied (SYS-01)
2. WHEN the light mode toggle is clicked from dark mode, THE Test_Suite SHALL verify the dark theme class is removed from the root element, restoring light theme (SYS-02)
3. WHEN dark mode is activated and the page is refreshed, THE Test_Suite SHALL verify the dark theme class is still present on the root element after reload (SYS-03)
4. WHEN each sidebar navigation link is clicked (Dashboard, Forecast, Ask WATT-IF, Price Calculator, Data Entry), THE Test_Suite SHALL verify the URL path updates to the corresponding route and a page-specific heading or container element is visible within 5 seconds (SYS-04)
5. WHEN a page is active, THE Test_Suite SHALL verify the corresponding sidebar link has a distinct CSS class or aria-current attribute indicating the active state (SYS-05)
6. WHEN the browser viewport is resized to mobile width (≤767px), THE Test_Suite SHALL verify the sidebar is not visible and a hamburger menu button is displayed (SYS-06)
7. WHEN the hamburger menu is clicked on mobile viewport (≤767px), THE Test_Suite SHALL verify the sidebar element becomes visible (SYS-06)
8. WHEN the overlay is clicked while the mobile sidebar is open, THE Test_Suite SHALL verify the sidebar element is no longer visible (SYS-07)
9. WHEN the Escape key is pressed while the mobile sidebar is open, THE Test_Suite SHALL verify the sidebar element closes (SYS-08)
10. WHEN all backend systems are running (FastAPI and Ollama), THE Test_Suite SHALL verify the health indicator element displays all status indicators with a green or "operational" state (SYS-09)

**Note:** SYS-10 (Health degraded — Ollama offline) and SYS-11 (Offline banner) require stopping external services or disconnecting the network and are excluded from automation. They remain manual tests.

### Requirement 16: Test Reporting and Execution

**User Story:** As a developer, I want comprehensive test reporting with HTML output and pytest markers, so that test results are easy to review and tests can be selectively executed by module.

#### Acceptance Criteria

1. THE Test_Suite SHALL generate an HTML test report using pytest-html at a configurable output path (defaulting to `reports/report.html`) after each test run
2. THE Test_Suite SHALL use pytest markers to categorize tests by module: `@pytest.mark.account`, `@pytest.mark.data_management`, `@pytest.mark.forecast_dashboard`, `@pytest.mark.chat`, `@pytest.mark.price_calculator`, `@pytest.mark.settings`, `@pytest.mark.system`, `@pytest.mark.manual`
3. WHEN a test fails, THE Test_Suite SHALL capture a browser screenshot as a PNG file and embed it in the HTML report as a base64 image or linked file
4. THE Test_Suite SHALL support running a single module via marker selection (e.g., `pytest -m account`, `pytest -m data_management`)
5. THE Test_Suite SHALL include test execution duration for each test case in the HTML report output
6. IF a WebDriver connection fails during test setup, THEN THE Test_Suite SHALL skip the affected tests with a pytest.skip message indicating the WebDriver connection failure reason rather than crashing the entire run
