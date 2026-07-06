# Test Cases — CSV Upload

**Module:** Data Entry — CSV Upload
**Prefix:** CSU
**Document Version:** 1.0
**Date:** July 2026
**Prepared by:** QA Team

---

**Pre-condition:** The backend is running on port 8000. A valid CSV file has been prepared on the test machine.
**Dependencies:** Backend `/upload` endpoint must be reachable.
**Test Priority:** High

---

### CSU-01: Upload valid CSV with minimum required columns
**Summary:** A CSV with only the required columns (year_month, kwh, price) should upload successfully.
**Test Steps:**
1. Create a file named `test_min.csv` with the following content:
   ```
   year_month,kwh,price
   2023-01,342,4210
   2023-02,310,3890
   2023-03,295,3750
   ```
2. Go to the Data Entry page.
3. Click **Choose CSV** and select `test_min.csv`.
**Test Data:** `test_min.csv` — 3 rows, columns: year_month, kwh, price
**Expected Result:** A success message appears. All 3 rows are visible in Entry History.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CSU-02: Upload valid CSV with all extended columns
**Summary:** A CSV with all 12 extended columns should upload and populate Entry History correctly.
**Test Steps:**
1. Use the provided file `data/synthetic_2022_2025.csv` (48 rows, all extended columns).
2. Go to the Data Entry page.
3. Click **Choose CSV** and select `synthetic_2022_2025.csv`.
4. Check Entry History after the upload.
**Test Data:** `synthetic_2022_2025.csv` — 48 rows, all 12 columns
**Expected Result:** Success message shown. All 48 rows appear in Entry History with correct values.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CSU-03: Upload invalid file type (.txt)
**Summary:** Uploading a non-CSV file should be rejected with a clear error message.
**Test Steps:**
1. Rename a text file to `test_file.txt`.
2. Go to the Data Entry page.
3. Click **Choose CSV** and select `test_file.txt`.
**Test Data:** A `.txt` file
**Expected Result:** An error message is shown (e.g., "Only CSV files are accepted"). No entries are added.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CSU-04: Upload CSV missing a required column (no kwh column)
**Summary:** A CSV that is missing the `kwh` column should be rejected.
**Test Steps:**
1. Create a file named `test_missing_kwh.csv` with the following content:
   ```
   year_month,price
   2023-01,4210
   2023-02,3890
   ```
2. Go to the Data Entry page.
3. Click **Choose CSV** and select `test_missing_kwh.csv`.
**Test Data:** `test_missing_kwh.csv` — missing `kwh` column
**Expected Result:** An error message indicates a required column is missing. No entries are added.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CSU-05: Upload CSV with blank kWh values (imputation test)
**Summary:** A CSV row with a blank kWh value should be imputed or skipped rather than crashing.
**Test Steps:**
1. Create a file named `test_blank_kwh.csv` with the following content:
   ```
   year_month,kwh,price
   2023-04,,4100
   2023-05,300,3800
   ```
2. Go to the Data Entry page.
3. Click **Choose CSV** and select `test_blank_kwh.csv`.
**Test Data:** `test_blank_kwh.csv` — one blank kWh cell
**Expected Result:** The file is processed without crashing. The blank row is either skipped with a warning or the kWh is imputed. No error page is shown.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CSU-06: Upload CSV with duplicate months (deduplication test)
**Summary:** A CSV with two rows for the same month should keep only one.
**Test Steps:**
1. Create a file named `test_dupe.csv` with the following content:
   ```
   year_month,kwh,price
   2023-06,310,3900
   2023-06,320,4000
   2023-07,295,3750
   ```
2. Go to the Data Entry page.
3. Upload `test_dupe.csv`.
4. Check Entry History for `2023-06`.
**Test Data:** `test_dupe.csv` — two rows for `2023-06`
**Expected Result:** Only one row for `2023-06` appears in Entry History. No crash or error.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CSU-07: Upload CSV with invalid date format
**Summary:** A CSV using a non-standard date format should fail with a clear error.
**Test Steps:**
1. Create a file named `test_bad_date.csv` with the following content:
   ```
   year_month,kwh,price
   2024/06,310,3900
   ```
2. Go to the Data Entry page.
3. Upload `test_bad_date.csv`.
**Test Data:** `test_bad_date.csv` — date in `YYYY/MM` format instead of `YYYY-MM`
**Expected Result:** An error indicates the date format is invalid. No entries are added.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CSU-08: Re-upload the same CSV (no duplicate entries)
**Summary:** Uploading the same file a second time should not create duplicate rows in Entry History.
**Test Steps:**
1. Upload `test_min.csv` successfully (from CSU-01). Note the row count.
2. Upload `test_min.csv` again.
3. Check the row count in Entry History.
**Expected Result:** The row count does not increase after the second upload. No duplicates are created.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### CSU-09: Verify uploaded rows appear in Entry History
**Summary:** After a successful upload, all rows from the CSV should be visible in Entry History.
**Test Steps:**
1. Upload `data/synthetic_2022_2025.csv` (48 rows).
2. Navigate through the Entry History pages.
3. Verify the total count shown.
**Expected Result:** All 48 rows from the CSV appear in Entry History. The entry count label reads 48.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
