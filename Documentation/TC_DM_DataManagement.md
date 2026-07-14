# Test Cases — Data Management

**Module:** Module 2 — Data Management (Manual Entry, CSV Upload, Entry History, Model Training, Clear All Data)  
**Prefix:** DM  
**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

**Pre-condition:** The backend is running on port 8000 and the frontend is open in a browser. The Data Entry page is accessible.  
**Dependencies:** Backend endpoints for all CRUD operations; Meralco rate API for entry history rate display.  
**Test Priority:** High

---

## Manual Entry (DM-01 to DM-12)

### DM-01: Valid entry — correct month and kWh
**Summary:** Submitting a valid month and kWh value saves the entry.
**Test Steps:**
1. Go to Data Entry page.
2. Select month `2024-03`.
3. Type `350` in kWh field.
4. Click **Submit**.
**Test Data:** Month: `2024-03`, kWh: `350`
**Expected Result:** Success message. Entry appears in history.
**Status:** ⬜ Not Run

---

### DM-02: Invalid — kWh left blank
**Summary:** Submitting without kWh shows validation error.
**Test Steps:**
1. Select month `2024-04`. Leave kWh empty. Click **Submit**.
**Expected Result:** Error message. No entry added.
**Status:** ⬜ Not Run

---

### DM-03: Invalid — kWh = 0
**Summary:** Zero kWh rejected.
**Test Steps:**
1. Select month `2024-05`. Type `0`. Click **Submit**.
**Expected Result:** Error message. No entry added.
**Status:** ⬜ Not Run

---

### DM-04: Invalid — kWh = negative
**Summary:** Negative kWh rejected.
**Test Steps:**
1. Select month `2024-06`. Type `-100`. Click **Submit**.
**Expected Result:** Error message. No entry added.
**Status:** ⬜ Not Run

---

### DM-05: Invalid — kWh = text
**Summary:** Non-numeric kWh rejected.
**Test Steps:**
1. Select month `2024-07`. Type `abc`. Click **Submit**.
**Expected Result:** Field rejects letters or error shown. No entry added.
**Status:** ⬜ Not Run

---

### DM-06: Boundary — kWh = 1 (minimum valid)
**Summary:** Minimum valid value accepted.
**Test Steps:**
1. Select month `2024-08`. Type `1`. Click **Submit**.
**Expected Result:** Entry saved with 1 kWh.
**Status:** ⬜ Not Run

---

### DM-07: Boundary — kWh = 1,000,000 (maximum valid)
**Summary:** Maximum valid value accepted.
**Test Steps:**
1. Select month `2024-09`. Type `1000000`. Click **Submit**.
**Expected Result:** Entry saved.
**Status:** ⬜ Not Run

---

### DM-08: Boundary — kWh = 1,000,001 (exceeds max)
**Summary:** Value above max rejected.
**Test Steps:**
1. Select month `2024-10`. Type `1000001`. Click **Submit**.
**Expected Result:** Error message. No entry added.
**Status:** ⬜ Not Run

---

### DM-09: Valid entry with optional bill amount
**Summary:** Optional bill amount saves correctly.
**Test Steps:**
1. Select `2024-11`. Type `320` kWh. Type `4500` in bill field. Click **Submit**.
**Expected Result:** Entry saved with 320 kWh and ₱4,500.
**Status:** ⬜ Not Run

---

### DM-10: Valid entry with rate override
**Summary:** Custom rate used for calculation.
**Test Steps:**
1. Select `2024-12`. Type `280` kWh. Type `11.50` in rate override. Click **Submit**.
**Expected Result:** Entry saved using ₱11.50/kWh.
**Status:** ⬜ Not Run

---

### DM-11: ~~Live bill preview appears while typing~~ [REMOVED — Feature no longer exists]
**Summary:** ~~Estimated bill shown as kWh is typed.~~ The live "Est. bill" preview has been removed from the New Reading Form. The estimated rate and bill are only shown in Entry History after saving an entry.
**Status:** ⛔ N/A — Feature Removed

---

### DM-11b: Export CSV button appears and downloads file
**Summary:** "↓ Export CSV" button is visible in the Entry History section header when at least one entry exists, and clicking it downloads `wattif_bill_data.csv`.
**Test Steps:**
1. Ensure at least one entry exists in Entry History.
2. Verify the "↓ Export CSV" button is visible in the Entry History section header.
3. Click **↓ Export CSV**.
**Test Data:** Any existing entry (e.g., from DM-01)
**Expected Result:** File `wattif_bill_data.csv` is downloaded. Button is not shown when history is empty.
**Status:** ⬜ Not Run

