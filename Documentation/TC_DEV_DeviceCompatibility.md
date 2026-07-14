# Test Cases — Device Compatibility

**Area:** Cross-Cutting — Device Compatibility Testing  
**Prefix:** DEV  
**Document Version:** 1.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

**Pre-condition:** The application is running (backend port 8000, frontend port 5173). A trained model and forecast data exist. Devices are connected to the same local network as the host machine, or browser DevTools device emulation is used.  
**Dependencies:** Target devices or emulators available; application accessible via local IP (e.g., `http://192.168.x.x:5173`).  
**Test Priority:** Medium

---

## Testing Approach

Device testing is performed using two methods:

1. **Browser DevTools Device Emulation** — Chrome/Edge DevTools responsive mode with device presets (touch simulation, viewport, DPR)
2. **Real Devices** (when available) — physical phones/tablets connected to the same network

### Target Device Matrix

| Category | Device / Viewport | Resolution | DPR | OS |
|----------|-------------------|------------|-----|-----|
| Phone (Small) | iPhone SE / Galaxy A | 375×667 | 2x | iOS / Android |
| Phone (Standard) | iPhone 14 / Pixel 7 | 390×844 | 3x | iOS / Android |
| Phone (Large) | iPhone 14 Pro Max / Galaxy S24 Ultra | 430×932 | 3x | iOS / Android |
| Tablet (Portrait) | iPad 10th Gen / Galaxy Tab S9 | 820×1180 | 2x | iPadOS / Android |
| Tablet (Landscape) | iPad 10th Gen / Galaxy Tab S9 | 1180×820 | 2x | iPadOS / Android |

---

### DEV-01: Phone — Layout & Navigation
**Summary:** Core layout, sidebar navigation, and hamburger menu function correctly on phone viewports.  
**Test Steps:**
1. Open the application in a phone viewport (390×844).
2. Verify the sidebar is hidden by default and a hamburger menu icon is visible in the TopBar.
3. Tap the hamburger icon — sidebar overlay slides in.
4. Verify all navigation links are visible and tappable (Dashboard, Forecast, Ask WATT-IF, Price Calculator, Data Entry).
5. Tap a navigation link — page navigates and sidebar closes.
6. Open sidebar again and tap outside the overlay — sidebar closes.
7. Verify the TopBar shows the page title, dark mode toggle, and user account button without overflow or truncation.
8. Switch to landscape orientation (844×390) — verify layout adapts without horizontal scrolling.

**Test Data:** Viewport: 390×844 (portrait), 844×390 (landscape); Touch simulation enabled  
**Expected Result:** Hamburger menu works; sidebar opens/closes smoothly; all nav links accessible; no horizontal overflow in either orientation. Touch targets are at least 44×44px.  
**Actual Result:** _(to be filled during testing)_  
**Status:** ⬜ Not Run  
**Notes:**

---

### DEV-02: Phone — Data Entry & Forms
**Summary:** All form inputs on the Data Entry page are usable on phone screens.  
**Test Steps:**
1. Navigate to Data Entry on a phone viewport (390×844).
2. Verify form fields (Month, Year, kWh, optional overrides) are stacked vertically and fill the viewport width.
3. Tap the kWh input — verify the on-screen numeric keyboard opens (type=number).
4. Enter a valid kWh value — verify the live bill preview appears without overlapping the input.
5. Tap "Submit" — verify the button is fully visible without scrolling past it.
6. Open the optional overrides `<details>` section — verify it expands without layout breakage.
7. Scroll to Entry History table — verify horizontal scrolling is available if columns exceed viewport width (or table adapts responsively).
8. Tap "Edit" on a row — verify inline edit inputs are usable with touch.
9. Test CSV upload — tap "Choose CSV", verify file picker opens.

