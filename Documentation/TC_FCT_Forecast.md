# Test Cases — Forecast

**Module:** Forecast Page
**Prefix:** FCT
**Document Version:** 1.0
**Date:** July 2026
**Prepared by:** QA Team

---

**Pre-condition:** A model has been trained (TRM-01). Data from `synthetic_2022_2025.csv` is in the database (latest month: December 2025).
**Dependencies:** Backend `/forecast` endpoint must be reachable.
**Test Priority:** High

---

### FCT-01: Default 3-month forecast loads on page visit
**Summary:** Navigating to the Forecast page should automatically display a 3-month forecast.
**Test Steps:**
1. Ensure the model is trained.
2. Click **Forecast** in the sidebar.
**Expected Result:** A 3-month forecast loads. The kWh bar chart has 3 bars and the bill line chart has 3 data points. Forecast months start from January 2026 (the month after the latest data).
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### FCT-02: Select 1-month horizon — chart updates to 1 bar
**Summary:** Clicking the "1m" option should update the chart to show a single forecast month.
**Test Steps:**
1. Go to the Forecast page.
2. Click **1m** in the horizon selector.
**Expected Result:** The kWh bar chart updates to show exactly 1 bar. The bill chart shows 1 data point.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### FCT-03: Select 6-month horizon — chart updates to 6 bars
**Summary:** Clicking "6m" should show 6 forecast months.
**Test Steps:**
1. Go to the Forecast page.
2. Click **6m** in the horizon selector.
**Expected Result:** The kWh bar chart has 6 bars. The bill chart has 6 data points.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### FCT-04: Select 9-month horizon — chart updates to 9 bars
**Summary:** Clicking "9m" should show 9 forecast months.
**Test Steps:**
1. Go to the Forecast page.
2. Click **9m** in the horizon selector.
**Expected Result:** The kWh bar chart has 9 bars. The bill chart has 9 data points.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### FCT-05: Select 12-month horizon — chart updates to 12 bars
**Summary:** Clicking "12m" should show 12 forecast months.
**Test Steps:**
1. Go to the Forecast page.
2. Click **12m** in the horizon selector.
**Expected Result:** The kWh bar chart has 12 bars. The bill chart has 12 data points.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### FCT-06: Forecast months start from the month after the latest data
**Summary:** The first forecast month should immediately follow the most recent entry in the database.
**Test Steps:**
1. Confirm the latest entry is `2025-12` (December 2025).
2. Go to the Forecast page and check the x-axis labels on the kWh chart.
**Test Data:** Latest data entry: `2025-12`
**Expected Result:** The first forecast bar is labelled `Jan 2026`. No bar falls within the historical data range.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### FCT-07: kWh bar chart has visible error bars (confidence intervals)
**Summary:** Each bar should show upper and lower error bars representing the 95% confidence interval.
**Test Steps:**
1. Go to the Forecast page with any horizon selected.
2. Inspect the kWh bar chart.
**Expected Result:** Each bar has visible error bars (lines extending above and below the top of the bar) showing the CI range.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### FCT-08: Bill line chart has a shaded confidence interval band
**Summary:** The bill chart should show a shaded area around the line representing the CI.
**Test Steps:**
1. Go to the Forecast page with any horizon selected.
2. Inspect the bill line chart.
**Expected Result:** A shaded band is visible around the forecast line. It represents the upper and lower 95% CI bounds.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### FCT-09: Hover over a bar — tooltip shows kWh and CI values
**Summary:** Hovering over a bar should show a tooltip with forecast values.
**Test Steps:**
1. Go to the Forecast page.
2. Hover the mouse over any bar in the kWh chart.
**Expected Result:** A tooltip appears showing the forecasted kWh value and the lower/upper CI values for that month.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### FCT-10: Forecast page with no trained model — error message shown
**Summary:** If no model has been trained, the Forecast page should display a clear error rather than a blank chart.
**Test Steps:**
1. Clear all data (CAD-02) to remove the model.
2. Go to the Forecast page.
**Expected Result:** A message is shown (e.g., "No trained model found. Please upload data and train the model first."). No blank white area or crash.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### FCT-11: Forecast page with a completely empty database
**Summary:** With no data and no model, the page should guide the user to add data.
**Test Steps:**
1. Clear all data (CAD-02).
2. Go to the Forecast page.
**Expected Result:** A message guides the user to go to Data Entry, add data, and train a model. No crash or blank screen.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
