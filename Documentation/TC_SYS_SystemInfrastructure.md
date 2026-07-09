# Test Cases — System & Infrastructure

**Module:** Module 7 — System & Infrastructure (Navigation, Theme, Mobile, Health, Offline)  
**Prefix:** SYS  
**Document Version:** 2.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

**Pre-condition:** The app is open in a browser. No specific data state required unless noted.  
**Dependencies:** None (except Ollama for health indicator tests).  
**Test Priority:** Medium

---

### SYS-01: Toggle dark mode
**Summary:** Theme switches to dark color scheme.
**Test Steps:**
1. Click dark/light mode toggle (sun/moon icon).
**Expected Result:** All elements switch to dark palette.
**Status:** ⬜ Not Run

---

### SYS-02: Toggle back to light mode
**Summary:** Theme returns to light.
**Test Steps:**
1. Click toggle again from dark mode.
**Expected Result:** Light color scheme restored.
**Status:** ⬜ Not Run

---

### SYS-03: Theme persists after refresh
**Summary:** Preference saved in localStorage.
**Test Steps:**
1. Switch to dark mode. Refresh page (F5).
**Expected Result:** App reloads in dark mode.
**Status:** ⬜ Not Run

---

### SYS-04: Sidebar navigation — correct pages
**Summary:** Each link loads the correct page.
**Test Steps:**
1. Click each sidebar link: Dashboard, Forecast, Ask WATT-IF, Price Calculator, Data Entry.
**Expected Result:** Each navigates to the correct page with matching content.
**Status:** ⬜ Not Run

---

### SYS-05: Active navigation item highlighted
**Summary:** Current page link visually distinct.
**Test Steps:**
1. Navigate to each page. Check sidebar highlight.
**Expected Result:** Active link has distinct styling (background/bold).
**Status:** ⬜ Not Run

---

### SYS-06: Mobile — sidebar hidden, opens via hamburger
**Summary:** Sidebar drawer on mobile.
**Test Steps:**
1. Resize to ≤767px or simulate phone. Click ☰ button.
**Expected Result:** Sidebar hidden by default. Hamburger reveals it.
**Status:** ⬜ Not Run

---

### SYS-07: Mobile — sidebar closes on overlay tap
**Summary:** Overlay dismiss closes drawer.
**Test Steps:**
1. Open mobile sidebar. Tap overlay.
**Expected Result:** Sidebar closes, overlay disappears.
**Status:** ⬜ Not Run

---

### SYS-08: Mobile — sidebar closes on Escape
**Summary:** Escape key closes drawer.
**Test Steps:**
1. Open mobile sidebar. Press Escape.
**Expected Result:** Sidebar closes.
**Status:** ⬜ Not Run

---

### SYS-09: Health indicator — all green
**Summary:** All systems operational.
**Test Steps:**
1. Ensure backend + Ollama running with data. Check health indicator.
**Expected Result:** All subsystem indicators green/OK.
**Status:** ⬜ Not Run

---

### SYS-10: Health indicator — degraded (Ollama offline)
**Summary:** Ollama offline shows degraded state.
**Test Steps:**
1. Stop Ollama. Wait 30s. Check health indicator.
**Expected Result:** Ollama subsystem shows degraded. Others remain green.
**Status:** ⬜ Not Run

---

### SYS-11: Offline banner appears when disconnected
**Summary:** Network loss shows banner.
**Test Steps:**
1. Set browser to Offline mode.
**Expected Result:** Offline banner appears. App doesn't crash. Cached content still visible.
**Status:** ⬜ Not Run