**Test Data:** Viewport: 390×844; Touch simulation enabled  
**Expected Result:** Forms are usable without pinch-zoom. Numeric keyboard appears for number fields. All buttons and interactive elements are reachable. Table scrolls horizontally if needed.  
**Actual Result:** _(to be filled during testing)_  
**Status:** ⬜ Not Run  
**Notes:**

---

### DEV-03: Phone — Forecast Charts
**Summary:** Forecast charts render correctly and remain interactive on phone screens.  
**Test Steps:**
1. Navigate to Forecast page on a phone viewport (390×844).
2. Verify the horizon selector buttons (1 Mo, 3 Mo, etc.) wrap or scroll horizontally without overflow.
3. Select a forecast horizon — verify charts load.
4. Verify kWh bar chart is visible and occupies full width; bars are distinguishable.
5. Touch and hold a bar — verify tooltip displays forecast + CI range without being clipped.
6. Scroll down to bill chart — verify it renders with the CI shaded area visible.
7. Verify axis labels are readable (not overlapping or truncated).
8. Switch to landscape — verify charts resize and remain readable.

**Test Data:** Viewport: 390×844 (portrait), 844×390 (landscape); Touch simulation enabled  
**Expected Result:** Charts render at full viewport width, tooltips display on touch, axis labels readable, no overflow. Charts resize smoothly on orientation change.  
**Actual Result:** _(to be filled during testing)_  
**Status:** ⬜ Not Run  
**Notes:**

---

### DEV-04: Phone — Chat Assistant
**Summary:** Chat interface is usable on phone screens with proper keyboard handling.  
**Test Steps:**
1. Navigate to Ask WATT-IF on a phone viewport (390×844).
2. Verify the message thread occupies most of the viewport height.
3. Tap the question input — verify the virtual keyboard appears and the input remains visible (not hidden behind keyboard).
4. Type a question (near 500 chars) — verify character counter is visible.
5. Tap "Ask" — verify the message appears in the thread and auto-scrolls to show the response.
6. Verify assistant response bubbles wrap text properly (no horizontal overflow).
7. Verify the "Generating answer…" indicator is visible while streaming.
8. Test "Clear chat" button — verify it's accessible (not obscured by other elements).

**Test Data:** Viewport: 390×844; Touch simulation enabled  
**Expected Result:** Chat is fully functional on phone. Input stays visible above keyboard. Messages wrap correctly. Auto-scroll works.  
**Actual Result:** _(to be filled during testing)_  
**Status:** ⬜ Not Run  
**Notes:**

---

### DEV-05: Phone — Price Calculator
**Summary:** Price Calculator layout and interactions work on phone viewports.  
**Test Steps:**
1. Navigate to Price Calculator on a phone viewport (390×844).
2. Verify the account type dropdown, kWh input, and bracket selector are stacked vertically.
3. Enter a kWh value — verify the Estimated Bill card appears without overlapping inputs.
4. Scroll down — verify the bill breakdown table is readable (either stacked layout or horizontal scroll).
5. Verify the "Refresh Rate" button is tappable and not cut off.
6. Switch customer type — verify the UI updates without layout shift.

**Test Data:** Viewport: 390×844; Touch simulation enabled  
**Expected Result:** All calculator elements accessible. Breakdown table readable via scrolling or responsive layout. No elements cut off.  
**Actual Result:** _(to be filled during testing)_  
**Status:** ⬜ Not Run  
**Notes:**

---

### DEV-06: Tablet — Dashboard Layout
**Summary:** Dashboard utilizes tablet screen real estate effectively.  
**Test Steps:**
1. Open the application in a tablet viewport (820×1180, portrait).
2. Verify the sidebar is either visible as a permanent panel or accessible via hamburger (depends on breakpoint).
3. Verify stat cards display in a 2×2 grid (not single column like phone).
4. Verify the forecast chart renders at appropriate width with readable axis labels.
5. Switch to landscape (1180×820) — verify the sidebar becomes persistent (if applicable) and content area adjusts.
6. Verify the anomaly card (if present) doesn't overlap stat cards.
7. Check spacing and padding — elements should not feel cramped or excessively spaced.

