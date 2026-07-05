# Requirements Document

## Introduction

This feature redesigns the WATT-IF frontend to match a new visual design mockup. The current single-page application with a top-header layout and inline styles is replaced by a multi-page, sidebar-navigated application using a formal CSS design token system. The redesign introduces `react-router-dom` for client-side routing across five pages (Dashboard, Forecast, Ask WATT-IF, Data Entry, Recommendations), a fixed dark-navy sidebar with icon navigation, a structured colour/typography design system, and a restyled version of every existing component. All existing backend integrations (forecast, chat, upload, health, model-info) remain functionally unchanged.

---

## Glossary

- **App**: The WATT-IF React 18 + TypeScript + Vite single-page application served from `frontend/`.
- **Design_Token_System**: A set of CSS custom properties (variables) declared on `:root` that define the canonical colour palette, typography scale, spacing, and shadow values used across all components.
- **Sidebar**: The fixed left navigation panel, approximately 220 px wide on desktop, containing the logo, navigation items, model-status pill, and settings link.
- **TopBar**: The horizontal bar at the top of each page content area containing the page title, dark-mode toggle icon, notifications icon, and user avatar icon.
- **Router**: The `react-router-dom` v6 client-side router mounted in `main.tsx`.
- **Dashboard_Page**: The page rendered at `/` showing stat cards, the Consumption History chart, and an Anomaly alert card.
- **Forecast_Page**: The page rendered at `/forecast` showing `ForecastChart` and `HorizonSelector`.
- **Ask_Page**: The page rendered at `/ask` showing `ChatPanel`.
- **DataEntry_Page**: The page rendered at `/data-entry` showing a New Reading form, the restyled `UploadPanel`, and a Session Log table.
- **Recommendations_Page**: The page rendered at `/recommendations` showing a placeholder card.
- **ForecastChart**: The existing Recharts-based composed chart component displaying kWh and price forecasts with 95% confidence intervals.
- **ChatPanel**: The existing SSE-streaming chat component for natural-language questions.
- **HealthIndicator**: The existing component that polls `/health` every 30 seconds and displays subsystem status dots.
- **HorizonSelector**: The existing 1m / 3m / 6m toggle button group component.
- **ModelEvaluation**: The existing component that fetches `/model-info` and displays MAPE metrics and model details.
- **OfflineBanner**: The existing sticky banner that displays when the browser is offline.
- **UploadPanel**: The existing CSV file upload and training-poll component.
- **ModelStatusPill**: A green pill element rendered at the bottom of the Sidebar showing "MODEL ACTIVE · MAPE X.X%" sourced from the `/model-info` API endpoint.
- **StatCard**: A white card component used on the Dashboard_Page to display a single KPI metric (label, value, unit).
- **SessionLog**: A table on the DataEntry_Page listing recent data entry events for the current browser session.
- **DarkModeToggle**: An icon button in the TopBar that toggles between the light and dark CSS theme.
- **AnomalyCard**: A card on the Dashboard_Page that surfaces an alert when forecast consumption deviates significantly from the monthly average.
- **Inter**: The primary sans-serif typeface loaded from Google Fonts, used for body text, headings, and UI labels.
- **SpaceMono**: The monospace typeface loaded from Google Fonts (Space Mono or IBM Plex Mono), used for metric values, status text, and data table cells.

---

## Requirements

### Requirement 1: Design Token System

**User Story:** As a developer, I want a single source-of-truth CSS variable system, so that colours, typography, and spacing are consistent across all components and can be updated in one place.

#### Acceptance Criteria

1. THE Design_Token_System SHALL define CSS custom properties on the `:root` selector covering: colour tokens (sidebar background, sidebar alternate, page background, primary accent, hover accent, teal, card background, text primary, text muted, text on accent, border, input fill, amber, red, and rating-level background/border/text for each of Excellent/Good/Fair/Poor), typography tokens (`--font-sans`, `--font-mono`), spacing/sizing tokens (`--radius-card`), and shadow tokens (`--shadow-card`, `--shadow-sidebar`).
2. THE Design_Token_System SHALL define a `[data-theme="dark"]` selector that provides an override value for every colour token defined on `:root`, so that applying `data-theme="dark"` to the `<html>` element changes all colours without leaving any token unset.
3. WHEN the Google Fonts stylesheet has been applied, THE App SHALL use the loaded Inter typeface for `--font-sans` and the loaded Space Mono typeface for `--font-mono` with system-ui and monospace as respective fallbacks.
4. WHEN a developer applies a colour, typography, or spacing value in any component, THE App SHALL reference a Design_Token_System CSS variable rather than a literal colour, font, or dimension value.
5. THE Design_Token_System SHALL be defined in a single CSS file that is imported exactly once at the application entry point, so all components share the same token definitions.

