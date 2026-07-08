# Requirements Document

## Introduction

WATT-IF currently operates as a single-user application with no authentication or data isolation. This feature introduces a login and account system so that multiple users can each have their own trained SARIMAX model, forecast data, and chat history — all isolated from one another. The system adds user registration, login, session management, and per-user data scoping to both the FastAPI backend and the React frontend.

## Glossary

- **Account_System**: The authentication and authorization subsystem responsible for user registration, login, logout, session validation, and per-user data isolation.
- **User**: A registered individual with a unique email address and credentials stored in the WATT-IF database.
- **Default_Account**: A pre-seeded user account that exists in the database on first application startup, allowing immediate use without registration.
- **Session**: A time-limited authentication token (JWT) issued upon successful login that authorizes subsequent API requests.
- **Protected_Endpoint**: Any API endpoint that requires a valid Session token to access.
- **User_Data_Store**: The per-user partition of the SQLite database containing that user's monthly bill records, data entry log, training log, and chat history.
- **Model_Artefact**: The serialized SARIMAX model file produced by training, stored per-user on the filesystem.
- **Auth_Router**: The FastAPI router handling registration, login, logout, and token refresh endpoints.
- **Login_Page**: The frontend page where users enter credentials to authenticate.
- **Registration_Page**: The frontend page where new users create an account.
- **Account_Settings_Page**: The frontend page accessible from the top bar where users can view and manage their account details.
- **Account_Icon**: A user avatar or icon button displayed in the upper-right area of the top bar that opens account-related actions.

## Requirements

### Requirement 1: Default Account

**User Story:** As a first-time user, I want the application to work immediately without requiring registration, so that I can start using WATT-IF right away.

#### Acceptance Criteria

1. WHEN the application database is initialized for the first time, THE Account_System SHALL create a Default_Account with a pre-configured email of "wattif@gmail.com" and a password of "wattif" stored using the same bcrypt hashing as registered User accounts.
2. IF no registered User accounts other than the Default_Account exist and no stored Session token is present, THEN THE Account_System SHALL automatically log the user in with the Default_Account and store the resulting Session token.
3. THE Default_Account SHALL function identically to any registered User account, owning its own User_Data_Store, Model_Artefact, and chat history.
4. WHEN existing data with no user_id is found during migration, THE Account_System SHALL assign it to the Default_Account by setting the user_id column to the Default_Account's identifier.
5. THE Account_System SHALL allow the Default_Account credentials to be changed through the Account_Settings_Page.
6. IF additional User accounts have been registered, THEN THE Account_System SHALL disable automatic login for the Default_Account and redirect unauthenticated users to the Login_Page.

### Requirement 2: User Registration

**User Story:** As a new user, I want to create an account with my email and password, so that I can have my own isolated data and forecasts.

#### Acceptance Criteria

1. WHEN a valid email and password are submitted to the registration endpoint, THE Account_System SHALL create a new User record with a hashed password and return HTTP 201 with the User's email in the response body.
2. WHEN an email that already exists in the database is submitted for registration, THE Account_System SHALL reject the request with HTTP 409 and a message indicating the email is already registered.
3. THE Account_System SHALL validate that the password is at least 8 characters long and reject submissions that fail this check with HTTP 422 and a message indicating the minimum length.
4. THE Account_System SHALL validate that the email contains exactly one "@" character with at least one character before it and a domain with at least one "." after it, and reject invalid emails with HTTP 422 and a message indicating invalid email format.
5. THE Account_System SHALL validate that the email does not exceed 254 characters in length.
6. WHEN registration succeeds, THE Account_System SHALL create an empty User_Data_Store partition for the new User.
7. THE Account_System SHALL store passwords using bcrypt hashing with a minimum cost factor of 12.

### Requirement 3: User Login

**User Story:** As a registered user, I want to log in with my email and password, so that I can access my personal data and forecasts.

#### Acceptance Criteria

