# Test Cases — Clear All Data

**Module:** Data Entry — Clear All Data
**Prefix:** CAD
**Document Version:** 1.0
**Date:** July 2026
**Prepared by:** QA Team

---

**Pre-condition:** Data exists in the database. A trained model artefact may also exist.
**Dependencies:** Backend `/data/all` DELETE endpoint must be reachable.
**Test Priority:** High

---

### CAD-01: Click "Clear All Data…" — confirmation panel appears
**Summary:** Clicking the Clear All Data button should show a confirmation step before deleting anything.
**Test Steps:**
1. Go to the Data Entry page.
2. Scroll to the Danger Zone section.
3. Click **Clear All Data…**.
**Expected Result:** A confirmation panel appears warning that all data will be permanently deleted and asking the user to confirm.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CAD-02: Confirm clear — all entries are removed and table is empty
**Summary:** Confirming the clear operation should wipe all entries from Entry History.
**Test Steps:**
1. Click **Clear All Data…**.
2. In the confirmation panel, click **Yes, clear everything**.
3. Check Entry History.
**Expected Result:** Entry History is empty. An empty state message is shown. The total entry count shows 0.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CAD-03: Cancel clear — data remains intact
**Summary:** Cancelling the confirmation should leave all data untouched.
**Test Steps:**
1. Click **Clear All Data…**.
2. In the confirmation panel, click **Cancel**.
3. Check Entry History.
**Expected Result:** All entries remain. No data was deleted.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CAD-04: Model is unloaded after clearing (forecast returns an error)
**Summary:** After clearing all data, the trained model should be removed, so the Forecast page should show an error.
**Test Steps:**
1. Train a model first (TRM-01).
2. Verify the Forecast page shows a chart.
3. Go back to Data Entry and clear all data (CAD-02).
4. Go to the Forecast page and try to generate a forecast.
**Expected Result:** The Forecast page shows an error or message (e.g., "No trained model found"). It does not show a stale forecast from before the clear.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CAD-05: Upload new data after clearing — works normally
**Summary:** After clearing, the app should accept a fresh upload without issues.
**Test Steps:**
1. Clear all data (CAD-02).
2. Upload `data/synthetic_2022_2025.csv`.
3. Check Entry History.
**Expected Result:** The upload succeeds. All 48 rows appear in Entry History. No error from the previous cleared state.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CAD-06: Clear All Data on an already empty database
**Summary:** Clearing when the database is already empty should not cause an error.
**Test Steps:**
1. Ensure the database is empty (or clear it first).
2. Click **Clear All Data…** and confirm.
**Expected Result:** The operation completes without any error. Entry History remains empty. No crash or error message.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
