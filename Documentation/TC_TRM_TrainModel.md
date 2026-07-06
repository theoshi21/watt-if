# Test Cases — Train Model

**Module:** Data Entry — Train Model
**Prefix:** TRM
**Document Version:** 1.0
**Date:** July 2026
**Prepared by:** QA Team

---

**Pre-condition:** Data exists in the database. At least 14 rows are needed for training.
**Dependencies:** Backend `/retrain` and `/status` endpoints must be reachable.
**Test Priority:** High

---

### TRM-01: Train Model with sufficient data
**Summary:** Clicking Train Model when enough data exists should start and complete training successfully.
**Test Steps:**
1. Ensure at least 14 entries exist in Entry History (upload `synthetic_2022_2025.csv` if needed).
2. On the Data Entry page, click **Train Model**.
3. Watch the status panel.
4. Wait for training to finish (up to ~60 seconds).
**Expected Result:** Status changes from "Idle" → "Training…" → "Done". The model info panel updates with MAPE, accuracy rating, and training window.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### TRM-02: Train Model with no data (empty database)
**Summary:** Clicking Train Model with an empty database should show a clear error, not crash.
**Test Steps:**
1. Ensure the database is empty (use Clear All Data if needed).
2. On the Data Entry page, click **Train Model**.
**Expected Result:** An error message is shown (e.g., "Not enough data to train the model"). Status does not change to "Training".
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### TRM-03: Train Model with fewer than 14 entries (boundary — insufficient data)
**Summary:** Training with fewer than the minimum required rows should fail gracefully.
**Test Steps:**
1. Ensure exactly 5 entries exist in the database.
2. Click **Train Model**.
**Test Data:** 5 entries in database (below the 14-row minimum)
**Expected Result:** An error message indicates insufficient data. Training does not start.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### TRM-04: Status changes to "Training…" immediately after clicking
**Summary:** The status indicator should update to "Training…" within a second of clicking Train Model.
**Test Steps:**
1. Ensure at least 14 entries exist.
2. Click **Train Model**.
3. Immediately observe the status label.
**Expected Result:** The status label reads "Training…" (or equivalent) within one second of clicking.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### TRM-05: Status changes to "Done" after training completes
**Summary:** After training finishes, the status should update to "Done" automatically.
**Test Steps:**
1. Click **Train Model** and wait for it to complete.
2. Observe the status label.
**Expected Result:** Status changes to "Done" (or "Trained"). No error message is shown.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### TRM-06: Model info panel updates after training
**Summary:** MAPE, accuracy rating, and training window should reflect the newly trained model.
**Test Steps:**
1. Note any existing values in the model info panel before training.
2. Click **Train Model** and wait for it to complete.
3. Check the model info panel again.
**Expected Result:** MAPE, accuracy rating, and training window (start and end months) are displayed and reflect the new model.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### TRM-07: Clicking Train Model while training is already in progress
**Summary:** A second training run should not be allowed while the first is still running.
**Test Steps:**
1. Click **Train Model** to start training.
2. Immediately click **Train Model** again before it finishes.
**Expected Result:** The button is disabled while training is in progress, or a message says "Training already in progress." A second training job is not queued.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
