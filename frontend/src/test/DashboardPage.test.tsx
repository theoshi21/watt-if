import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import type { ForecastMonth } from '../api/types'

vi.mock('../context/ForecastContext', () => ({
  useForecast: vi.fn(),
}))

import { useForecast } from '../context/ForecastContext'
const mockUseForecast = useForecast as ReturnType<typeof vi.fn>

// Lazy import after mock is set up
const { default: DashboardPage } = await import('../pages/DashboardPage')

// ── Helpers ──────────────────────────────────────────────────────────────────

function makeMonth(kwh: number, yearMonth = '2025-01', avgTemp = 22.5, avgHumidity = 65.0): ForecastMonth {
  return {
    year_month: yearMonth,
    kwh_forecast: kwh,
    kwh_lower_95: kwh - 10,
    kwh_upper_95: kwh + 10,
    price_forecast: kwh * 0.25,
    price_lower_95: (kwh - 10) * 0.25,
    price_upper_95: (kwh + 10) * 0.25,
    avg_temperature: avgTemp,
    avg_humidity: avgHumidity,
  }
}

const baseContext = {
  horizon: 3 as const,
  error: null,
  setHorizon: vi.fn(),
  loadForecast: vi.fn(),
  setMonths: vi.fn(),
}

function renderPage() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // Requirement 7.1 — loading state
  it('renders 4 placeholder skeleton cards when loading is true', () => {
    mockUseForecast.mockReturnValue({ ...baseContext, months: [], loading: true })

    renderPage()

    // The skeleton renders 4 aria-hidden placeholder cards
    const skeletons = document.querySelectorAll('[aria-hidden="true"]')
    // At least 4 placeholder cards (the 4 stat cards + 1 chart placeholder)
    expect(skeletons.length).toBeGreaterThanOrEqual(4)
    // Should NOT show stat cards or empty-state text
    expect(screen.queryByText(/no forecast data yet/i)).not.toBeInTheDocument()
  })

  // Requirement 7.2 — empty state
  it('renders empty-state message when months is empty and not loading', () => {
    mockUseForecast.mockReturnValue({ ...baseContext, months: [], loading: false })

    renderPage()

    expect(screen.getByText(/no forecast data yet/i)).toBeInTheDocument()
    expect(screen.getByText(/data entry/i)).toBeInTheDocument()
  })

  // Requirement 7.3 — stat cards
  it('renders exactly 4 StatCards when forecast data is present', () => {
    mockUseForecast.mockReturnValue({
      ...baseContext,
      months: [makeMonth(300, '2025-01'), makeMonth(280, '2025-02'), makeMonth(260, '2025-03')],
      loading: false,
    })

    renderPage()

    // Each StatCard renders a <dt> with the label — check all four labels
    expect(screen.getByText('This Month')).toBeInTheDocument()
    expect(screen.getByText('Daily Average')).toBeInTheDocument()
    expect(screen.getByText('Avg Temp')).toBeInTheDocument()
    expect(screen.getByText('Avg Humidity')).toBeInTheDocument()
  })

  // Requirement 7.4 — anomaly card present
  it('renders AnomalyCard when the first month is >110% of the mean', () => {
    // first month at 500, others at 100 → mean = (500+100+100)/3 ≈ 233
    // 500 > 1.1 * 233 ≈ 256 → anomaly triggered
    mockUseForecast.mockReturnValue({
      ...baseContext,
      months: [makeMonth(500, '2025-01'), makeMonth(100, '2025-02'), makeMonth(100, '2025-03')],
      loading: false,
    })

    renderPage()

    expect(screen.getByText(/anomaly detected/i)).toBeInTheDocument()
  })

  // Requirement 7.4 — anomaly card absent
  it('does NOT render AnomalyCard when all months are uniform', () => {
    mockUseForecast.mockReturnValue({
      ...baseContext,
      months: [makeMonth(300, '2025-01'), makeMonth(300, '2025-02'), makeMonth(300, '2025-03')],
      loading: false,
    })

    renderPage()

    expect(screen.queryByText(/anomaly detected/i)).not.toBeInTheDocument()
  })

  // Requirement 7.5 — consumption history section
  it('renders "Consumption History" section when data is present', () => {
    mockUseForecast.mockReturnValue({
      ...baseContext,
      months: [makeMonth(300, '2025-01'), makeMonth(280, '2025-02')],
      loading: false,
    })

    renderPage()

    expect(screen.getByText('Consumption History')).toBeInTheDocument()
  })
})