---

### Requirement 2: Google Fonts Integration

**User Story:** As a user, I want the UI to use Inter and Space Mono typefaces, so that the application matches the design mockup visually.

#### Acceptance Criteria

1. THE App SHALL include `<link rel="preconnect" href="https://fonts.googleapis.com">` and `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>` elements in `index.html` before the Google Fonts stylesheet link.
2. THE App SHALL include a `<link rel="stylesheet">` element in `index.html` that requests Inter (weights 400, 500, 600, 700) and Space Mono (weights 400, 700) from Google Fonts with `font-display=swap` to prevent invisible text during load.
3. IF the Google Fonts stylesheet is unavailable (e.g. browser is offline or the request fails), THE App SHALL render all text using the system-ui sans-serif fallback for `--font-sans` and the monospace fallback for `--font-mono`, with text remaining visible, line heights preserved, and no layout overflow introduced.

---

### Requirement 3: Client-Side Router Setup

**User Story:** As a developer, I want a client-side router, so that each section of the application has a distinct URL and the back/forward browser buttons work correctly.

#### Acceptance Criteria

1. THE App SHALL use push-state (history API) routing so that all route URLs take the form `/path` with no `#` fragment and are bookmarkable.
2. THE Router SHALL wrap the entire application shell, making all navigation link clicks update the browser URL and render the matching page component without triggering a full-page network request.
3. THE Router SHALL map the following paths to page components: `/` to Dashboard_Page, `/forecast` to Forecast_Page, `/ask` to Ask_Page, `/data-entry` to DataEntry_Page, `/recommendations` to Recommendations_Page.
4. WHEN a user navigates to a path that does not match any defined route, THE Router SHALL replace the current history entry with `/` and render the Dashboard_Page, so the invalid path does not remain in the browser history.
5. WHEN a user clicks a navigation link, THE Router SHALL push the new path onto the browser history stack so the browser's back button returns to the previously viewed page.
6. WHEN a user loads the application by directly entering a route URL (e.g. `/forecast`) into the browser address bar, THE Router SHALL render the correct page component for that path without a 404 error or redirect to `/`.

---

### Requirement 4: Application Shell Layout

**User Story:** As a user, I want a consistent page shell with a sidebar and top bar, so that navigation and branding are always visible regardless of which page I am viewing.

#### Acceptance Criteria

1. THE App SHALL render a persistent application shell on all five route pages, composed of the Sidebar on the left, the TopBar at the top of the main content area, and the page content below the TopBar.
2. IF the browser is offline, THE App SHALL render the OfflineBanner as a full-width element above the shell, with the Sidebar and main content area retaining their original positions and dimensions below it.
3. WHILE the viewport width is 768 px or wider, THE App SHALL display the Sidebar as a fixed panel occupying the full viewport height with a width of 220 px.
4. WHILE the viewport width is narrower than 768 px, THE App SHALL hide the Sidebar from view and display a hamburger menu icon button in the TopBar.
5. WHEN the user activates the hamburger menu icon on a mobile viewport, THE App SHALL slide in the Sidebar as an overlay drawer from the left edge of the screen without altering the dimensions of the main content area beneath the overlay.
6. WHEN the user taps outside the open Sidebar drawer on a mobile viewport, THE App SHALL close the Sidebar drawer.
7. WHEN the Sidebar drawer is open on a mobile viewport and the user presses the Escape key, THE App SHALL close the Sidebar drawer.

---

### Requirement 5: Sidebar Navigation

**User Story:** As a user, I want a clearly labelled navigation sidebar, so that I can move between sections of the application quickly.

#### Acceptance Criteria

