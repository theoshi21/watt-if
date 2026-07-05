/**
 * AppShell.test.tsx
 *
 * Tests for the AppShell layout component and App routing.
 *
 * Requirements: 3.3, 3.4, 4.1, 4.2, 4.4
 */
import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '../context/ThemeContext'

// ── Mock child components to isolate AppShell / routing ──────────────────────

vi.mock('../components/Sidebar', () => ({
  default: () => <nav data-testid="sidebar">Sidebar</nav>,
}))

vi.mock('../components/TopBar', () => ({
  default: ({ onMenuClick }: { onMenuClick: () => void }) => (
    <header data-testid="topbar">
      <button onClick={onMenuClick} aria-label="Open navigation menu">
        Menu
      </button>
    </header>
  ),
}))

vi.mock('../components/OfflineBanner', () => ({
  OfflineBanner: () => <div data-testid="offline-banner" />,
}))

// ── Mock page components ──────────────────────────────────────────────────────

vi.mock('../pages/DashboardPage', () => ({
  default: () => <div>Dashboard</div>,
}))
vi.mock('../pages/ForecastPage', () => ({
  default: () => <div>Forecast</div>,
}))
vi.mock('../pages/AskPage', () => ({
  default: () => <div>Ask</div>,
}))
vi.mock('../pages/DataEntryPage', () => ({
  default: () => <div>Data Entry</div>,
}))
vi.mock('../pages/RecommendationsPage', () => ({
  default: () => <div>Recommendations</div>,
}))

// ── Mock ForecastContext so provider doesn't make API calls ──────────────────

vi.mock('../context/ForecastContext', () => ({
  ForecastProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useForecast: () => ({
    months: [],
    loading: false,
    error: null,
    loadForecast: vi.fn(),
    setHorizon: vi.fn(),
    setMonths: vi.fn(),
    horizon: 3,
  }),
}))

// Lazy-import App after mocks are registered
const { App } = await import('../App')

// ── Render helper ─────────────────────────────────────────────────────────────

function renderAt(path: string) {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </ThemeProvider>,
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('AppShell routing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // Requirement 3.3 — route `/` renders Dashboard
  it('renders Dashboard page at root path', () => {
    renderAt('/')
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  // Requirement 3.3 — route `/forecast` renders Forecast
  it('renders Forecast page at /forecast', () => {
    renderAt('/forecast')
    expect(screen.getByText('Forecast')).toBeInTheDocument()
  })

  // Requirement 3.3 — route `/ask` renders Ask
  it('renders Ask page at /ask', () => {
    renderAt('/ask')
    expect(screen.getByText('Ask')).toBeInTheDocument()
  })

  // Requirement 3.3 — route `/data-entry` renders Data Entry
  it('renders Data Entry page at /data-entry', () => {
    renderAt('/data-entry')
    expect(screen.getByText('Data Entry')).toBeInTheDocument()
  })

  // Requirement 3.3 — route `/recommendations` renders Recommendations
  it('renders Recommendations page at /recommendations', () => {
    renderAt('/recommendations')
    expect(screen.getByText('Recommendations')).toBeInTheDocument()
  })

  // Requirement 3.4 — unknown paths redirect to `/` (Dashboard)
  it('redirects unknown paths to / and renders Dashboard', () => {
    renderAt('/this-does-not-exist')
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  // Requirement 4.1 — app-shell element present in DOM
  it('renders the app-shell container element', () => {
    renderAt('/')
    // AppShell wraps content in a div with class "app-shell"
    const shell = document.querySelector('.app-shell')
    expect(shell).not.toBeNull()
  })
})

describe('AppShell layout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // Requirement 4.2 — OfflineBanner renders above the shell
  it('renders OfflineBanner in the document', () => {
    renderAt('/')
    expect(screen.getByTestId('offline-banner')).toBeInTheDocument()
  })

  // Requirement 4.4 — hamburger button visible (present in DOM)
  it('renders hamburger button with accessible label', () => {
    renderAt('/')
    const hamburger = screen.getByRole('button', { name: /open navigation menu/i })
    expect(hamburger).toBeInTheDocument()
  })

  // Requirement 4.4 — hamburger button is visible on all routes (spot-check)
  it('hamburger button is present on /forecast', () => {
    renderAt('/forecast')
    expect(screen.getByRole('button', { name: /open navigation menu/i })).toBeInTheDocument()
  })

  // Sidebar is rendered as part of AppShell
  it('renders sidebar', () => {
    renderAt('/')
    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
  })
})
