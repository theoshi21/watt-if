# Test Cases — Account System

**Module:** Account System (Registration, Login, Logout, Session, Data Isolation)
**Prefix:** ACT
**Document Version:** 1.0
**Date:** July 2026
**Prepared by:** QA Team

---

**Pre-condition:** The backend is running on port 8000 and the frontend is open in a browser. The database has been initialized (migrations complete). The Default Account (wattif@gmail.com / wattif) exists.
**Dependencies:** None (no external services required for auth testing).
**Test Priority:** Critical

---

## Registration

### ACT-01: Valid registration — new email and strong password
**Summary:** Submitting a valid email and a password ≥8 characters creates a new account and auto-logs in.
**Test Steps:**
1. Navigate to the Registration page (click "Register" link from the Login page).
2. In the Email field, type `testuser@example.com`.
3. In the Password field, type `SecurePass1`.
4. In the Confirm Password field, type `SecurePass1`.
5. Click **Register**.
**Test Data:** Email: `testuser@example.com`, Password: `SecurePass1`, Confirm Password: `SecurePass1`
**Expected Result:** Registration succeeds. The user is automatically logged in and redirected to the Dashboard page.
**Post-condition:** The user `testuser@example.com` exists in the database. The user is authenticated.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-02: Invalid registration — duplicate email
**Summary:** Attempting to register with an email that already exists shows an error.
**Test Steps:**
1. Navigate to the Registration page.
2. In the Email field, type `wattif@gmail.com` (the Default Account email).
3. In the Password field, type `SomePass123`.
4. In the Confirm Password field, type `SomePass123`.
5. Click **Register**.
**Test Data:** Email: `wattif@gmail.com`, Password: `SomePass123`, Confirm Password: `SomePass123`
**Expected Result:** An error message is displayed indicating the email is already registered. No duplicate account is created.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-03: Invalid registration — password too short
**Summary:** A password shorter than 8 characters prevents form submission.
**Test Steps:**
1. Navigate to the Registration page.
2. In the Email field, type `short@example.com`.
3. In the Password field, type `abc`.
4. In the Confirm Password field, type `abc`.
5. Observe the Submit button state.
**Test Data:** Email: `short@example.com`, Password: `abc`, Confirm Password: `abc`
**Expected Result:** The Submit button remains disabled because the password is fewer than 8 characters. No registration request is made.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-04: Invalid registration — passwords do not match
**Summary:** Mismatched password and confirm-password fields prevent form submission.
**Test Steps:**
1. Navigate to the Registration page.
2. In the Email field, type `mismatch@example.com`.
3. In the Password field, type `ValidPass1`.
4. In the Confirm Password field, type `DifferentPass2`.
5. Observe the Submit button state.
**Test Data:** Email: `mismatch@example.com`, Password: `ValidPass1`, Confirm Password: `DifferentPass2`
**Expected Result:** The Submit button remains disabled because password and confirm-password do not match.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-05: Invalid registration — invalid email format
**Summary:** An email without proper format (missing "@" or domain) is rejected by the backend.
**Test Steps:**
1. Navigate to the Registration page.
2. In the Email field, type `notanemail`.
3. In the Password field, type `ValidPass1`.
4. In the Confirm Password field, type `ValidPass1`.
5. Click **Register**.
**Test Data:** Email: `notanemail`, Password: `ValidPass1`, Confirm Password: `ValidPass1`
**Expected Result:** An error message is displayed indicating invalid email format. No account is created.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Login