1. WHEN valid credentials are submitted to the login endpoint, THE Account_System SHALL return a JWT Session token with an expiration time of 24 hours.
2. WHEN an incorrect password is submitted, THE Account_System SHALL reject the request with HTTP 401 and a generic "invalid credentials" error message.
3. WHEN a non-existent email is submitted, THE Account_System SHALL reject the request with HTTP 401 and the same generic "invalid credentials" error message used for incorrect passwords.
4. THE Account_System SHALL include the User identifier in the JWT token payload.
5. WHEN a login request is received, THE Account_System SHALL respond within 500 milliseconds.
6. WHEN either the email or password field is missing or empty, THE Account_System SHALL reject the request with HTTP 422 and a message indicating the missing field.
7. THE Account_System SHALL rate-limit login attempts to a maximum of 10 failed attempts per email address within a 15-minute window, returning HTTP 429 when the limit is exceeded.

### Requirement 4: Session Management

**User Story:** As an authenticated user, I want my session to persist across page refreshes, so that I do not need to log in repeatedly.

#### Acceptance Criteria

1. WHEN login succeeds, THE Account_System SHALL store the JWT Session token in browser localStorage under the key "wattif_token".
2. WHEN a page is loaded, THE Account_System SHALL check localStorage for a stored Session token, verify the token's expiry claim has not passed, and only render protected content if the token is present and not expired, completing this check within 1 second.
3. IF a Session token is expired or invalid upon page load validation, THEN THE Account_System SHALL remove the stored token from localStorage and redirect the user to the Login_Page.
4. WHEN the user clicks logout, THE Account_System SHALL remove the Session token from localStorage and redirect to the Login_Page.
5. THE Account_System SHALL attach the Session token as a Bearer token in the Authorization header of all API requests to Protected_Endpoints.
6. IF a Protected_Endpoint returns HTTP 401 during an active session, THEN THE Account_System SHALL remove the stored Session token from localStorage and redirect the user to the Login_Page.

### Requirement 5: Protected Endpoints

**User Story:** As an authenticated user, I want all my API interactions to be secured, so that unauthenticated users cannot access my data.

#### Acceptance Criteria

1. THE Account_System SHALL require a valid Session token for all endpoints except: registration, login, and health check, where valid means the token is well-formed, has a correct cryptographic signature, and is not expired.
2. WHEN a request to a Protected_Endpoint is missing a Session token, THE Account_System SHALL return HTTP 401 Unauthorized.
3. WHEN a request to a Protected_Endpoint contains an expired Session token, THE Account_System SHALL return HTTP 401 Unauthorized.
4. WHEN a request to a Protected_Endpoint contains a malformed Session token or a token with an invalid cryptographic signature, THE Account_System SHALL return HTTP 401 Unauthorized.
5. THE Account_System SHALL extract the User identifier from the validated Session token and use it to scope all data operations to that User's records.
6. IF a validated Session token contains a User identifier that does not correspond to an existing User in the database, THEN THE Account_System SHALL return HTTP 401 Unauthorized.

### Requirement 6: Per-User Data Isolation — Bill Records and Entries

**User Story:** As an authenticated user, I want my uploaded bill data and manual entries to be visible only to me, so that my data is private.

#### Acceptance Criteria

1. WHEN a User uploads a CSV or creates a manual entry, THE Account_System SHALL associate every persisted record with that User's identifier extracted from the validated Session token.
2. WHEN a User queries their data entries, THE Account_System SHALL return only records belonging to that User, returning an empty list if the User has no records.
3. WHEN a User requests to edit or delete a data entry, THE Account_System SHALL verify the entry belongs to that User before performing the operation.
4. IF a User attempts to edit or delete an entry belonging to a different User, THEN THE Account_System SHALL return HTTP 403 Forbidden with an error message indicating access is denied, and SHALL NOT modify the entry.
5. IF a User attempts to edit or delete an entry ID that does not exist, THEN THE Account_System SHALL return HTTP 404 Not Found.
6. THE Account_System SHALL add a non-nullable user_id column to the monthly_bill_records and data_entry_log tables, referencing the users table.
7. THE Account_System SHALL filter all SELECT, UPDATE, and DELETE queries on monthly_bill_records and data_entry_log by the authenticated User's identifier.

