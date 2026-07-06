# Test Cases — Pagination

**Module:** Data Entry — Entry History Pagination
**Prefix:** PGN
**Document Version:** 1.0
**Date:** July 2026
**Prepared by:** QA Team

---

**Pre-condition:** More than 10 entries exist in Entry History. Upload `synthetic_2022_2025.csv` (48 rows) to satisfy this.
**Dependencies:** None beyond the backend being running.
**Test Priority:** Medium

---

### PGN-01: First page shows exactly 10 rows
**Summary:** The default view of Entry History should show exactly 10 rows per page.
**Test Steps:**
1. Ensure at least 11 entries exist.
2. Go to the Data Entry page.
3. Count the rows visible in Entry History.
**Expected Result:** Exactly 10 rows are shown on the first page.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PGN-02: Navigate to page 2 — different rows are shown
**Summary:** Clicking the Next button should load the next set of entries.
**Test Steps:**
1. Ensure at least 11 entries exist.
2. On the Data Entry page, click the **›** (Next page) button.
**Expected Result:** The table updates to show rows 11–20 (or fewer if only 11–N entries exist). These rows are different from page 1.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PGN-03: Navigate to the last page — only remaining rows shown
**Summary:** The last page should show only the leftover rows, not a full 10.
**Test Steps:**
1. Ensure 48 entries exist (upload `synthetic_2022_2025.csv`).
2. Navigate to the last page (page 5 for 48 entries).
**Expected Result:** The last page shows exactly 8 rows (48 mod 10 = 8). No blank/empty rows are padded.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PGN-04: Boundary — exactly 10 entries shows no pagination
**Summary:** With exactly 10 entries, no pagination controls should be displayed.
**Test Steps:**
1. Ensure exactly 10 entries exist in the database.
2. Go to the Data Entry page.
3. Check whether pagination controls are visible.
**Test Data:** 10 entries in database
**Expected Result:** Pagination controls are not shown. All 10 entries appear in a single table without page numbers.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PGN-05: Boundary — exactly 11 entries shows pagination
**Summary:** With 11 entries, pagination should appear and page 2 should show 1 row.
**Test Steps:**
1. Ensure exactly 11 entries exist.
2. Go to the Data Entry page.
3. Confirm pagination controls appear.
4. Navigate to page 2.
**Test Data:** 11 entries in database
**Expected Result:** Pagination is visible. Page 1 shows 10 rows; page 2 shows 1 row.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PGN-06: Use « first and » last page buttons
**Summary:** The first-page and last-page navigation buttons should jump directly to those pages.
**Test Steps:**
1. Navigate to a middle page (e.g., page 3 of 5).
2. Click the **«** (first page) button.
3. Verify you are on page 1.
4. Click the **»** (last page) button.
5. Verify you are on the last page.
**Expected Result:** « jumps to page 1; » jumps to the last page.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PGN-07: Entry count label matches actual total
**Summary:** Any label showing the total entry count should match the real number in the database.
**Test Steps:**
1. Ensure 48 entries exist.
2. Look for a count label on the Data Entry page (e.g., "48 entries" or "Page 1 of 5").
**Expected Result:** The label shows 48. It matches the actual number of rows in the database.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
