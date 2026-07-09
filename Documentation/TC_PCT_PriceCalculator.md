# Test Cases — Price Calculator

**Module:** Module 5 — Price Calculator (Rate Scraping, Brackets, Bill Breakdown)  
**Prefix:** PCT  
**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

**Pre-condition:** The backend is running and the Meralco rate endpoint is reachable.
**Dependencies:** `/meralco-rate` endpoint; internet connection recommended for live rate scraping on first load.
**Test Priority:** Medium

---

### PCT-01: Page loads with live Meralco rate displayed
**Summary:** Opening the Price Calculator should fetch and display the current Meralco rate.
**Test Steps:**
1. Click **Price Calculator** in the sidebar.
2. Observe the rate display area.
**Expected Result:** A Meralco rate value (in ₱/kWh) is shown along with a last-updated timestamp. The value is between ₱9 and ₱15/kWh.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PCT-02: Enter valid kWh (250) — bill breakdown is shown
**Summary:** Entering a valid kWh amount should calculate and display a detailed bill breakdown.
**Test Steps:**
1. Go to the Price Calculator page.
2. In the kWh input, type `250`.
**Test Data:** kWh: `250`
**Expected Result:** A bill breakdown table appears showing individual charge components (generation, transmission, system loss, distribution, supply, metering, and other charges) plus a total bill amount.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PCT-03: Enter 0 kWh — breakdown shows zeros or is hidden
**Summary:** A kWh of zero should result in a zero-cost breakdown or the breakdown should hide.
**Test Steps:**
1. Go to the Price Calculator page.
2. Clear the kWh field and type `0`.
**Test Data:** kWh: `0`
**Expected Result:** Either the breakdown shows all zero values, or it is hidden. No error is thrown.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PCT-04: Enter negative kWh — not accepted or treated as zero
**Summary:** A negative kWh value should be rejected or defaulted to zero.
**Test Steps:**
1. Go to the Price Calculator page.
2. Try to type `-50` in the kWh field.
**Test Data:** kWh: `-50`
**Expected Result:** The field does not accept a negative sign, or the value is treated as 0/empty. No bill is calculated for negative input.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PCT-05: Boundary — enter 1 kWh (minimum meaningful input)
**Summary:** A kWh of 1 should produce a small but valid bill breakdown.
**Test Steps:**
1. Go to the Price Calculator page.
2. Type `1` in the kWh field.
**Test Data:** kWh: `1`
**Expected Result:** A breakdown is shown with very small but valid charge values. The total is greater than ₱0. No error.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PCT-06: Enter very large kWh (9,999) — breakdown scales correctly
**Summary:** A large kWh value should produce a proportionally scaled breakdown without errors.
**Test Steps:**
1. Go to the Price Calculator page.
2. Type `9999` in the kWh field.
**Test Data:** kWh: `9999`
**Expected Result:** A breakdown is shown with large values proportional to 9,999 kWh. No overflow, NaN values, or crash.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PCT-07: Auto bracket selection — correct bracket chosen for 350 kWh
**Summary:** The calculator should automatically select the 301–400 kWh bracket when 350 kWh is entered.
**Test Steps:**
1. Go to the Price Calculator page.
2. Type `350` in the kWh field.
3. Observe the bracket selector.
**Test Data:** kWh: `350`
**Expected Result:** The bracket `301–400 kWh` is automatically selected. The breakdown uses rates from that bracket.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PCT-08: Auto bracket boundary — 400 kWh selects the "301–400" bracket
**Summary:** At the upper boundary of the 301–400 bracket, that bracket should still be selected.
**Test Steps:**
1. Type `400` in the kWh field.
2. Observe the bracket selector.
**Test Data:** kWh: `400`
**Expected Result:** The `301–400 kWh` bracket (or equivalent) is selected. The breakdown uses those rates.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PCT-09: Auto bracket boundary — 401 kWh selects the "Over 400" bracket
**Summary:** One kWh above the 301–400 boundary should bump into the next bracket.
**Test Steps:**
1. Type `401` in the kWh field.
2. Observe the bracket selector.
**Test Data:** kWh: `401`
**Expected Result:** The `Over 400 kWh` bracket (or equivalent) is selected. The breakdown updates accordingly.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PCT-10: Manual bracket override — bill recalculates for selected bracket
**Summary:** Manually choosing a different bracket should recalculate the bill using that bracket's rates.
**Test Steps:**
1. Enter `350` kWh (auto-selects 301–400 bracket). Note the total bill.
2. Manually change the bracket to `201–300 kWh`.
3. Observe the total bill.
**Expected Result:** The total bill changes to reflect the 201–300 bracket's rates, even though kWh (350) hasn't changed.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PCT-11: Change customer type — brackets update accordingly
**Summary:** Switching between customer types should update the bracket options and rates.
**Test Steps:**
1. Go to the Price Calculator page. Observe the brackets for "Residential" (default).
2. Change the customer type to "General Service" (or vice versa).
3. Observe the bracket selector and breakdown.
**Expected Result:** Bracket options update for the new customer type. The bill breakdown recalculates using the new type's rates.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PCT-12: Refresh rate button — rate updates and bill recalculates
**Summary:** Clicking rate refresh should fetch a fresh Meralco rate and recalculate the bill.
**Test Steps:**
1. Note the current rate shown on the page.
2. Click the **↻ Refresh Rate** button.
3. Wait for the rate to reload.
**Expected Result:** The rate timestamp updates. The bill recalculates using the refreshed rate. No error is thrown.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### PCT-13: Calculator works when Meralco API is unavailable (fallback rates)
**Summary:** If the live rate cannot be fetched, a cached or fallback rate should be used so the calculator still works.
**Test Steps:**
1. Disconnect from the internet (or simulate offline mode in browser dev tools).
2. Go to the Price Calculator page.
3. Enter `300` in the kWh field.
**Test Data:** kWh: `300`; Meralco API: unavailable
**Expected Result:** The page still shows a rate (from cache or fallback) and produces a bill breakdown. A note may indicate the rate is not live. No blank page or crash.
**Post-condition:** Reconnect to the internet after this test.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
