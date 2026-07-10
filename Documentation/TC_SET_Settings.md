# Test Cases — Settings

**Module:** Module 6 — Settings (User Preferences, Notifications, Model Retraining, Data & Privacy)  
**Prefix:** SET  
**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

**Pre-condition:** The backend is running on port 8000, the frontend is open in a browser, and the user is logged in. The Settings page is accessible via the user account icon in the top bar or by navigating to `/account`.
**Dependencies:** None (settings are independent of trained model state).
**Test Priority:** High

---

## Navigation & Access

### SET-01: Settings page accessible via account icon
**Summary:** Clicking the user account icon in the top bar navigates to the Settings page.
**Test Steps:**
1. Log in to the application.
2. Click the user account icon (circle) in the top-right corner of the top bar.
**Test Data:** N/A
**Expected Result:** The browser navigates to the Settings page (`/account`). All settings sections are visible: Customer Type, Default Forecast Horizon, Rate Override, Chat Preferences, Data & Privacy, Notification Thresholds, Model Retraining, Account, Change Password, and Session.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:** The bell/notification icon was removed in the UI redesign. Settings is now accessed exclusively via the user account button.

---

### SET-02: Settings page accessible via user icon
**Summary:** Clicking the user circle icon in the top bar navigates to the Settings page (same entry point as SET-01).
**Test Steps:**
1. Log in to the application.
2. Click the user circle icon in the top-right corner of the top bar.
**Test Data:** N/A
**Expected Result:** The browser navigates to the Settings page (`/account`).
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Customer Type

### SET-03: Change customer type — Residential to General Service A
**Summary:** Selecting a different customer type saves immediately and pre-selects in the Price Calculator.
**Test Steps:**
1. Navigate to the Settings page.
2. In the "Customer Type" section, change the dropdown from "Residential" to "General Service A".
3. Wait for the "Customer type saved" confirmation.
4. Navigate to the Price Calculator page.
5. Observe the Customer Type dropdown value.
**Test Data:** Customer type: General Service A
**Expected Result:** The dropdown value is saved. On the Price Calculator page, the Customer Type dropdown is pre-selected as "General Service A".
**Post-condition:** User's customer_type setting is "General Service A".
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Default Forecast Horizon

### SET-04: Change default forecast horizon to 6 months
**Summary:** Selecting a different horizon saves and pre-selects on the Forecast page.
**Test Steps:**
1. Navigate to the Settings page.
2. In the "Default Forecast Horizon" section, change the dropdown to "6 months".
3. Wait for the "Forecast horizon saved" confirmation.
4. Clear browser localStorage entry for forecast state (or log out and back in).
5. Navigate to the Forecast page.
**Test Data:** Horizon: 6
**Expected Result:** The Forecast page uses 6-month horizon as the default when no saved forecast exists.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Electricity Rate Override

### SET-05: Set a rate override — valid value
**Summary:** Entering a valid rate saves it and is used when adding new data entries.
**Test Steps:**
1. Navigate to the Settings page.
2. In the "Electricity Rate Override" section, type `12.50` in the Rate input.
3. Click outside the input (blur).
4. Wait for the "Rate override saved" confirmation.
5. Navigate to Data Entry, add a manual entry for a future month.
6. Observe the resolved Meralco rate in the Entry History.
**Test Data:** Rate: 12.50 ₱/kWh
**Expected Result:** The rate override is saved. New data entries use ₱12.50/kWh instead of the scraped rate.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### SET-06: Rate override — boundary value (max 100)
**Summary:** Entering a value above 100 is clamped to 100.
**Test Steps:**
1. Navigate to the Settings page.
2. In the "Electricity Rate Override" input, type `150`.
3. Click outside the input.
**Test Data:** Rate: 150
**Expected Result:** The value is clamped to 100 and saved as 100. The input does not accept values beyond the screen width.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### SET-07: Clear rate override
**Summary:** Clicking "Clear" removes the override and restores auto-scraped rate behavior.
**Test Steps:**
1. Navigate to the Settings page.
2. Ensure a rate override is set (e.g., 12.50).
3. Click the "Clear" button next to the rate input.
4. Wait for the confirmation message.
**Test Data:** N/A
**Expected Result:** The rate override is removed (input is empty). New data entries will use the live Meralco rate.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Chat Preferences

