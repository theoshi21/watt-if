# Test Cases — Performance

**Area:** Cross-Cutting — Performance Testing  
**Prefix:** PERF  
**Document Version:** 1.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

**Pre-condition:** The backend is running on port 8000. The database is populated with test data. The system is in a stable state.  
**Dependencies:** Backend and frontend must be running. Tools for load testing (e.g., browser multiple tabs, `ab`, or `locust`).  
**Test Priority:** Medium

---

### PERF-01: Upload very large CSV file (10,000+ rows)
**Summary:** Uploading a large CSV should complete within acceptable time without crashing.
**Test Steps:**
1. Generate a CSV with 10,000 rows of valid data (year_month from 2000-01 to 2833-04, kWh 100–500).
2. Upload the file via the Data Entry page.
3. Measure the time from upload click to success/error response.
**Test Data:** `large_test.csv` with 10,000 rows, file size ~500 KB
**Expected Result:** Upload completes within 30 seconds. Either succeeds (with deduplication to unique months) or returns a clear size/limit error. No server crash or timeout. Memory usage doesn't spike beyond 500 MB.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PERF-02: Forecast generation under heavy load
**Summary:** Generating forecasts while the system is under load should still complete.
**Test Steps:**
1. Ensure a trained model exists.
2. Open 5 browser tabs simultaneously.
3. In each tab, trigger a 12-month forecast at the same time.
4. Measure response times.
**Test Data:** 5 concurrent 12-month forecast requests
**Expected Result:** All 5 requests complete within 60 seconds. No request fails with a 500 error. Responses are correct.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PERF-03: 100 simultaneous API requests
**Summary:** The API should handle 100 concurrent read requests without failing.
**Test Steps:**
1. Use a load testing tool (e.g., `ab -n 100 -c 100`) to send 100 simultaneous GET requests to `/health`.
2. Measure response times and error rate.
**Test Data:** 100 concurrent GET requests to `/health`
**Expected Result:** All 100 requests return HTTP 200. Average response time < 2 seconds. No 500 errors. Zero connection failures.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PERF-04: Multiple concurrent model training requests
**Summary:** Simultaneous training requests from the same user should be blocked (no concurrent training).
**Test Steps:**
1. Ensure ≥14 entries for a user.
2. Send a POST to `/retrain` (or click Train Model).
3. Immediately send a second POST to `/retrain` (or click Train Model again).
**Test Data:** Two concurrent `/retrain` requests for the same user
**Expected Result:** The first request starts training (status: "running"). The second request returns HTTP 409 "Training already in progress." No crash, no duplicate training, no model corruption.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PERF-05: Large database performance (1,000+ entries)
**Summary:** The application should remain responsive with a large entry history.
**Test Steps:**
1. Insert 1,000 entries into the database (programmatically or via repeated CSV uploads).
2. Navigate to the Data Entry page.
3. Measure page load time.
4. Navigate through pagination (page 1, 50, 100).
5. Edit an entry on page 50.
**Test Data:** 1,000 entries in `data_entry_log`
**Expected Result:** Page loads within 3 seconds. Pagination navigates within 1 second per page. Edit/save operations complete within 2 seconds.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PERF-06: API response time benchmarks
**Summary:** Key API endpoints should respond within acceptable time limits.
**Test Steps:**
1. Measure response time for each endpoint (average of 10 requests):
   - `GET /health`
   - `GET /data-entries`
   - `POST /forecast` (3-month horizon)
   - `GET /meralco-rate`
   - `GET /settings`
**Test Data:** 10 sequential requests to each endpoint, timed
**Expected Result:**
- `/health`: < 500 ms
- `/data-entries`: < 1 second (with 48 entries)
- `/forecast`: < 10 seconds (3-month)
- `/meralco-rate`: < 2 seconds (from cache)
- `/settings`: < 500 ms
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
