# Test Cases — AI Robustness

**Area:** Cross-Cutting — AI Robustness Testing  
**Prefix:** AIR  
**Document Version:** 1.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

**Pre-condition:** The backend is running. A user account exists with data uploaded and model trained.  
**Dependencies:** SARIMAX model must be trainable. Backend `/forecast` endpoint reachable.  
**Test Priority:** High

---

### AIR-01: Highly irregular historical data (random noise)
**Summary:** The model should handle extreme variance in historical data without crashing.
**Test Steps:**
1. Create a CSV with 24 months of data where kWh values are random between 50 and 5,000 with no seasonal pattern.
2. Upload and train the model.
3. Generate a 6-month forecast.
**Test Data:** CSV with 24 rows, kWh values: random uniform(50, 5000), price = kWh × 11.5
**Expected Result:** Model trains (possibly with wide CIs). Forecast generates without error. All forecasted values are positive. CI widths reflect uncertainty. No crash or unhandled exception.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### AIR-02: Missing months in historical data
**Summary:** Gaps in the time series should be handled gracefully.
**Test Steps:**
1. Create a CSV covering 2022-01 to 2025-12 but omit months: 2023-04, 2023-05, 2024-09.
2. Upload the CSV.
3. Train the model.
4. Generate a forecast.
**Test Data:** 45 rows (48 minus 3 skipped months)
**Expected Result:** Either the system imputes missing months during pipeline processing and trains successfully, or provides a clear error message about non-contiguous data. No crash.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### AIR-03: Extreme outliers (e.g., 50,000 kWh in one month)
**Summary:** A single extreme outlier should not corrupt the model or produce invalid forecasts.
**Test Steps:**
1. Upload `synthetic_2022_2025.csv` (normal data, 200–500 kWh range).
2. Add one manual entry: 2025-06 with 50,000 kWh.
3. Train the model.
4. Generate a 3-month forecast.
**Test Data:** Normal 48-month dataset + one entry at 50,000 kWh
**Expected Result:** Model trains. Forecast values are not extremely inflated by the single outlier (robust estimation). All values are positive. CIs may be wider. No negative forecasts.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### AIR-04: Negative forecast prevention
**Summary:** The SARIMAX model should never produce negative kWh or bill forecasts.
**Test Steps:**
1. Upload a dataset with very low kWh values (10–50 range) and a declining trend.
2. Train the model.
3. Generate a 12-month forecast.
4. Check all forecasted values including lower CI bounds.
**Test Data:** 24 months with declining kWh: month 1 = 50, month 24 = 10 (linear decline)
**Expected Result:** All forecasted kWh values are ≥ 0. All bill values are ≥ 0. Lower CI bounds may be 0 (floored) but not negative.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### AIR-05: Confidence interval anomalies (CI wider than forecast value)
**Summary:** When CIs are extremely wide, the system should still display correctly.
**Test Steps:**
1. Use a noisy dataset (high variance) to train the model.
2. Generate a 12-month forecast.
3. Check if any CI lower bound is negative or if CI width exceeds the forecast value.
**Test Data:** High-variance dataset (standard deviation > mean)
**Expected Result:** Charts render correctly even with wide CIs. Lower CI bounds are floored at 0 if negative. Error bars/bands are visually reasonable. No NaN or Infinity values in the UI.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### AIR-06: Model convergence failures
**Summary:** When the SARIMAX optimizer cannot converge, a clear error is reported.
**Test Steps:**
1. Create a minimal dataset (14 rows) with completely constant values (all kWh = 300, all price = 3000, all exogenous identical).
2. Upload and attempt to train.
3. Observe the training status and error message.
**Test Data:** 14 identical rows: kWh=300, price=3000, temp=30, humidity=70, rainfall=100, all same
**Expected Result:** Either the model trains successfully (flat forecast), or training fails with a clear error message like "Model could not converge" or "Insufficient variance in data." No crash. Status shows "Failed" with an explanation.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
