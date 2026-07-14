# Test Cases — Browser Compatibility

**Area:** Cross-Cutting — Browser Compatibility Testing  
**Prefix:** BRWS  
**Document Version:** 1.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

**Pre-condition:** The application is running (backend port 8000, frontend port 5173). A trained model and forecast data exist.  
**Dependencies:** All target browsers installed at their latest stable versions.  
**Test Priority:** Medium

---

### BRWS-01: Google Chrome (latest stable)
**Summary:** Full application functionality verified in Chrome.
**Test Steps:**
1. Open the application in Google Chrome (latest stable version).
2. Execute the following checks:
   - Login and register flows work
   - Data Entry page: manual entry, CSV upload, entry history pagination
   - Forecast page: horizon selection, charts render with CI bands/error bars
   - Ask WATT-IF: send a question, response streams in
   - Price Calculator: enter kWh, breakdown displays
   - Settings: change preferences, verify persistence
   - Dark/light mode toggle works
   - Mobile responsive layout (resize to 360px width)
3. Check browser console for JavaScript errors.
**Test Data:** Browser: Chrome latest stable; Viewport: 1920×1080, then 360×800
**Expected Result:** All features work correctly. Charts render with proper interactivity (tooltips, hover). No JavaScript errors in console. Responsive layout adapts correctly.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### BRWS-02: Mozilla Firefox (latest stable)
**Summary:** Full application functionality verified in Firefox.
**Test Steps:**
1. Open the application in Mozilla Firefox (latest stable version).
2. Execute the same checks as BRWS-01:
   - Login/register, data entry, forecast charts, chat, price calculator, settings, dark mode, responsive
3. Check browser console for JavaScript errors.
4. Verify Service Worker registration for PWA.
**Test Data:** Browser: Firefox latest stable; Viewport: 1920×1080, then 360×800
**Expected Result:** All features work identically to Chrome. Charts render correctly (Recharts library supports Firefox). PWA install prompt may differ but Service Worker registers. No JS errors.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### BRWS-03: Microsoft Edge (latest stable)
**Summary:** Full application functionality verified in Edge.
**Test Steps:**
1. Open the application in Microsoft Edge (latest stable version).
2. Execute the same checks as BRWS-01:
   - Login/register, data entry, forecast charts, chat, price calculator, settings, dark mode, responsive
3. Check browser console for JavaScript errors.
4. Test PWA install (Edge supports PWA install from address bar).
**Test Data:** Browser: Edge latest stable; Viewport: 1920×1080, then 360×800
**Expected Result:** All features work identically to Chrome (Edge uses Chromium engine). PWA installable from address bar. No JS errors.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### BRWS-04: Apple Safari (latest stable)
**Summary:** Full application functionality verified in Safari.
**Test Steps:**
1. Open the application in Safari (latest stable version on macOS or iOS simulator).
2. Execute the same checks as BRWS-01:
   - Login/register, data entry, forecast charts, chat, price calculator, settings, dark mode, responsive
3. Check Safari's Web Inspector console for JavaScript errors.
4. Verify CSS custom properties (design tokens) render correctly.
5. Verify SSE streaming (chat) works in Safari.
**Test Data:** Browser: Safari latest stable; Viewport: 1920×1080, then 375×812 (iPhone)
**Expected Result:** All features work correctly. CSS custom properties supported. SSE streaming for chat works (Safari supports EventSource). Note: PWA install requires HTTPS on iOS Safari.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:** Safari on iOS requires HTTPS for full PWA functionality. Local HTTP testing is limited to "Add to Home Screen" as a bookmark.