---

### DM-12: Duplicate month rejected
**Summary:** Same month twice is rejected.
**Test Steps:**
1. Ensure entry exists for `2024-03`. Submit `2024-03` again with `400` kWh.
**Expected Result:** Error indicates record already exists. No duplicate created.
**Status:** ⬜ Not Run

---

## CSV Upload (DM-13 to DM-21)

### DM-13: Upload valid CSV with minimum columns
**Summary:** CSV with year_month, kwh, price uploads successfully.
**Test Steps:**
1. Create `test_min.csv` with 3 rows (year_month, kwh, price). Upload via Data Entry.
**Expected Result:** Success message. All 3 rows in history.
**Status:** ⬜ Not Run

---

### DM-14: Upload valid CSV with all extended columns
**Summary:** Full 48-row synthetic dataset uploads correctly.
**Test Steps:**
1. Upload `data/synthetic_2022_2025.csv`.
**Expected Result:** Success. All 48 rows in history.
**Status:** ⬜ Not Run

---

### DM-15: Upload invalid file type (.txt)
**Summary:** Non-CSV file rejected.
**Test Steps:**
1. Upload a `.txt` file.
**Expected Result:** Error: "Only CSV files are accepted." No entries added.
**Status:** ⬜ Not Run

---

### DM-16: Upload CSV missing required column
**Summary:** CSV without `kwh` column rejected.
**Test Steps:**
1. Create CSV with only `year_month` and `price`. Upload.
**Expected Result:** Error indicates missing column.
**Status:** ⬜ Not Run

---

### DM-17: Upload CSV with blank kWh (imputation)
**Summary:** Blank kWh row handled gracefully.
**Test Steps:**
1. Create CSV with one blank kWh row. Upload.
**Expected Result:** File processed without crash. Row skipped or imputed.
**Status:** ⬜ Not Run

---

### DM-18: Upload CSV with duplicate months (deduplication)
**Summary:** Duplicate months deduplicated.
**Test Steps:**
1. Create CSV with two rows for `2023-06`. Upload.
**Expected Result:** Only one row for `2023-06` in history.
**Status:** ⬜ Not Run

---

### DM-19: Upload CSV with invalid date format
**Summary:** Non-YYYY-MM date rejected.
**Test Steps:**
1. Create CSV with `2024/06` format. Upload.
**Expected Result:** Error indicates invalid date format.
**Status:** ⬜ Not Run

---

### DM-20: Re-upload same CSV (no duplicates)
**Summary:** Second upload of same file doesn't create duplicates.
**Test Steps:**
1. Upload `test_min.csv`. Note count. Upload again.
**Expected Result:** Row count unchanged after second upload.
**Status:** ⬜ Not Run

---

### DM-21: Uploaded rows visible in Entry History
**Summary:** All uploaded rows appear in paginated history.
**Test Steps:**
1. Upload `synthetic_2022_2025.csv`. Navigate through pages.
**Expected Result:** All 48 rows visible. Count label shows 48.
**Status:** ⬜ Not Run

---

## Entry History — Edit (DM-22 to DM-27)

### DM-22: Click Edit — inline form appears
**Summary:** Edit button transforms row to editable inputs.
**Test Steps:**
1. Click **Edit** on any row.
**Expected Result:** Row shows editable kWh and bill fields with Save/Cancel buttons.
**Status:** ⬜ Not Run

---

### DM-23: Edit kWh with valid value — save succeeds
**Summary:** Valid kWh edit saves.
**Test Steps:**
1. Click **Edit**. Change kWh to `500`. Click **Save**.
**Expected Result:** Row shows 500 kWh.
**Status:** ⬜ Not Run

---

### DM-24: Edit kWh with invalid value (0) — rejected
**Summary:** Zero kWh rejected during edit.
**Test Steps:**
1. Click **Edit**. Change kWh to `0`. Click **Save**.
**Expected Result:** Error. Original value preserved.
**Status:** ⬜ Not Run

---

### DM-25: Edit kWh above maximum (1,000,001) — rejected
**Summary:** Exceeding max during edit rejected.
**Test Steps:**
1. Click **Edit**. Type `1000001`. Click **Save**.
**Expected Result:** Error. Original value preserved.
**Status:** ⬜ Not Run