### ACT-06: Valid login — correct credentials
**Summary:** Logging in with a valid email and password grants access and redirects to the Dashboard.
**Test Steps:**
1. Navigate to the Login page.
2. In the Email field, type `wattif@gmail.com`.
3. In the Password field, type `wattif`.
4. Click **Login**.
**Test Data:** Email: `wattif@gmail.com`, Password: `wattif`
**Expected Result:** Login succeeds. The user is redirected to the Dashboard page. The user's email is visible in the Sidebar.
**Post-condition:** A JWT token is stored in localStorage under the key "wattif_token".
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-07: Invalid login — wrong password
**Summary:** Logging in with a correct email but wrong password shows a generic error.
**Test Steps:**
1. Navigate to the Login page.
2. In the Email field, type `wattif@gmail.com`.
3. In the Password field, type `wrongpassword`.
4. Click **Login**.
**Test Data:** Email: `wattif@gmail.com`, Password: `wrongpassword`
**Expected Result:** A generic "Invalid credentials" error message is displayed. No token is stored. The user remains on the Login page.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-08: Invalid login — non-existent email
**Summary:** Logging in with an unregistered email shows the same generic error as a wrong password.
**Test Steps:**
1. Navigate to the Login page.
2. In the Email field, type `nobody@nowhere.com`.
3. In the Password field, type `SomePass123`.
4. Click **Login**.
**Test Data:** Email: `nobody@nowhere.com`, Password: `SomePass123`
**Expected Result:** A generic "Invalid credentials" error message is displayed (identical to ACT-07). No information leak about email existence.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-09: Login rate limiting — 10+ failed attempts
**Summary:** After 10 failed login attempts for the same email within 15 minutes, further attempts are blocked.
**Test Steps:**
1. Navigate to the Login page.
2. Type `wattif@gmail.com` in the Email field.
3. Type an incorrect password and click **Login**. Repeat this 10 times.
4. On the 11th attempt, type an incorrect password and click **Login**.
**Test Data:** Email: `wattif@gmail.com`, Password: `wrong` (repeated 11 times)
**Expected Result:** The first 10 attempts each show "Invalid credentials". The 11th attempt returns an error indicating too many login attempts (HTTP 429). The user must wait before trying again.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Logout

### ACT-10: Logout — token cleared and redirected to Login
**Summary:** Clicking the Logout button removes the session and redirects to the Login page.
**Test Steps:**
1. Log in as `wattif@gmail.com` (from ACT-06).
2. Verify the Dashboard is displayed and the email appears in the Sidebar.
3. Click the **Logout** button in the Sidebar.
**Test Data:** N/A
**Expected Result:** The user is redirected to the Login page within 1 second. The "wattif_token" key is removed from localStorage. Navigating to any protected page (e.g., Dashboard) redirects back to Login.
**Post-condition:** No token in localStorage. User is unauthenticated.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-11: Logout — graceful handling when network is unavailable
**Summary:** Logout still clears the local session even if a network error occurs.
**Test Steps:**
1. Log in as `wattif@gmail.com`.
2. Open browser DevTools → Network tab → set to "Offline" mode.
3. Click the **Logout** button in the Sidebar.
**Test Data:** N/A
**Expected Result:** The user is redirected to the Login page. The "wattif_token" key is removed from localStorage despite the network being offline.
**Post-condition:** No token in localStorage.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Session Persistence

### ACT-12: Session persists across page refresh
**Summary:** After logging in and refreshing the page, the user remains authenticated.
**Test Steps:**
1. Log in as `wattif@gmail.com`.
2. Verify the Dashboard is displayed.
3. Press F5 (or Cmd+R) to refresh the browser.
**Test Data:** N/A
**Expected Result:** After the page reloads, the user is still on the Dashboard (not redirected to Login). The email is still shown in the Sidebar.
**Post-condition:** Token remains in localStorage and is still valid.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-13: Expired token forces re-login
**Summary:** If the JWT token has expired, the user is redirected to the Login page on next page load.
**Test Steps:**
1. Log in as `wattif@gmail.com`.
2. Open browser DevTools → Application → Local Storage.
3. Manually modify the "wattif_token" value to a token with an expired `exp` claim (or wait 24 hours).
4. Refresh the page.
**Test Data:** Manually tampered or expired JWT token.
**Expected Result:** The user is redirected to the Login page. The invalid token is removed from localStorage.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-14: API 401 response triggers session clearance
**Summary:** If a protected API endpoint returns 401 during an active session, the user is logged out.
**Test Steps:**
1. Log in as `wattif@gmail.com`.
2. Open browser DevTools → Application → Local Storage.
3. Replace the "wattif_token" value with an invalid string (e.g., `invalid.token.here`).
4. Trigger an API call by navigating to the Data Entry page or performing any action that calls the backend.
**Test Data:** Token manually replaced with `invalid.token.here`.
**Expected Result:** The API returns 401. The application clears the token from localStorage and redirects to the Login page.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Data Isolation