1. THE Sidebar SHALL display the WATT-IF logo image and the text "ENERGY INTELLIGENCE" as a subtitle at the top of the panel.
2. THE Sidebar SHALL render six navigation items in order: Dashboard (`/`), Forecast (`/forecast`), Ask WATT-IF (`/ask`), Recommendations (`/recommendations`), Data Entry (`/data-entry`), each accompanied by a distinct icon, followed by a Settings link at the very bottom of the panel.
3. IF the current route matches a navigation item's path, THE Sidebar SHALL render that item with `--color-accent-primary` as its background colour and `--color-text-secondary` as its text colour to indicate the active state.
4. THE Sidebar SHALL render the ModelStatusPill above the Settings link at the bottom of the navigation area.
5. THE ModelStatusPill SHALL poll the `/model-info` endpoint on mount and re-poll every 60 seconds to keep its displayed value current.
6. WHEN the `/model-info` endpoint returns a non-null `mape_avg_pct` value, THE ModelStatusPill SHALL display the text "MODEL ACTIVE · MAPE X.X%" where X.X is `mape_avg_pct` formatted to one decimal place.
7. IF the `/model-info` endpoint returns a null `mape_avg_pct`, is still loading, or responds with an error, THE ModelStatusPill SHALL display "MODEL NOT TRAINED" using `--color-text-muted` styling.
8. THE Sidebar SHALL apply `--color-sidebar-bg` as its background colour and `--shadow-sidebar` as its box shadow.

---

### Requirement 6: Top Bar

**User Story:** As a user, I want a consistent page-level top bar, so that I always know which page I am on and can access global controls.

#### Acceptance Criteria

1. THE TopBar SHALL display the current page title as an `<h1>` element aligned to the left side of the bar.
2. THE TopBar SHALL display three icon-only buttons aligned to the right side: DarkModeToggle, a notifications bell icon, and a user avatar placeholder icon.
3. WHEN the user activates the DarkModeToggle button and no theme preference is stored, THE App SHALL default to the light theme; WHEN a stored preference exists, THE App SHALL restore it on load before the first render to prevent a flash of the wrong theme.
4. THE App SHALL persist the user's theme preference to `localStorage` under the key `wattif-theme` whenever the DarkModeToggle is activated.
5. THE notifications icon button and user avatar icon button SHALL be rendered as accessible `<button>` elements with descriptive `aria-label` attributes and SHALL have no functional behaviour in this release.
6. WHEN the application loads, THE App SHALL read the `wattif-theme` key from `localStorage` and apply the stored theme; IF the stored value is absent, unrecognised, or invalid, THE App SHALL default to the light theme.

---

### Requirement 7: Dashboard Page

**User Story:** As a user, I want a Dashboard overview page, so that I can see my most important energy metrics at a glance without navigating to individual sections.

#### Acceptance Criteria

1. THE Dashboard_Page SHALL render a grid of four StatCard components displaying: "This Month kWh" (sourced from `months[0].kwh_forecast`), "Daily Average kWh/day" (`months[0].kwh_forecast` divided by 30, rounded to two decimal places), "Temp Today °C" (a static placeholder value of "—"), and "Humidity %" (a static placeholder value of "—").
2. THE Dashboard_Page SHALL render the ForecastChart component in a "Consumption History" section below the StatCard grid, loaded with the 3-month horizon forecast data.
3. WHEN `months[0].kwh_forecast` exceeds 110% of the mean `kwh_forecast` across all entries in `months[]`, THE Dashboard_Page SHALL render the AnomalyCard with the message "Anomaly Detected: forecast consumption for [month] is [X.X]% above your average." where [month] is the formatted year-month of `months[0]` and [X.X] is the percentage excess rounded to one decimal place.
4. IF no forecast data has been loaded and the forecast request has not yet been made, THE Dashboard_Page SHALL render a prompt card instructing the user to navigate to the Data Entry page and upload a CSV.
5. IF the forecast request is in progress, THE Dashboard_Page SHALL render a loading skeleton or spinner in place of the StatCard grid and ForecastChart.
6. THE StatCard component SHALL use `--font-mono` for the metric value and `--font-sans` for the label text, and SHALL use `<dl>/<dt>/<dd>` or equivalent semantic markup.
7. THE AnomalyCard SHALL use a 4 px left border styled with `--color-teal` as its accent colour.

---

### Requirement 8: Forecast Page

