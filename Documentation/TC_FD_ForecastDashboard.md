# Test Cases — Forecasting & Dashboard

**Module:** Module 3 — Forecasting & Dashboard  
**Prefix:** FD  
**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

**Pre-condition:** A model has been trained (DM-36 completed). Data from `synthetic_2022_2025.csv` is in the database (latest month: December 2025).  
**Dependencies:** Backend `/forecast` endpoint must be reachable.  
**Test Priority:** High

---

## Forecasting (FD-01 to FD-11)

### FD-01: Default 3-month forecast loads
**Summary:** Forecast page displays a 3-month forecast by default.
**Test Steps:**
1. Click **Forecast** in sidebar.
**Expected Result:** 3-month forecast loads. Bar chart has 3 bars, line chart has 3 points. Months start from Jan 2026.
**Status:** ⬜ Not Run

---

### FD-02: Select 1-month horizon
**Summary:** Chart updates to 1 bar.
**Test Steps:**
1. Click **1m** in horizon selector.
**Expected Result:** 1 bar in kWh chart, 1 point in bill chart.
**Status:** ⬜ Not Run

---

### FD-03: Select 6-month horizon
**Summary:** Chart updates to 6 bars.
**Test Steps:**
1. Click **6m**.
**Expected Result:** 6 bars, 6 bill points.
**Status:** ⬜ Not Run

---

### FD-04: Select 9-month horizon
**Summary:** Chart updates to 9 bars.
**Test Steps:**
1. Click **9m**.
**Expected Result:** 9 bars, 9 bill points.
**Status:** ⬜ Not Run

---

### FD-05: Select 12-month horizon
**Summary:** Chart updates to 12 bars.
**Test Steps:**
1. Click **12m**.
**Expected Result:** 12 bars, 12 bill points.
**Status:** ⬜ Not Run

---

### FD-06: Forecast anchored from latest data
**Summary:** First forecast month is month after latest entry.
**Test Steps:**
1. Confirm latest entry is `2025-12`. Check x-axis labels.
**Expected Result:** First bar is "Jan 2026."
**Status:** ⬜ Not Run

---

### FD-07: kWh chart has error bars (CI)
**Summary:** Each bar shows 95% confidence interval error bars.
**Test Steps:**
1. Inspect kWh bar chart.
**Expected Result:** Visible error bars above/below each bar.
**Status:** ⬜ Not Run

---

### FD-08: Bill chart has shaded CI band
**Summary:** Shaded area represents confidence interval.
**Test Steps:**
1. Inspect bill line chart.
**Expected Result:** Shaded band around the line.
**Status:** ⬜ Not Run

---

### FD-09: Tooltip on hover shows values
**Summary:** Hovering shows kWh and CI values.
**Test Steps:**
1. Hover over any bar.
**Expected Result:** Tooltip shows forecast kWh and lower/upper CI.
**Status:** ⬜ Not Run

---

### FD-10: No trained model — error message
**Summary:** Without a model, clear error shown.
**Test Steps:**
1. Clear all data. Go to Forecast page.
**Expected Result:** Message: "No trained model found." No blank area.
**Status:** ⬜ Not Run

---

### FD-11: Empty database — guidance message
**Summary:** With no data or model, user guided to add data.
**Test Steps:**
1. Clear all data. Go to Forecast page.
**Expected Result:** Message guides user to Data Entry.
**Status:** ⬜ Not Run

---

## Dashboard (FD-12 to FD-20)

### FD-12: Four stat cards displayed
**Summary:** Dashboard shows This Month, Daily Average, Avg Temp, Avg Humidity cards.
**Test Steps:**
1. Ensure forecast exists. Click **Dashboard**.
**Expected Result:** Four labeled stat cards visible with numeric values.
**Status:** ⬜ Not Run

---

### FD-13: "This Month" shows first forecast kWh
**Summary:** Card matches first forecast month's value.
**Test Steps:**
1. Note first forecast kWh. Check Dashboard card.
**Expected Result:** Card shows same kWh value.
**Status:** ⬜ Not Run

---

### FD-14: "Daily Average" = first month kWh ÷ 30
**Summary:** Calculated correctly from first month.
**Test Steps:**
1. Check "Daily Average" card.
**Expected Result:** Value ≈ This Month kWh / 30.
**Status:** ⬜ Not Run

---

### FD-15: Temp and Humidity show plausible values
**Summary:** Philippine climate range values shown.
**Test Steps:**
1. Check Avg Temp (25–38°C) and Avg Humidity (50–95%).
**Expected Result:** Both within plausible ranges.
**Status:** ⬜ Not Run

---

### FD-16: No forecast — empty state message
**Summary:** Helpful message when no forecast available.
**Test Steps:**
1. Clear all data. Go to Dashboard.
**Expected Result:** Empty state directing user to upload data.
**Status:** ⬜ Not Run

---

### FD-17: Anomaly card appears (>110% of mean)
**Summary:** Alert when first month exceeds 110% average.
**Test Steps:**
1. Generate forecast where first month kWh > 110% of mean.
**Expected Result:** Anomaly card/banner visible.
**Status:** ⬜ Not Run

---

### FD-18: Anomaly card absent (normal range)
**Summary:** No alert when forecast within normal range.
**Test Steps:**
1. Generate normal forecast (≤110% of mean).
**Expected Result:** No anomaly card shown.
**Status:** ⬜ Not Run

---

### FD-19: Forecast chart renders on Dashboard
**Summary:** Chart visible on Dashboard page.
**Test Steps:**
1. Ensure forecast exists. Check Dashboard.
**Expected Result:** Chart rendered with data.
**Status:** ⬜ Not Run

---

### FD-20: Loading skeleton while data fetches
**Summary:** Skeleton placeholders during load.
**Test Steps:**
1. Throttle network (Slow 3G). Navigate to Dashboard.
**Expected Result:** Skeleton blocks appear, replaced by content when loaded.
**Status:** ⬜ Not Run