---

### DM-26: Cancel edit — original values restored
**Summary:** Cancel discards changes.
**Test Steps:**
1. Click **Edit**. Change kWh to `999`. Click **Cancel**.
**Expected Result:** Row shows original value. No changes saved.
**Status:** ⬜ Not Run

---

### DM-27: Edit second row while first is in edit mode
**Summary:** Only one row editable at a time.
**Test Steps:**
1. Click **Edit** on first row. Click **Edit** on second row.
**Expected Result:** First row auto-cancelled or second Edit disabled.
**Status:** ⬜ Not Run

---

## Entry History — Delete (DM-28 to DM-31)

### DM-28: Click Delete — confirmation appears
**Summary:** Delete shows confirmation before action.
**Test Steps:**
1. Click **Delete** on any row.
**Expected Result:** Confirmation dialog appears.
**Status:** ⬜ Not Run

---

### DM-29: Confirm delete — entry removed
**Summary:** Confirmed delete removes the row.
**Test Steps:**
1. Click **Delete**. Click **Yes, delete**.
**Expected Result:** Row removed. Entry count decreases by 1.
**Status:** ⬜ Not Run

---

### DM-30: Cancel delete — entry remains
**Summary:** Cancelled delete leaves data intact.
**Test Steps:**
1. Click **Delete**. Click **Cancel**.
**Expected Result:** Row remains. Nothing deleted.
**Status:** ⬜ Not Run

---

### DM-31: Delete last entry — empty state shown
**Summary:** Deleting the only entry shows empty state.
**Test Steps:**
1. Ensure only 1 entry. Delete and confirm.
**Expected Result:** History empty. Empty state message shown.
**Status:** ⬜ Not Run

---

## Pagination (DM-32 to DM-35)

### DM-32: First page shows 10 rows
**Summary:** Default page shows exactly 10 rows.
**Test Steps:**
1. Ensure >10 entries. Check first page.
**Expected Result:** Exactly 10 rows visible.
**Status:** ⬜ Not Run

---

### DM-33: Navigate to page 2 — different rows shown
**Summary:** Next page shows next set of entries.
**Test Steps:**
1. Click Next (›) button.
**Expected Result:** Rows 11–20 shown. Different from page 1.
**Status:** ⬜ Not Run

---

### DM-34: Exactly 10 entries — no pagination shown
**Summary:** Pagination hidden when ≤10 entries.
**Test Steps:**
1. Ensure exactly 10 entries.
**Expected Result:** No pagination controls visible.
**Status:** ⬜ Not Run

---

### DM-35: Entry count label matches total
**Summary:** Count label accurate.
**Test Steps:**
1. Ensure 48 entries. Check count label.
**Expected Result:** Label shows 48.
**Status:** ⬜ Not Run

---

## Model Training (DM-36 to DM-40)

### DM-36: Train with sufficient data — success
**Summary:** Training with ≥14 entries completes successfully.
**Test Steps:**
1. Ensure ≥14 entries. Click **Train Model**. Wait ~60s.
**Expected Result:** Status: Idle → Training → Done. Model info shows MAPE and training window.
**Status:** ⬜ Not Run

---

### DM-37: Train with no data — error
**Summary:** Training on empty database shows error.
**Test Steps:**
1. Clear all data. Click **Train Model**.
**Expected Result:** Error: "Not enough data." Status stays Idle.
**Status:** ⬜ Not Run

---

### DM-38: Train with <14 entries — error
**Summary:** Insufficient data (below minimum) rejected.
**Test Steps:**
1. Ensure only 5 entries. Click **Train Model**.
**Expected Result:** Error indicates insufficient data.
**Status:** ⬜ Not Run

---

### DM-39: Concurrent training prevented
**Summary:** Second click while training is blocked.
**Test Steps:**
1. Click **Train Model**. Immediately click again.
**Expected Result:** Button disabled or message "Training in progress."
**Status:** ⬜ Not Run

---

### DM-40: Clear All Data — confirmation and wipe
**Summary:** Clear All removes entries and model.
**Test Steps:**
1. Click **Clear All Data**. Click **Yes, clear everything**.
2. Check Entry History. Check Forecast page.
**Expected Result:** History empty. Forecast shows "no model" error.
**Status:** ⬜ Not Run
