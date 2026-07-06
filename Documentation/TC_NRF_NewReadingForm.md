# Test Cases — New Reading Form

**Module:** Data Entry — New Reading Form
**Prefix:** NRF
**Document Version:** 1.0
**Date:** July 2026
**Prepared by:** QA Team

---

**Pre-condition:** The backend is running on port 8000 and the frontend is open in a browser. The Data Entry page is visible.
**Dependencies:** Meralco rate API must be accessible for the live bill preview to appear.
**Test Priority:** High

---

### NRF-01: Valid entry — correct month and kWh
**Summary:** Submitting a valid month and kWh value saves the entry and shows it in Entry History.
**Test Steps:**
1. Go to the Data Entry page.
2. In the Month field, select `2024-03` (March 2024).
3. In the kWh field, type `350`.
4. Click **Submit**.
**Test Data:** Month: `2024-03`, kWh: `350`
**Expected Result:** A success message appears. The new entry (2024-03, 350 kWh) appears in the Entry History table.
**Post-condition:** One entry exists in Entry History for March 2024.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### NRF-02: Invalid — kWh left blank
**Summary:** Submitting the form without a kWh value should show a validation error.
**Test Steps:**
1. Go to the Data Entry page.
2. Select a valid month (e.g., `2024-04`).
3. Leave the kWh field empty.
4. Click **Submit**.
**Test Data:** Month: `2024-04`, kWh: _(blank)_
**Expected Result:** An error message is shown (e.g., "kWh is required"). No entry is added to history.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### NRF-03: Invalid — kWh = 0
**Summary:** A kWh value of zero should be rejected as invalid.
**Test Steps:**
1. Go to the Data Entry page.
2. Select a valid month (e.g., `2024-05`).
3. In the kWh field, type `0`.
4. Click **Submit**.
**Test Data:** Month: `2024-05`, kWh: `0`
**Expected Result:** An error message is shown. No entry is added.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### NRF-04: Invalid — kWh = negative number
**Summary:** A negative kWh value should be rejected.
**Test Steps:**
1. Go to the Data Entry page.
2. Select a valid month (e.g., `2024-06`).
3. In the kWh field, type `-100`.
4. Click **Submit**.
**Test Data:** Month: `2024-06`, kWh: `-100`
**Expected Result:** An error message is shown. No entry is added.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### NRF-05: Invalid — kWh = text value
**Summary:** A non-numeric kWh value should be rejected.
**Test Steps:**
1. Go to the Data Entry page.
2. Select a valid month (e.g., `2024-07`).
3. In the kWh field, type `abc`.
4. Click **Submit**.
**Test Data:** Month: `2024-07`, kWh: `abc`
**Expected Result:** The field does not accept letters, or an error message is shown. No entry is added.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### NRF-06: Boundary — kWh = 1 (minimum valid)
**Summary:** A kWh value of 1 should be the minimum accepted value.
**Test Steps:**
1. Go to the Data Entry page.
2. Select a valid month (e.g., `2024-08`).
3. In the kWh field, type `1`.
4. Click **Submit**.
**Test Data:** Month: `2024-08`, kWh: `1`
**Expected Result:** Entry is accepted and saved. It appears in Entry History with 1 kWh.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### NRF-07: Boundary — kWh = 1,000,000 (maximum valid)
**Summary:** A kWh value of 1,000,000 should be the maximum accepted value.
**Test Steps:**
1. Go to the Data Entry page.
2. Select a valid month (e.g., `2024-09`).
3. In the kWh field, type `1000000`.
4. Click **Submit**.
**Test Data:** Month: `2024-09`, kWh: `1000000`
**Expected Result:** Entry is accepted and saved. It appears in Entry History with 1,000,000 kWh.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### NRF-08: Boundary — kWh = 1,000,001 (exceeds maximum)
**Summary:** A kWh value just above the maximum should be rejected.
**Test Steps:**
1. Go to the Data Entry page.
2. Select a valid month (e.g., `2024-10`).
3. In the kWh field, type `1000001`.
4. Click **Submit**.
**Test Data:** Month: `2024-10`, kWh: `1000001`
**Expected Result:** An error message is shown. No entry is added.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### NRF-09: Valid entry with optional bill amount override
**Summary:** Providing an optional bill amount saves both values correctly.
**Test Steps:**
1. Go to the Data Entry page.
2. Select `2024-11` as the month.
3. In the kWh field, type `320`.
4. Expand **Optional overrides** and type `4500` in the Actual Bill Amount field.
5. Click **Submit**.
**Test Data:** Month: `2024-11`, kWh: `320`, Bill Amount: `4500`
**Expected Result:** Entry is saved. Entry History shows 320 kWh and ₱4,500 for that month.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### NRF-10: Valid entry with optional rate override
**Summary:** Providing a custom rate per kWh uses that rate for the bill calculation.
**Test Steps:**
1. Go to the Data Entry page.
2. Select `2024-12` as the month.
3. In the kWh field, type `280`.
4. Expand **Optional overrides** and type `11.50` in the Rate Override field.
5. Click **Submit**.
**Test Data:** Month: `2024-12`, kWh: `280`, Rate Override: `11.50`
**Expected Result:** Entry is saved. The bill is calculated using ₱11.50/kWh rather than the auto-resolved rate.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### NRF-11: Live bill preview appears as kWh is typed
**Summary:** An estimated bill should be shown below the kWh field as the user types.
**Test Steps:**
1. Go to the Data Entry page.
2. Click into the kWh field.
3. Type `250`.
4. Observe the area below the kWh field.
**Test Data:** kWh: `250`
**Expected Result:** An estimated bill (e.g., "Est. bill: ₱2,950.00 @ ₱11.80/kWh") appears while typing, based on the live Meralco rate.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### NRF-12: Submitting the same month twice
**Summary:** Entering a month that already has a record should be rejected or handled gracefully.
**Test Steps:**
1. Ensure an entry already exists for `2024-03` (from NRF-01, or add one first).
2. In the New Reading form, select `2024-03` as the month.
3. Type `400` in the kWh field.
4. Click **Submit**.
**Test Data:** Month: `2024-03` (duplicate), kWh: `400`
**Expected Result:** An error is shown indicating a record for that month already exists. No duplicate is created in Entry History.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