**User Story:** As a user, I want a dedicated Forecast page, so that I can view my electricity consumption and bill forecasts with confidence interval charts.

#### Acceptance Criteria

1. THE Forecast_Page SHALL render the HorizonSelector component and the ForecastChart component.
2. WHEN the user selects a horizon using the HorizonSelector, THE Forecast_Page SHALL disable the HorizonSelector, fetch a new forecast from the `/forecast` endpoint, pass the updated months data to ForecastChart, and re-enable the HorizonSelector once the response has been received.
3. WHILE a forecast request is in flight, THE Forecast_Page SHALL render a loading indicator with `role="status"` that is visible to both sighted users and screen readers.
4. IF the `/forecast` endpoint returns a 503 status, THE Forecast_Page SHALL clear any previously displayed forecast data and render the message "No trained model found — upload a CSV on the Data Entry page to train the model first." inside a `role="alert"` region.
5. IF the `/forecast` endpoint returns a non-503 HTTP error or a network failure occurs, THE Forecast_Page SHALL clear any previously displayed forecast data and render a human-readable error message inside a `role="alert"` region.
6. WHEN the Forecast_Page first mounts and no training is in progress, THE Forecast_Page SHALL automatically request a forecast with the default horizon of 3 months.
7. THE HorizonSelector SHALL style the active button with `--color-accent-primary` background and `--color-text-on-accent` text, and inactive buttons with `--color-input-fill` background and `--color-text-primary` text.

---

### Requirement 9: Ask WATT-IF Page

**User Story:** As a user, I want a dedicated Ask WATT-IF page, so that I can ask natural-language questions about my energy data in a focused interface.

#### Acceptance Criteria

1. WHEN the user navigates to `/ask`, THE Ask_Page SHALL render the ChatPanel component occupying 100% of the viewport height below the TopBar.
2. THE ChatPanel SHALL style user message bubbles with `--color-accent-primary` background and `--color-text-on-accent` text colour.
3. THE ChatPanel SHALL style assistant message bubbles with `--color-card-bg` background, `1px solid var(--color-border)` border, and `--color-text-primary` text colour.
4. THE ChatPanel SHALL style error message bubbles with a light red background and a red text colour using the `--color-red` token defined in the Design_Token_System.
5. THE ChatPanel input field SHALL use `--color-input-fill` as its background and `--color-border` as its border colour.
6. WHILE the submit button is enabled, THE ChatPanel submit button SHALL use `--color-accent-primary` background with `--color-text-on-accent` text.
7. IF the submit button is disabled (loading or empty input), THE ChatPanel submit button SHALL use `--color-text-muted` background with `cursor: not-allowed`.

---

### Requirement 10: Data Entry Page

**User Story:** As a user, I want a Data Entry page, so that I can manually input new readings and upload CSV data in one place.

#### Acceptance Criteria

1. THE DataEntry_Page SHALL render a "New Reading" form containing: a required Date field (type `date`), a required Time field (type `time`), a required kWh field (type `number`, min 0, max 999999), and an optional Label field (type `text`, maxLength 100), plus a Submit button.
2. WHEN the user submits the New Reading form with Date, Time, and kWh all completed, THE DataEntry_Page SHALL append a new row to the SessionLog table with Source set to "Manual" and reset all four form fields to their empty default state (no pre-filled values, no retained input).
3. WHEN the user submits the New Reading form with one or more of the required fields (Date, Time, kWh) empty, THE DataEntry_Page SHALL display an inline validation message adjacent to each empty required field and SHALL NOT append any entry to the SessionLog; the validation messages SHALL remain visible until the corresponding field is corrected.
4. THE DataEntry_Page SHALL render the UploadPanel component inside a card below the New Reading form.
5. THE DataEntry_Page SHALL render the SessionLog table below the UploadPanel, with columns: Date, Time, kWh, Label, and Source.
6. WHEN no entries exist in the SessionLog, THE DataEntry_Page SHALL render the empty-state message "No entries recorded yet this session." inside the SessionLog card.
7. THE SessionLog table SHALL use `--font-mono` for Date, Time, and kWh cell values.
8. Form input fields on the DataEntry_Page SHALL use `--color-input-fill` as background, `--color-border` as border, and `--font-sans` as font.
9. WHEN the UploadPanel fires its `onUploadSuccess` callback, THE DataEntry_Page SHALL append a new row to the SessionLog table with Date and Time set to the current local timestamp, kWh set to "—", Label set to the uploaded filename, and Source set to "CSV Upload".

