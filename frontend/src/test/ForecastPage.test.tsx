import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { useForecast } from '../context/ForecastContext'
import ForecastPage from '../pages/ForecastPage'

vi.mock('../context/ForecastContext', () => ({
  useForecast: vi.fn(),
}))

vi.mock('../components/ForecastChart', () => ({
  ForecastChart: () => <div data-testid="forecast-chart" />,
}))

const mockUseForecast = useForecast as ReturnType<typeof vi.fn>

function renderPage() {
  return render(
    <MemoryRouter>
      <ForecastPage />
    </MemoryRouter>,
  )
}

describe('ForecastPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls loadForecast(3) on mount when months is empty', () => {
    const loadForecast = vi.fn()
    mockUseForecast.mockReturnValue({
      months: [],
      loading: false,
      error: null,
      loadForecast,
      setHorizon: vi.fn(),
      horizon: 3,
      setMonths: vi.fn(),
    })

    renderPage()

    expect(loadForecast).toHaveBeenCalledOnce()
    expect(loadForecast).toHaveBeenCalledWith(3)
  })

  it('does NOT call loadForecast if months are already loaded', () => {
    const loadForecast = vi.fn()
    mockUseForecast.mockReturnValue({
      months: [
        {
          year_month: '2024-01',
          kwh_forecast: 100,
          kwh_lower_95: 90,
          kwh_upper_95: 110,
          price_forecast: 20,
          price_lower_95: 18,
          price_upper_95: 22,
        },
      ],
      loading: false,
      error: null,
      loadForecast,
      setHorizon: vi.fn(),
      horizon: 3,
      setMonths: vi.fn(),
    })

    renderPage()

    expect(loadForecast).not.toHaveBeenCalled()
  })

  it('renders loading indicator with role="status" while loading', () => {
    mockUseForecast.mockReturnValue({
      months: [],
      loading: true,
      error: null,
      loadForecast: vi.fn(),
      setHorizon: vi.fn(),
      horizon: 3,
      setMonths: vi.fn(),
    })

    renderPage()

    const indicator = screen.getByRole('status')
    expect(indicator).toBeInTheDocument()
    expect(indicator.tagName).toBe('SPAN')
  })

  it('renders 503 error alert with correct message when error contains "No trained model"', () => {
    mockUseForecast.mockReturnValue({
      months: [],
      loading: false,
      error: 'No trained model found — upload a CSV to train the model first.',
      loadForecast: vi.fn(),
      setHorizon: vi.fn(),
      horizon: 3,
      setMonths: vi.fn(),
    })

    renderPage()

    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert.textContent).toContain('No trained model found')
  })

  it('renders generic error message in role="alert" for non-503 errors', () => {
    mockUseForecast.mockReturnValue({
      months: [],
      loading: false,
      error: 'Network request failed',
      loadForecast: vi.fn(),
      setHorizon: vi.fn(),
      horizon: 3,
      setMonths: vi.fn(),
    })

    renderPage()

    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert.textContent).toBe('Network request failed')
  })

  it('renders HorizonSelector as disabled when loading is true', () => {
    mockUseForecast.mockReturnValue({
      months: [],
      loading: true,
      error: null,
      loadForecast: vi.fn(),
      setHorizon: vi.fn(),
      horizon: 3,
      setMonths: vi.fn(),
    })

    renderPage()

    screen.getAllByRole('button').forEach((btn) => {
      expect(btn).toBeDisabled()
    })
  })
})