### ACT-15: User A cannot see User B's data entries
**Summary:** Each user's data entries are isolated; one user cannot view another user's records.
**Test Steps:**
1. Log in as `wattif@gmail.com`. Add a manual entry for month `2025-01` with 400 kWh. Verify it appears in Entry History.
2. Log out.
3. Register a new account `userb@example.com` with password `UserBPass1`.
4. After auto-login, navigate to the Data Entry page.
5. Check the Entry History table.
**Test Data:** User A: `wattif@gmail.com`, Entry: 2025-01 / 400 kWh. User B: `userb@example.com`.
**Expected Result:** User B's Entry History is empty — User A's entry (2025-01, 400 kWh) is not visible to User B.
**Post-condition:** Each user's data remains isolated.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-16: User A cannot see User B's chat history
**Summary:** Chat messages are isolated per user.
**Test Steps:**
1. Log in as `wattif@gmail.com`. Go to the Ask page and send "Hello from User A". Verify the message appears.
2. Log out.
3. Log in as `userb@example.com` (registered in ACT-15).
4. Go to the Ask page.
**Test Data:** User A message: "Hello from User A".
**Expected Result:** User B's chat history is empty. The message "Hello from User A" is not visible.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-17: User A cannot edit or delete User B's entries
**Summary:** Attempting to modify another user's data entry returns a 403 Forbidden error.
**Test Steps:**
1. Log in as `wattif@gmail.com`. Note the ID of an existing entry (e.g., from ACT-15).
2. Log out and log in as `userb@example.com`.
3. Using browser DevTools (or an API client), send a PUT or DELETE request to `/data-entries/{id}` for User A's entry, using User B's valid token.
**Test Data:** User B's token targeting User A's entry ID.
**Expected Result:** The API returns HTTP 403 Forbidden. User A's entry remains unchanged.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-18: User's trained model is isolated
**Summary:** Each user's SARIMAX model is trained only on their own data.
**Test Steps:**
1. Log in as `wattif@gmail.com`. Upload `data/synthetic_2022_2025.csv` and click **Train Model**. Wait for training to complete.
2. Navigate to the Forecast page. Verify a forecast is displayed.
3. Log out.
4. Log in as `userb@example.com`.
5. Navigate to the Forecast page.
**Test Data:** User A has uploaded data and trained model. User B has no data.
**Expected Result:** User B sees an error/message indicating no trained model is available (HTTP 503 from backend). User A's forecast is not shown to User B.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

## Error Handling

### ACT-19: Unauthenticated access to protected route redirects to Login
**Summary:** Navigating directly to a protected page without a token redirects to the Login page.
**Test Steps:**
1. Ensure no token exists in localStorage (clear it if present).
2. Navigate directly to `http://localhost:5173/` (Dashboard).
**Test Data:** N/A
**Expected Result:** The user is immediately redirected to the Login page. No protected content is shown.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-20: Authenticated user visiting Login page is redirected to Dashboard
**Summary:** An already-authenticated user cannot access the Login or Registration pages.
**Test Steps:**
1. Log in as `wattif@gmail.com`. Verify you are on the Dashboard.
2. Manually navigate to `http://localhost:5173/login`.
3. Manually navigate to `http://localhost:5173/register`.
**Test Data:** N/A
**Expected Result:** Both navigation attempts redirect the user back to the Dashboard. The Login and Registration pages are not displayed.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-21: Password change — valid current password and valid new password
**Summary:** Successfully changing the password from the Account Settings page.
**Test Steps:**
1. Log in as `wattif@gmail.com`.
2. Click the Account icon in the top bar to navigate to Account Settings.
3. In the Current Password field, type `wattif`.
4. In the New Password field, type `NewSecure1`.
5. In the Confirm New Password field, type `NewSecure1`.
6. Click **Change Password**.
**Test Data:** Current: `wattif`, New: `NewSecure1`, Confirm: `NewSecure1`
**Expected Result:** A success message is displayed. The user can log out and log back in with the new password `NewSecure1`.
**Post-condition:** Password is updated. Reset it back to `wattif` after testing if needed.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### ACT-22: Password change — incorrect current password
**Summary:** Providing the wrong current password prevents the password change.
**Test Steps:**
1. Log in as `wattif@gmail.com`.
2. Navigate to Account Settings.
3. In the Current Password field, type `wrongcurrent`.
4. In the New Password field, type `NewSecure1`.
5. In the Confirm New Password field, type `NewSecure1`.
6. Click **Change Password**.
**Test Data:** Current: `wrongcurrent`, New: `NewSecure1`, Confirm: `NewSecure1`
**Expected Result:** An error message is displayed indicating the current password is incorrect. The password is not changed.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