**Test Data:** Viewport: 820×1180 (portrait), 1180×820 (landscape); Touch simulation enabled  
**Expected Result:** Layout adapts to tablet dimensions. Stat cards in grid. Charts sized appropriately. Sidebar behavior matches breakpoint design.  
**Actual Result:** _(to be filled during testing)_  
**Status:** ⬜ Not Run  
**Notes:**

---

### DEV-07: Tablet — Data Entry & History Table
**Summary:** Data entry forms and the entry history table are usable on tablet screens.  
**Test Steps:**
1. Navigate to Data Entry on a tablet viewport (820×1180).
2. Verify form fields may display side-by-side or in a wider single column (appropriate use of space).
3. Verify the Entry History table displays more columns without horizontal scrolling compared to phone.
4. Test inline edit — verify inputs are appropriately sized for touch.
5. Test delete confirmation dialog — verify it centers on the viewport with readable text.
6. Verify pagination controls are easily tappable.
7. Switch to landscape — verify table shows additional columns if available.

**Test Data:** Viewport: 820×1180 (portrait), 1180×820 (landscape); Touch simulation enabled  
**Expected Result:** Table shows more data without horizontal scroll on tablet. Forms utilize space efficiently. All touch targets meet 44px minimum.  
**Actual Result:** _(to be filled during testing)_  
**Status:** ⬜ Not Run  
**Notes:**

---

### DEV-08: Tablet — Forecast & Charts
**Summary:** Forecast charts render with higher detail on tablet screens.  
**Test Steps:**
1. Navigate to Forecast page on a tablet viewport (820×1180).
2. Verify horizon selector buttons are displayed in a single row without wrapping.
3. Verify charts are larger than phone rendering with more readable labels.
4. Touch a data point — verify tooltip is positioned correctly (not clipped by viewport edges).
5. Verify both kWh chart and bill chart are visible with minimal scrolling.
6. Switch to landscape — verify charts expand to use available width.

**Test Data:** Viewport: 820×1180 (portrait), 1180×820 (landscape); Touch simulation enabled  
**Expected Result:** Charts render at larger size with clear labels. Tooltips position correctly. Horizon buttons fit in one row.  
**Actual Result:** _(to be filled during testing)_  
**Status:** ⬜ Not Run  
**Notes:**

---

### DEV-09: Touch Interactions & Gestures
**Summary:** Touch-specific interactions work correctly across all device sizes.  
**Test Steps:**
1. On a phone viewport (390×844) with touch simulation:
   - Tap buttons — verify single tap activates (no double-tap-to-zoom issue).
   - Long-press chart data points — verify tooltip displays.
   - Swipe/scroll through Entry History table horizontally.
   - Pull down on pages — verify no unintended browser refresh interferes.
2. Verify no `:hover`-dependent functionality is broken (hover states should not block touch access).
3. Verify all interactive elements have a minimum touch target of 44×44 CSS pixels.
4. Verify dropdown menus (`<select>`) open the native OS picker on mobile.
5. Test pinch-to-zoom — verify it works on charts but form layout doesn't require it.

**Test Data:** Phone viewport: 390×844; Tablet viewport: 820×1180; Touch simulation enabled  
**Expected Result:** All touch interactions responsive. No double-tap issues. Touch targets meet 44px minimum. Native pickers for dropdowns on mobile.  
**Actual Result:** _(to be filled during testing)_  
**Status:** ⬜ Not Run  
**Notes:**

---

### DEV-10: Orientation Change & Viewport Resize
**Summary:** Application handles orientation changes gracefully without data loss or layout corruption.  
**Test Steps:**
1. On a phone viewport, navigate to Data Entry and partially fill in the kWh field.
2. Switch from portrait to landscape — verify the input value is preserved and form remains usable.
3. Navigate to Forecast page with a chart displayed.
4. Switch orientation — verify the chart resizes without requiring a page reload.
5. On a tablet viewport, navigate to the Dashboard.
6. Switch from portrait to landscape — verify stat cards and chart reflow correctly.
7. Navigate to Chat with messages visible — switch orientation — verify message thread remains scrolled to the same position.

