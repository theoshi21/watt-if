# Test Cases — Delete Entry

**Module:** Data Entry — Entry History (Delete)
**Prefix:** DLE
**Document Version:** 1.0
**Date:** July 2026
**Prepared by:** QA Team

---

**Pre-condition:** At least one entry exists in Entry History.
**Dependencies:** Backend `/data-entries/{id}` DELETE endpoint must be reachable.
**Test Priority:** High

---

### DLE-01: Click Delete — confirmation dialog appears
**Summary:** Clicking the Delete button should show a confirmation prompt before anything is deleted.
**Test Steps:**
1. Go to the Data Entry page.
2. Locate any row in Entry History.
3. Click the **Delete** button for that row.
**Expected Result:** A confirmation dialog appears asking the user to confirm the deletion.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### DLE-02: Confirm delete — entry is removed from table
**Summary:** Confirming the deletion should remove the row from Entry History immediately.
**Test Steps:**
1. Click **Delete** on any row.
2. In the confirmation dialog, click **Yes, delete**.
**Expected Result:** The row disappears from Entry History. The total entry count decreases by 1.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### DLE-03: Cancel delete — entry remains in table
**Summary:** Cancelling the delete dialog should leave the entry unchanged.
**Test Steps:**
1. Click **Delete** on any row.
2. In the confirmation dialog, click **Cancel**.
**Expected Result:** The dialog closes. The row is still present in Entry History. Nothing is deleted.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### DLE-04: Delete the last remaining entry
**Summary:** Deleting the only entry in the database should leave Entry History empty.
**Test Steps:**
1. Ensure only one entry exists (delete all others, or start with a single entry).
2. Click **Delete** on that entry and confirm.
**Expected Result:** Entry History is empty. An empty state message is shown (e.g., "No entries recorded yet."). No error occurs.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### DLE-05: Deleted entry does not reappear after page navigation
**Summary:** A deleted entry should remain gone after navigating away and returning.
**Test Steps:**
1. Delete an entry and confirm (DLE-02).
2. Navigate to a different page (e.g., Dashboard).
3. Navigate back to the Data Entry page.
4. Check Entry History.
**Expected Result:** The deleted entry is not present. The entry count matches the count after deletion.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
