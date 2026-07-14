# Test Cases — Accessibility

**Area:** Cross-Cutting — Accessibility Testing  
**Prefix:** A11Y  
**Document Version:** 1.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

**Pre-condition:** The application is running (backend port 8000, frontend port 5173). A screen reader (NVDA on Windows or VoiceOver on macOS) is available for testing.  
**Dependencies:** Browser with accessibility tools (Chrome DevTools Accessibility panel, axe DevTools extension).  
**Test Priority:** Medium

---

### A11Y-01: Keyboard-only navigation
**Summary:** All interactive elements should be reachable and operable using only the keyboard.
**Test Steps:**
1. Open the application in a browser. Do NOT use the mouse.
2. Press Tab repeatedly to navigate through:
   - Login form fields and submit button
   - Sidebar navigation links
   - Data Entry form inputs and buttons
   - Forecast horizon selector buttons
   - Chat input field and send button
   - Price Calculator inputs
   - Settings dropdowns and toggles
3. Press Enter/Space to activate buttons and links.
4. Press Escape to close the mobile drawer (at mobile viewport).
5. Verify Tab does not get trapped (except intentional focus traps like the mobile drawer).
**Test Data:** Keyboard only: Tab, Shift+Tab, Enter, Space, Escape, Arrow keys
**Expected Result:** Every interactive element is reachable via Tab. Buttons activate with Enter/Space. Focus order is logical (top-to-bottom, left-to-right). Mobile drawer has a focus trap. Escape closes drawers/modals.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### A11Y-02: Screen reader compatibility (NVDA / VoiceOver)
**Summary:** Key page content and interactive elements should be announced correctly by screen readers.
**Test Steps:**
1. Enable NVDA (Windows) or VoiceOver (macOS).
2. Navigate to each page and verify:
   - Page headings are announced (e.g., "Dashboard", "Forecast")
   - Form labels are read with their inputs ("Month", "kWh", "Email", "Password")
   - Buttons announce their purpose ("Submit", "Train Model", "Ask", "Clear Chat")
   - Stat cards announce their values ("This Month: 342 kWh")
   - Error messages are announced when they appear
   - Navigation links announce their destination
3. Submit a form and verify the success/error message is announced.
**Test Data:** Screen reader: NVDA 2024+ or VoiceOver (macOS 14+)
**Expected Result:** All headings, labels, buttons, and dynamic content are announced meaningfully. No unlabeled buttons (announced as "button" without text). Form inputs have associated labels. Error messages are live-announced.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:** Full WCAG compliance requires manual testing with assistive technologies and expert accessibility review.

---

### A11Y-03: Color contrast ratios (WCAG AA)
**Summary:** Text and interactive elements should meet WCAG AA contrast ratio requirements (4.5:1 for normal text, 3:1 for large text).
**Test Steps:**
1. Open the application in light mode.
2. Use Chrome DevTools → Accessibility → Contrast check (or axe DevTools extension).
3. Check contrast for:
   - Body text against background
   - Sidebar text against sidebar background
   - Button text against button background
   - Stat card labels against card background
   - Input placeholder text
   - Error message text
4. Switch to dark mode and repeat all checks.
**Test Data:** Light mode and dark mode, checked with automated contrast tool
**Expected Result:** All text meets 4.5:1 contrast ratio (normal text) or 3:1 (large text ≥18px). No contrast failures in either light or dark mode. Placeholder text meets 3:1 minimum.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### A11Y-04: Focus indicators on all interactive elements
**Summary:** A visible focus indicator (outline/ring) should appear on every focused element.
**Test Steps:**
1. Use Tab to navigate through the application.
2. For each focused element, verify a visible focus indicator is present:
   - Sidebar links
   - Form inputs (text, dropdowns, buttons)
   - Horizon selector buttons
   - Chat send button
   - Dark mode toggle
   - Pagination controls
   - Edit/Delete buttons in Entry History
**Test Data:** Keyboard Tab navigation through all pages
**Expected Result:** Every focusable element shows a visible focus ring/outline that is clearly distinguishable from the unfocused state. Focus indicator has sufficient contrast (3:1 against adjacent colors).
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### A11Y-05: ARIA labels on custom components
**Summary:** Custom interactive components (icon buttons, toggles, charts) should have ARIA labels.
**Test Steps:**
1. Open browser DevTools → Elements panel.
2. Inspect the following elements for `aria-label`, `aria-labelledby`, or `aria-describedby` attributes:
   - Dark mode toggle button (has no visible text)
   - Hamburger menu button (☰)
   - Close drawer button (×)
   - Health indicator dots
   - Pagination arrow buttons (‹ ›)
   - Edit/Delete icon buttons (if icon-only)
   - Chart containers
3. Verify each has a meaningful label describing its function.
**Test Data:** Inspect DOM elements via DevTools
**Expected Result:** All icon-only buttons have `aria-label` (e.g., "Toggle dark mode", "Open menu", "Next page"). Chart containers have `aria-label` describing the chart content. No interactive elements are unlabeled.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### A11Y-06: Accessible chart alternatives
**Summary:** Charts should provide alternative text or data table access for screen reader users.
**Test Steps:**
1. Navigate to the Forecast page with an active forecast.
2. Inspect the chart container for:
   - `role="img"` with an `aria-label` describing the chart
   - Or a visually hidden data table summarizing the chart values
   - Or `aria-describedby` pointing to a summary
3. Test with a screen reader — attempt to understand the forecast data without seeing the chart.
**Test Data:** Active 3-month forecast with chart rendered
**Expected Result:** Screen reader users can understand the forecast data through at least one of: ARIA label describing the chart, a hidden data table, or descriptive text. The chart is not completely invisible to assistive technology.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:** Recharts library has limited native accessibility. Consider adding a visually hidden summary table as a fallback.