**Test Data:** Phone: 390×844 ↔ 844×390; Tablet: 820×1180 ↔ 1180×820  
**Expected Result:** No data loss on orientation change. Charts resize dynamically. Layout adapts without horizontal scroll. Scroll position preserved where applicable.  
**Actual Result:** _(to be filled during testing)_  
**Status:** ⬜ Not Run  
**Notes:**

---

### DEV-11: PWA Behavior on Mobile Devices
**Summary:** PWA install and offline behavior on mobile devices.  
**Test Steps:**
1. Access the application via HTTPS (or local network) on a real Android device using Chrome.
2. Verify the "Add to Home Screen" / PWA install prompt appears (requires HTTPS in production).
3. Install the PWA — verify the app opens in standalone mode (no browser chrome).
4. Verify the app icon appears on the home screen.
5. Open the installed PWA — verify navigation works within the standalone window.
6. Test on iOS Safari — verify "Add to Home Screen" adds a bookmark (full PWA requires HTTPS).
7. Go offline while the PWA is open — verify an appropriate offline indicator or cached content appears.

**Test Data:** Real devices: Android phone (Chrome), iOS phone (Safari); Network: Same LAN as host  
**Expected Result:** PWA installs on Android Chrome (with HTTPS). Standalone mode works. iOS adds as bookmark. Offline state handled gracefully.  
**Actual Result:** _(to be filled during testing)_  
**Status:** ⬜ Not Run  
**Notes:** Full PWA install requires HTTPS. For local development, only Android Chrome supports HTTP PWA install via `localhost`. iOS requires HTTPS for Service Worker.

---

### DEV-12: Performance on Mobile Devices
**Summary:** Application performance is acceptable on mobile devices with limited resources.  
**Test Steps:**
1. On a phone viewport, open Chrome DevTools Performance tab with CPU throttling (4x slowdown) and network throttling (Fast 3G).
2. Navigate to the Dashboard — measure Time to Interactive (TTI).
3. Navigate to Forecast page and select 12-month horizon — measure chart render time.
4. Navigate to Data Entry and load Entry History with pagination — verify smooth scrolling.
5. Open Chat and submit a question — verify the streaming response doesn't cause UI jank.
6. Check memory usage — verify no memory leaks after navigating between all pages multiple times.

**Test Data:** CPU throttle: 4x; Network: Fast 3G (1.6 Mbps down, 750ms latency); Viewport: 390×844  
**Expected Result:** TTI < 5 seconds on throttled connection. Charts render within 3 seconds. Scrolling remains smooth (60fps). No memory leaks detected.  
**Actual Result:** _(to be filled during testing)_  
**Status:** ⬜ Not Run  
**Notes:** Performance thresholds are guidelines. Actual acceptable values depend on project requirements.

---

## Summary

| Test Case | Focus Area | Priority |
|-----------|-----------|----------|
| DEV-01 | Phone — Layout & Navigation | High |
| DEV-02 | Phone — Data Entry & Forms | High |
| DEV-03 | Phone — Forecast Charts | Medium |
| DEV-04 | Phone — Chat Assistant | Medium |
| DEV-05 | Phone — Price Calculator | Medium |
| DEV-06 | Tablet — Dashboard Layout | Medium |
| DEV-07 | Tablet — Data Entry & History Table | Medium |
| DEV-08 | Tablet — Forecast & Charts | Low |
| DEV-09 | Touch Interactions & Gestures | High |
| DEV-10 | Orientation Change & Viewport Resize | Medium |
| DEV-11 | PWA Behavior on Mobile Devices | Low |
| DEV-12 | Performance on Mobile Devices | Medium |
