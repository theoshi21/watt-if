# Test Cases — Edit Entry

**Module:** Data Entry — Entry History (Edit)
**Prefix:** EDE
**Document Version:** 1.0
**Date:** July 2026
**Prepared by:** QA Team

---

**Pre-condition:** At least one entry exists in Entry History.
**Dependencies:** Backend `/data-entries/{id}` PUT endpoint must be reachable.
**Test Priority:** High

---

### EDE-01: Click Edit — inline edit row appears
**Summary:** Clicking the Edit button on a row should transform it into an editable inline form.
**Test Steps:**
1. Go to the Data Entry page.
2. Locate any row in Entry History.
3. Click the **Edit** button for that row.
**Expected Result:** The row changes to show editable input fields for kWh and bill amount, with Save and Cancel buttons.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### EDE-02: Edit kWh with a valid value — save succeeds
**Summary:** Changing kWh to a valid number and saving should update the entry in the table.
**Test Steps:**
1. Click **Edit** on any row.
2. Clear the kWh field and type `500`.
3. Click **Save**.
**Test Data:** kWh: `500`
**Expected Result:** The row exits edit mode and displays 500 kWh.
**Post-condition:** Entry History shows 500 kWh for that month.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### EDE-03: Edit kWh with invalid value (0) — error shown
**Summary:** Setting kWh to 0 during edit should not be saved.
**Test Steps:**
1. Click **Edit** on any row.
2. Clear the kWh field and type `0`.
3. Click **Save**.
**Test Data:** kWh: `0`
**Expected Result:** An error message is shown. The original value is preserved. The row is not saved.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### EDE-04: Edit kWh with boundary value (1,000,000)
**Summary:** Setting kWh to exactly 1,000,000 during edit should save successfully.
**Test Steps:**
1. Click **Edit** on any row.
2. Clear the kWh field and type `1000000`.
3. Click **Save**.
**Test Data:** kWh: `1000000`
**Expected Result:** The row is saved and displays 1,000,000 kWh. No error.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### EDE-05: Edit kWh with value just above maximum (1,000,001)
**Summary:** Setting kWh to 1,000,001 during edit should be rejected.
**Test Steps:**
1. Click **Edit** on any row.
2. Clear the kWh field and type `1000001`.
3. Click **Save**.
**Test Data:** kWh: `1000001`
**Expected Result:** An error message is shown. The original value is preserved.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### EDE-06: Clear bill amount (set to blank) — saves as null
**Summary:** Deleting the bill amount during edit and saving should store it as empty without errors.
**Test Steps:**
1. Click **Edit** on a row that has a bill amount value.
2. Clear the Bill Amount field completely.
3. Click **Save**.
**Expected Result:** The row is saved. The Bill Amount column shows `—` for that entry. No error is thrown.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### EDE-07: Cancel edit — original values are restored
**Summary:** Clicking Cancel on an in-progress edit should discard all changes.
**Test Steps:**
1. Click **Edit** on any row.
2. Change the kWh to a different value (e.g., `999`).
3. Click **Cancel**.
**Expected Result:** The row exits edit mode showing the original kWh value. No changes are saved.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### EDE-08: Click Edit on a second row while one is already in edit mode
**Summary:** Attempting to edit two rows at the same time should be handled gracefully.
**Test Steps:**
1. Click **Edit** on the first row — it enters edit mode.
2. Without saving or cancelling, click **Edit** on a different row.
**Expected Result:** Either the first row is automatically cancelled and the second enters edit mode, or the second Edit button is disabled. Two rows should not be in edit mode at the same time.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
