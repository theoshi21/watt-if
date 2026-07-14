# Test Cases — Security

**Area:** Cross-Cutting — Security Testing  
**Prefix:** SEC  
**Document Version:** 1.0  
**Date:** July 2026  
**Prepared by:** QA Team

---

**Pre-condition:** The backend is running on port 8000 and the frontend is open in a browser. A valid user account exists.  
**Dependencies:** Backend API endpoints must be reachable. An API client (browser DevTools or Postman) for direct API calls.  
**Test Priority:** Critical

---

### SEC-01: SQL Injection via input fields
**Summary:** SQL injection attempts in form fields should be sanitized and rejected.
**Test Steps:**
1. Navigate to the Data Entry page.
2. In the month field (or any text input), enter: `2024-01'; DROP TABLE monthly_bill_records;--`
3. In the kWh field, enter: `100 OR 1=1`
4. Click **Submit**.
5. Attempt similar injection in the Login email field: `' OR '1'='1`
**Test Data:** SQL injection strings: `'; DROP TABLE monthly_bill_records;--`, `100 OR 1=1`, `' OR '1'='1`
**Expected Result:** All injection attempts are rejected with appropriate validation errors. No SQL is executed. Database integrity is maintained. Login fails with generic "Invalid credentials" message.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### SEC-02: Cross-Site Scripting (XSS) via text inputs
**Summary:** JavaScript injection in input fields should be escaped and not executed.
**Test Steps:**
1. Navigate to the Ask WATT-IF page.
2. Type: `<script>alert('XSS')</script>` and send the message.
3. Navigate to Data Entry and enter a label containing: `<img src=x onerror=alert(1)>`
4. Check if any script executes in the browser.
**Test Data:** XSS payloads: `<script>alert('XSS')</script>`, `<img src=x onerror=alert(1)>`, `javascript:alert(1)`
**Expected Result:** No JavaScript executes. Input is either rejected or displayed as escaped text. No alert dialogs appear.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### SEC-03: CSV injection (formula injection via uploaded data)
**Summary:** CSV cells beginning with `=`, `+`, `-`, or `@` should not trigger formula execution.
**Test Steps:**
1. Create a CSV file with cells containing:
   - `=CMD('calc')`
   - `+CMD('calc')`
   - `-1+1`
   - `@SUM(A1:A10)`
2. Upload the CSV via the Data Entry page.
3. View the entries in Entry History.
4. Export/download any data if export functionality exists.
**Test Data:** CSV with formula injection payloads in kWh/price columns
**Expected Result:** Values are treated as literal strings (rejected as invalid numeric) or sanitized. No system commands execute. Data displays safely.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### SEC-04: Unauthorized API access (invalid/missing tokens)
**Summary:** Protected endpoints should reject requests without valid JWT tokens.
**Test Steps:**
1. Using browser DevTools or an API client, send requests to protected endpoints without an Authorization header:
   - `GET /data-entries`
   - `POST /forecast`
   - `GET /settings`
2. Send requests with an expired/invalid JWT:
   - `Authorization: Bearer invalid.token.here`
3. Send requests with another user's valid token to endpoints that scope data.
**Test Data:** No token; invalid token: `invalid.token.here`; expired token
**Expected Result:** All requests without valid tokens return HTTP 401 Unauthorized. Requests with another user's token cannot access the first user's data (HTTP 403).
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### SEC-05: Session timeout and token expiry
**Summary:** JWT tokens should expire after 24 hours and force re-authentication.
**Test Steps:**
1. Log in and note the token in localStorage.
2. Decode the JWT to verify the `exp` claim is set to ~24 hours from now.
3. Manually set the system clock forward by 25 hours (or modify the token's `exp` to a past timestamp).
4. Attempt to navigate to a protected page.
**Test Data:** Manipulated JWT with expired `exp` claim
**Expected Result:** The application detects the expired token, clears it from localStorage, and redirects to the Login page.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**

---

### SEC-06: Authentication bypass attempts
**Summary:** Common auth bypass techniques should fail.
**Test Steps:**
1. Try accessing `/forecast` directly in the URL bar without logging in.
2. Try modifying the JWT payload (change user_id) without re-signing.
3. Try using a JWT signed with a different secret key.
4. Try sending the login request with `Content-Type: text/plain` instead of JSON.
**Test Data:** Tampered JWTs, wrong content types, direct URL access
**Expected Result:** All bypass attempts fail. Modified JWTs are rejected (signature mismatch). Direct URL access redirects to login. Wrong content types return 422.
**Actual Result:** _(to be filled during testing)_
**Status:** ⬜ Not Run
**Notes:**
