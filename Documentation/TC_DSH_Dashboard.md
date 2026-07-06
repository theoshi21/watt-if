# Test Cases — Dashboard

**Module:** Dashboard
**Prefix:** DSH
**Document Version:** 1.0
**Date:** July 2026
**Prepared by:** QA Team

---

**Pre-condition:** A model is trained and a forecast has been generated (run FCT-01 first).
**Dependencies:** Backend `/forecast` endpoint; data in the database.
**Test Priority:** Medium

---

### DSH-01: Dashboard shows 4 stat cards with correct labels
**Summary:** The dashboard should display four stat cards: This Month, Daily Average, Avg Temp, and Avg Humidity.
**Test Steps:**
1. Ensure a forecast has been generated.
2. Click **Dashboard** in the sidebar.
3. Observe the stat cards at the top of the page.
**Expected Result:** Four stat cards are visible, each with a label and numeric value.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### DSH-02: "This Month" card shows the first forecast month's kWh
**Summary:** The This Month card should display the kWh value from the first forecast month.
**Test Steps:**
1. Generate a 3-month forecast. Note the first month's kWh value (e.g., 342 kWh).
2. Go to the Dashboard.
3. Check the "This Month" stat card.
**Expected Result:** The card shows the same kWh as the first forecast month.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### DSH-03: "Daily Average" = first forecast month kWh ÷ 30
**Summary:** The Daily Average card should show kWh divided by 30.
**Test Steps:**
1. Note the "This Month" kWh from DSH-02 (e.g., 342).
2. Calculate expected daily average: 342 ÷ 30 = 11.4 kWh/day.
3. Check the "Daily Average" stat card.
**Expected Result:** The card shows approximately 11.4 kWh/day (within reasonable rounding).
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### DSH-04: Avg Temp and Avg Humidity show plausible forecast values
**Summary:** Temperature and humidity cards should show values from the first forecast month's exogenous data.
**Test Steps:**
1. Ensure a forecast has been generated.
2. Check the "Avg Temp" and "Avg Humidity" stat cards.
**Expected Result:** Avg Temp is between 25°C and 38°C; Avg Humidity is between 50% and 95%. Both values are plausible for the Philippines.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### DSH-05: Dashboard with no forecast — empty state message shown
**Summary:** If no forecast is available, the Dashboard should show a helpful empty state.
**Test Steps:**
1. Clear all data (CAD-02) to remove the model.
2. Go to the Dashboard.
**Expected Result:** An empty-state message appears directing the user to upload data and train a model. No blank screen or crash.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### DSH-06: Anomaly card appears when first forecast month exceeds 110% of the mean
**Summary:** An anomaly alert banner should appear when the first forecast month's kWh is unusually high.
**Test Steps:**
1. Ensure the forecast data has a first month kWh value greater than 110% of the average across all forecast months. (If needed, add manual entries with high kWh to push the forecast above threshold.)
2. Generate a forecast.
3. Go to the Dashboard.
**Expected Result:** An anomaly card or banner is visible, alerting that consumption is higher than usual.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### DSH-07: Anomaly card is absent when no anomaly is detected
**Summary:** The anomaly card should not appear when the forecast is within normal range.
**Test Steps:**
1. Ensure the forecast data is within normal historical ranges (first month kWh ≤ 110% of mean).
2. Go to the Dashboard.
**Expected Result:** No anomaly card is shown. The Dashboard displays the normal stat cards and chart only.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### DSH-08: Forecast chart renders on the Dashboard
**Summary:** A forecast chart should be visible on the Dashboard page.
**Test Steps:**
1. Ensure a forecast has been generated.
2. Go to the Dashboard.
3. Scroll down if needed to find the chart.
**Expected Result:** A chart is rendered showing forecast data. It is not blank or missing.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### DSH-09: Loading skeleton shown while forecast data is loading
**Summary:** While the Dashboard fetches data, placeholder loading elements should appear.
**Test Steps:**
1. Throttle the network in browser dev tools (DevTools → Network → set to Slow 3G).
2. Navigate to the Dashboard.
3. Observe the page while it loads.
**Expected Result:** Skeleton placeholder blocks appear where the stat cards and chart will be. They are replaced by real content once loading completes.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