---

### Requirement 11: Recommendations Page

**User Story:** As a user, I want a Recommendations page, so that future energy-saving recommendations will have a dedicated location in the navigation.

#### Acceptance Criteria

1. THE Recommendations_Page SHALL render a card containing a heading element with the text "Recommendations" and a separate body text element with the text "Personalised energy-saving recommendations will appear here once the feature is available."
2. THE Recommendations_Page card SHALL be styled using the Design_Token_System card tokens: `--color-card-bg` background, `1px solid var(--color-border)` border, `--radius-card` border-radius, and `--shadow-card` box-shadow.
3. WHEN the user clicks the "Recommendations" navigation item in the Sidebar, THE Router SHALL navigate to `/recommendations` and THE Recommendations_Page SHALL be rendered in the main content area.

---

### Requirement 12: Component Restyling — General Card Layout

**User Story:** As a user, I want all UI sections to appear as clean white cards, so that content areas are visually distinct from the page background.

#### Acceptance Criteria

1. THE App SHALL apply `--color-card-bg` background, `1px solid var(--color-border)` border, `--radius-card` border-radius, and `--shadow-card` box-shadow to the outermost rendered element of each of the following sections: each individual chart panel `<div>` inside ForecastChart, the ChatPanel outer `<section>` element, the UploadPanel `<section>` element, each panel inside ModelEvaluation, the New Reading form card on DataEntry_Page, and the SessionLog card on DataEntry_Page.
2. THE App SHALL use `--color-page-bg` as the background colour of the main content area outside of cards.
3. THE App SHALL apply `--font-sans` as the base font-family on the `body` element.

---

### Requirement 13: Component Restyling — Buttons

**User Story:** As a developer, I want a consistent button style system, so that all interactive buttons follow the design specification without per-component custom styles.

#### Acceptance Criteria

1. THE App SHALL define a primary button style using `--color-accent-primary` background, `--color-text-on-accent` text colour, `--radius-card` border-radius, and `--font-sans` font.
2. THE App SHALL define an outlined secondary button style using a transparent background, `1px solid var(--color-accent-primary)` border, `--color-accent-primary` text colour, and the same border-radius and font.
3. WHEN a primary button receives pointer hover, THE App SHALL apply `--color-accent-hover` as the background colour.
4. WHEN a primary button receives keyboard focus, THE App SHALL display a visible focus-visible outline using `--color-accent-hover` or a high-contrast outline token, meeting WCAG 2.4.7.
5. IF a button is in a disabled state, THE App SHALL apply `--color-text-muted` as the background (primary) or border/text colour (outlined) and set `cursor: not-allowed`.
6. THE HorizonSelector, UploadPanel upload trigger, ChatPanel submit, and DataEntry_Page submit button SHALL all use the primary button style defined in Acceptance Criterion 1.

---

### Requirement 14: Component Restyling — HealthIndicator

**User Story:** As a user, I want the health status to be displayed in the Sidebar rather than in the header, so that system status is accessible without cluttering the page top bar.

#### Acceptance Criteria

1. THE HealthIndicator SHALL be rendered inside the Sidebar panel below the navigation links and SHALL NOT appear in the page header or TopBar.
2. WHEN all subsystems report `operational`, THE HealthIndicator SHALL display a single status dot and the text "All systems operational" using `--color-teal`.
3. WHEN one or more subsystems report `degraded`, THE HealthIndicator SHALL display one status dot per subsystem alongside a label for that subsystem, with dots for degraded subsystems coloured using `--color-amber` and dots for operational subsystems coloured using `--color-teal`.
4. IF the backend is unreachable, THE HealthIndicator SHALL display the text "Backend offline" using `--color-red`.
5. WHILE the initial health check request is in flight, THE HealthIndicator SHALL display a connecting/loading state (e.g. spinner or "Connecting…" text) rather than a blank area or an incorrect operational status.

---

### Requirement 15: Component Restyling — OfflineBanner

**User Story:** As a user, I want the offline banner to match the new design system, so that the warning is visually consistent with the rest of the UI.