### Requirement 7: Per-User Data Isolation — Trained Model

**User Story:** As an authenticated user, I want my trained SARIMAX model to be isolated from other users, so that my forecasts are based solely on my data.

#### Acceptance Criteria

1. WHEN a User triggers model training, THE Account_System SHALL train the SARIMAX model using only that User's bill records from the User_Data_Store and store the resulting Model_Artefact in that User's designated file path.
2. WHEN a User requests a forecast, THE Account_System SHALL load the Model_Artefact from that User's designated file path, derived from the authenticated User's identifier.
3. IF a User requests a forecast but no Model_Artefact exists at that User's designated file path, THEN THE Account_System SHALL return HTTP 503 with a message indicating the model has not been trained.
4. THE Account_System SHALL store Model_Artefacts at `data/models/{user_id}/sarimax_artefact.json`, creating the directory if it does not exist.
5. WHEN a User clears all data, THE Account_System SHALL delete that User's Model_Artefact file and the containing user directory, as well as that User's records in the monthly_bill_records, data_entry_log, training_log, and chat_history tables.
6. IF model training fails after being triggered, THEN THE Account_System SHALL preserve any previously existing Model_Artefact for that User unchanged and return an error message indicating the training failure reason.

### Requirement 8: Per-User Data Isolation — Chat History

**User Story:** As an authenticated user, I want my chat history to be private, so that other users cannot see my conversations.

#### Acceptance Criteria

1. WHEN a User sends a message or receives a response, THE Account_System SHALL associate the chat record with that User's identifier.
2. WHEN a User loads their chat history, THE Account_System SHALL return only messages belonging to that User, limited to the 100 most recent messages ordered by creation time ascending.
3. WHEN a User clears their chat history, THE Account_System SHALL delete only that User's chat records and return HTTP 204.
4. THE Account_System SHALL add a user_id column to the chat_history table.
5. IF a User attempts to access or delete chat records belonging to a different User, THEN THE Account_System SHALL return HTTP 403 Forbidden and leave the records unchanged.

### Requirement 9: Frontend Authentication Flow

**User Story:** As a user, I want to see a login page when I am not authenticated, so that I understand I need to sign in to use the application.

#### Acceptance Criteria

1. WHEN an unauthenticated user navigates to any application route other than the Login_Page or Registration_Page, THE Account_System SHALL redirect them to the Login_Page.
2. THE Login_Page SHALL display a labelled email input field, a labelled password input field (masked), and a submit button.
3. THE Login_Page SHALL display a link to the Registration_Page for new users.
4. WHEN login succeeds, THE Account_System SHALL redirect the user to the Dashboard page.
5. WHEN login fails, THE Login_Page SHALL display a single generic error message indicating invalid credentials, without revealing whether the email or password was incorrect.
6. THE Registration_Page SHALL display labelled email, password, and confirm-password input fields and a submit button, and SHALL disable the submit button until the password and confirm-password values match and the password is at least 8 characters long.
7. WHEN registration succeeds, THE Account_System SHALL automatically log the user in and redirect to the Dashboard page.
8. IF registration fails due to a validation error or duplicate email, THEN THE Registration_Page SHALL display an error message indicating the reason for failure.
9. IF an authenticated user navigates to the Login_Page or Registration_Page, THEN THE Account_System SHALL redirect them to the Dashboard page.

### Requirement 10: Frontend User Indicator and Logout

**User Story:** As an authenticated user, I want to see my identity in the UI and have a logout option, so that I can confirm I am logged in and switch accounts.

#### Acceptance Criteria

1. WHILE a User is authenticated, THE Account_System SHALL display the User's email address in the Sidebar bottom section, truncated with an ellipsis if the email exceeds 24 characters in display width.
2. WHILE a User is authenticated, THE Account_System SHALL display a logout button labelled "Logout" in the Sidebar bottom section, below the displayed email address.
3. WHEN the logout button is clicked, THE Account_System SHALL remove the Session token from localStorage and redirect to the Login_Page within 1 second.
4. IF the logout button is clicked and a network error prevents any server-side logout call, THEN THE Account_System SHALL still remove the local Session token and redirect to the Login_Page.
5. WHILE a User is authenticated, THE Account_System SHALL obtain the displayed email from the stored Session token payload without requiring an additional API request.