### SET-08: Set max chat history — valid value within bounds
**Summary:** Entering a value between 10 and 500 saves correctly.
**Test Steps:**
1. Navigate to the Settings page.
2. In "Chat Preferences", change the "Max messages shown" to `50`.
3. Click outside the input.
**Test Data:** Max messages: 50
**Expected Result:** The value is saved. The "Chat preferences saved" confirmation appears.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### SET-09: Auto-clear chat on logout — toggle and verify
**Summary:** Enabling auto-clear wipes chat history when the user logs out.
**Test Steps:**
1. Navigate to the Ask WATT-IF page and send at least one message.
2. Navigate to the Settings page.
3. In "Chat Preferences", toggle "Auto-clear chat on logout" ON.
4. Wait for the confirmation message.
5. Click Logout (at the bottom of the Settings page or in the sidebar).
6. Log back in with the same account.
7. Navigate to the Ask WATT-IF page.
**Test Data:** N/A
**Expected Result:** After logging back in, the Ask page shows no previous messages. The chat history was cleared during logout.
**Post-condition:** Chat history table for this user is empty.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Data & Privacy

### SET-10: Clear chat history — with confirmation
**Summary:** Clearing chat history requires confirmation and wipes all messages.
**Test Steps:**
1. Send at least one message on the Ask WATT-IF page.
2. Navigate to the Settings page.
3. Click "Clear Chat History".
4. Observe the confirmation prompt ("Are you sure?").
5. Click "Yes, clear".
6. Navigate to the Ask WATT-IF page.
**Test Data:** N/A
**Expected Result:** After confirming, the chat history is wiped. The Ask page shows no previous messages.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### SET-11: Clear all data — cancel does nothing
**Summary:** Clicking "Clear All Data & Model" and then cancelling leaves data intact.
**Test Steps:**
1. Ensure at least one data entry exists.
2. Navigate to the Settings page.
3. Click "Clear All Data & Model".
4. Observe the confirmation prompt.
5. Click "Cancel".
6. Navigate to Data Entry page.
**Test Data:** N/A
**Expected Result:** The confirmation prompt disappears. Data entries remain intact on the Data Entry page.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Notification Thresholds

### SET-12: Set kWh budget — valid value and forecast warning
**Summary:** Setting a kWh budget triggers a warning when the forecast exceeds it.
**Test Steps:**
1. Navigate to the Settings page.
2. In "Notification Thresholds", type `200` in the "Monthly kWh budget" input.
3. Click outside the input.
4. Navigate to the Forecast page.
5. Generate a forecast (assumes model is trained and typical consumption is above 200 kWh).
**Test Data:** kWh budget: 200
**Expected Result:** The budget is saved. On the Forecast page, a yellow "Budget Alerts" banner appears showing months where the forecast exceeds 200 kWh.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### SET-13: Notification input — boundary value (max 99,999 kWh)
**Summary:** kWh budget input does not accept values beyond 99,999.
**Test Steps:**
1. Navigate to the Settings page.
2. In "Notification Thresholds", type `100000` in the "Monthly kWh budget" input.
3. Click outside the input.
**Test Data:** kWh budget: 100000
**Expected Result:** The value is clamped to 99,999 and saved. The input value does not extend beyond the input field's visual boundary.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Model Retraining

### SET-14: Auto-retrain on upload toggle
**Summary:** Enabling auto-retrain causes the model to retrain automatically after CSV upload.
**Test Steps:**
1. Navigate to the Settings page.
2. In "Model Retraining", toggle "Auto-retrain on CSV upload" ON.
3. Navigate to Data Entry page.
4. Upload a CSV file with at least 12 months of data.
5. Observe the training status indicator.
**Test Data:** Auto-retrain: enabled, CSV with ≥12 rows
**Expected Result:** After the upload completes, the training status automatically transitions to "Training" without the user manually clicking "Train Model".
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### SET-15: Minimum data points — retrain rejected with insufficient data
**Summary:** If the user has fewer data points than the configured minimum, retraining is blocked.
**Test Steps:**
1. Navigate to the Settings page.
2. In "Model Retraining", set "Minimum data points before training" to `24`.
3. Ensure the user has fewer than 24 months of data (e.g., upload a CSV with only 10 rows).
4. Navigate to Data Entry page.
5. Click "Train Model".
**Test Data:** Min data points: 24, Actual data points: 10
**Expected Result:** A 422 error message is shown: "Not enough data to train. You have 10 month(s) but need at least 24. Adjust this in Settings."
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Desktop Overlay Bug Fix Verification

### SET-16: Hamburger menu does not darken screen on desktop
**Summary:** Clicking the hamburger menu button on desktop does not show the overlay.
**Test Steps:**
1. Open the application in a desktop browser (viewport width > 767px).
2. Observe that the sidebar is already visible on the left.
3. If the hamburger icon is visible (inspect element or resize), click it.
4. Observe the screen background.
**Test Data:** Viewport: > 767px
**Expected Result:** On desktop, the hamburger button is hidden (not visible). The overlay (dark background) does not appear. The sidebar is always visible without needing the burger menu.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---
