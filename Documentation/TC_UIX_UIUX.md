# Test Cases — UI/UX

**Module:** UI/UX — Navigation, Theme, Mobile, Health
**Prefix:** UIX
**Document Version:** 1.0
**Date:** July 2026
**Prepared by:** QA Team

---

**Pre-condition:** The app is open in a browser. No specific data state is required unless noted.
**Dependencies:** None.
**Test Priority:** Low–Medium

---

### UIX-01: Toggle dark mode — theme switches to dark
**Summary:** Clicking the dark mode toggle should switch the entire app to a dark color scheme.
**Test Steps:**
1. Open the app in light mode (default).
2. Click the **dark/light mode toggle** in the top bar (sun/moon icon).
**Expected Result:** The background, text, cards, and sidebar all switch to a dark color palette.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### UIX-02: Toggle back to light mode — theme switches to light
**Summary:** Clicking the toggle a second time should return the app to light mode.
**Test Steps:**
1. Switch to dark mode (UIX-01).
2. Click the **dark/light mode toggle** again.
**Expected Result:** The app returns to a light color scheme. All elements use the light theme colors.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### UIX-03: Theme preference persists after page refresh
**Summary:** The chosen theme should be remembered after a page reload.
**Test Steps:**
1. Switch to dark mode (UIX-01).
2. Refresh the page (F5 or Ctrl+R).
**Expected Result:** The app reloads in dark mode. The preference was saved and applied automatically.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### UIX-04: Sidebar navigation — each link goes to the correct page
**Summary:** Clicking each item in the sidebar should load the corresponding page.
**Test Steps:**
1. Click **Dashboard** — confirm the Dashboard page loads.
2. Click **Forecast** — confirm the Forecast page loads.
3. Click **Ask WATT-IF** — confirm the Ask page loads.
4. Click **Price Calculator** — confirm the Price Calculator page loads.
5. Click **Data Entry** — confirm the Data Entry page loads.
**Expected Result:** Each link navigates to the correct page. The page title and content match.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### UIX-05: Active navigation item is highlighted for the current page
**Summary:** The sidebar should visually highlight the link for the current page.
**Test Steps:**
1. Navigate to each page one by one (Dashboard, Forecast, Ask WATT-IF, Price Calculator, Data Entry).
2. After navigating to each page, look at the corresponding sidebar link.
**Expected Result:** The link for the current page is visually distinct (e.g., different background color, bold text) from the other links.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### UIX-06: Mobile — sidebar hidden by default, opens via hamburger menu
**Summary:** On a narrow (mobile) screen, the sidebar should be hidden and opened by a menu button.
**Test Steps:**
1. Open the app and resize the browser to a mobile width (≤ 767px), or use DevTools to simulate a phone.
2. Observe whether the sidebar is hidden.
3. Click the **☰** hamburger button in the top bar.
**Expected Result:** The sidebar is not visible on mobile by default. Clicking the hamburger icon reveals the sidebar.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### UIX-07: Mobile — sidebar closes when overlay is tapped
**Summary:** Tapping the dark overlay behind the mobile sidebar should close it.
**Test Steps:**
1. Open the sidebar in mobile view (UIX-06).
2. Tap or click the semi-transparent overlay to the right of the sidebar.
**Expected Result:** The sidebar closes and the overlay disappears.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### UIX-08: Mobile — sidebar closes when Escape key is pressed
**Summary:** Pressing the Escape key should close the mobile sidebar.
**Test Steps:**
1. Open the sidebar in mobile view (UIX-06).
2. Press the **Escape** key.
**Expected Result:** The sidebar closes.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### UIX-09: Health indicator shows all green when all systems are running
**Summary:** The health indicator in the sidebar should show all subsystems as operational when the backend and Ollama are up.
**Test Steps:**
1. Ensure the FastAPI backend is running, Ollama is running, and data exists.
2. Look for the health indicator in the sidebar.
**Expected Result:** All subsystem status indicators are green (or equivalent "OK"). No warnings are shown.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### UIX-10: Health indicator shows degraded when Ollama is offline
**Summary:** Stopping Ollama should cause the health indicator to reflect a degraded state.
**Test Steps:**
1. Stop the Ollama service.
2. Wait up to 30 seconds for the health check to refresh.
3. Check the health indicator in the sidebar.
**Expected Result:** The Ollama subsystem shows as degraded (red or amber). The backend and data indicators remain green.
**Post-condition:** Restart Ollama after this test (`ollama serve`).
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### UIX-11: Offline banner appears when network is disconnected
**Summary:** Going offline should cause an offline notification banner to appear in the app.
**Test Steps:**
1. Open the app normally.
2. Use browser DevTools → Network → set to **Offline** (or disconnect Wi-Fi).
3. Observe the app.
**Expected Result:** An offline banner or indicator appears (e.g., "You are offline. Some features may not be available."). The app does not crash and still shows cached content where possible.
**Post-condition:** Reconnect to the network after this test.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