### Requirement 11: Account Settings UI

**User Story:** As an authenticated user, I want to access an account settings page from the top bar, so that I can view and manage my account details.

#### Acceptance Criteria

1. WHILE a User is authenticated, THE Account_System SHALL display an Account_Icon in the upper-right area of the top bar.
2. WHEN the Account_Icon is clicked, THE Account_System SHALL navigate to the Account_Settings_Page within 1 second.
3. THE Account_Settings_Page SHALL display the User's email address as read-only text.
4. THE Account_Settings_Page SHALL provide a password change form containing three fields: current password, new password, and confirm new password.
5. WHEN a password change is submitted where the new password is at least 8 characters long and the new password field matches the confirm new password field, THE Account_System SHALL update the password hash and display a success message that remains visible until the user dismisses it or navigates away.
6. IF the new password is fewer than 8 characters, THEN THE Account_System SHALL reject the submission and display an error message indicating the minimum length requirement.
7. IF the new password and confirm new password fields do not match, THEN THE Account_System SHALL reject the submission and display an error message indicating the passwords do not match.
8. IF the current password provided is incorrect, THEN THE Account_System SHALL reject the password change and display an error message indicating that the current password is incorrect.
9. THE Account_Settings_Page SHALL provide a logout button that clears the Session and redirects to the Login_Page.

### Requirement 12: Database Migration

**User Story:** As a developer, I want the database schema to be updated to support multi-user isolation, so that the backend correctly partitions data.

#### Acceptance Criteria

1. THE Account_System SHALL create a `users` table with columns: id (integer primary key), email (unique text, maximum 254 characters), password_hash (text), and created_at (text in ISO 8601 format).
2. THE Account_System SHALL add a `user_id` integer column to the monthly_bill_records, data_entry_log, chat_history, and training_log tables, referencing the `users` table id column.
3. WHEN the application starts, THE Account_System SHALL run schema migrations to add any missing tables and columns without modifying or deleting existing data.
4. THE Account_System SHALL ensure migrations are idempotent, so that running the migration multiple times on the same database produces no errors and no duplicate changes.
5. WHEN existing rows in monthly_bill_records, data_entry_log, chat_history, or training_log have a NULL user_id, THE Account_System SHALL assign them to the Default_Account's user id.
6. IF a schema migration fails, THEN THE Account_System SHALL log the error and prevent the application from serving requests until the migration succeeds.

### Requirement 13: Test Plan and Test Case Documentation

**User Story:** As a QA tester, I want updated test documentation covering the account system, so that I can verify authentication and data isolation work correctly.

#### Acceptance Criteria

1. THE Account_System SHALL include updates to the existing Test Plan document (Test_Plan.md) adding account system components (registration form, login form, logout action, session persistence mechanism, and data isolation behavior) to Section 2 (Test Items) and adding an "Account System" subsection to Section 3 (Features to Be Tested) listing registration, login, logout, session persistence, data isolation, and error handling as testable feature areas.
2. THE Account_System SHALL include a new Test Case document named TC_ACT_AccountSystem.md containing at least 1 test case per scenario category: registration, login, logout, session persistence, data isolation, and error handling, for a minimum of 6 test cases total.
3. THE Test Case document SHALL use the ACT prefix for all test case IDs and each test case SHALL include the following fields: test case ID (ACT-NN format), Summary, Pre-condition, Test Steps (numbered), Expected Result, Actual Result (blank for tester to fill), Status (defaulting to "⬜ Not Run"), and Notes.
4. THE Account_System SHALL include updates to Section 6 (Item Pass/Fail Criteria) of Test_Plan.md adding a row for account/authentication features defining pass and fail conditions for registration, login, logout, session persistence, and data isolation.