#### Acceptance Criteria

1. IF the browser is offline, THE OfflineBanner SHALL render as a full-width element using `--color-accent-primary` as its background colour and `--color-sidebar-bg` (#0d1b2a) as its text colour.
2. WHILE the OfflineBanner is visible, THE OfflineBanner SHALL be positioned with `position: sticky; top: 0; z-index: 1000` so it overlays the Sidebar and TopBar without displacing them.
3. WHEN the browser comes back online, THE OfflineBanner SHALL be removed from the DOM so it is no longer visible.

---

### Requirement 16: Component Restyling — ModelEvaluation

**User Story:** As a user, I want the Model Evaluation metrics to use the new design tokens, so that the MAPE display is visually consistent with the rest of the application.

#### Acceptance Criteria

1. THE ModelEvaluation component SHALL use `--font-mono` for all numeric metric values displayed in the component, including MAPE percentages, ARIMA order tuples, and the MAPE sub-value inside the rating badge.
2. THE ModelEvaluation component SHALL use Design_Token_System variables for all background, border, and text colours across all rendered states (loading, error, empty, populated), replacing hardcoded hex values with `--color-card-bg`, `--color-border`, `--color-text-primary`, `--color-text-muted`, and `--color-page-bg` respectively.
3. THE ModelEvaluation rating badge SHALL use the Design_Token_System rating-level tokens for its background, border, and text colours: `--color-rating-excellent-bg/border/text`, `--color-rating-good-bg/border/text`, `--color-rating-fair-bg/border/text`, and `--color-rating-poor-bg/border/text`, each of which SHALL be declared in the Design_Token_System.

---

### Requirement 17: Responsive Layout — Mobile

**User Story:** As a mobile user, I want the application to be usable on a small screen, so that I can check my energy data on my phone.

#### Acceptance Criteria

1. WHILE the viewport width is narrower than 768 px, THE Dashboard_Page StatCard grid SHALL render in a two-column layout.
2. WHILE the viewport width is narrower than 480 px, THE Dashboard_Page StatCard grid SHALL render in a single-column layout.
3. WHILE the viewport width is narrower than 768 px, THE App main content area SHALL occupy 100% of the viewport width so no horizontal scrollbar appears on the page.
4. WHILE the viewport width is narrower than 768 px, each ForecastChart ResponsiveContainer SHALL maintain a minimum height of 240 px.
5. WHILE the viewport width is narrower than 768 px, each ForecastChart ResponsiveContainer SHALL not exceed the viewport width (no horizontal overflow).
6. THE App SHALL serve its content with a viewport meta tag that sets `width=device-width` and `initial-scale=1` so mobile browsers render at the device's native CSS pixel resolution without forced zoom.

---

### Requirement 18: Accessibility

**User Story:** As a user relying on assistive technology, I want the redesigned UI to be navigable by keyboard and screen reader, so that I can use the application without a pointer device.

#### Acceptance Criteria

1. THE Sidebar navigation items SHALL be rendered as `<a>` or `<button>` elements whose accessible name exactly matches the visible label text, and SHALL be reachable and operable by keyboard using Tab (to focus) and Enter or Space (to activate).
2. WHEN the Sidebar drawer is opened on a mobile viewport, THE App SHALL move keyboard focus to the first navigation item within the drawer.
3. WHILE the Sidebar drawer is open on a mobile viewport, THE App SHALL confine keyboard Tab and Shift+Tab navigation to elements within the drawer so focus cannot reach elements behind the overlay.
4. THE DarkModeToggle, notifications icon button, and user avatar icon button SHALL each have a non-empty `aria-label` attribute that describes the button's purpose.
5. WHEN the Sidebar drawer is closed on a mobile viewport, THE App SHALL return keyboard focus to the hamburger menu button that triggered the open action.
6. THE StatCard components SHALL use `<dl>/<dt>/<dd>` markup or ARIA `role="term"` / `role="definition"` with `aria-labelledby` so screen readers announce label and value pairs as associated terms and definitions.
7. THE App SHALL achieve a minimum colour contrast ratio of 4.5:1 between normal text (below 18 pt / 14 pt bold) and its background, and a minimum of 3:1 for large text (18 pt or above / 14 pt bold or above), as measured against the WCAG 2.1 AA standard.
