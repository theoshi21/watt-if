import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ForecastChart } from '../components/ForecastChart'
import type { ForecastMonth } from '../api/types'

const makeForecastMonth = (i: number): ForecastMonth => ({
  year_month: `2026-${String(i + 1).padStart(2, '0')}`,
  kwh_forecast: 300 + i,
  kwh_lower_95: 270 + i,
  kwh_upper_95: 330 + i,
  price_forecast: 85 + i,
  price_lower_95: 75 + i,
  price_upper_95: 95 + i,
  avg_temperature: 28.5,
  avg_humidity: 72.0,
})

describe('ForecastChart', () => {
  it('renders empty state when months is empty', () => {
    render(<ForecastChart months={[]} />)
    expect(screen.getByRole('status', { name: /no forecast data/i })).toBeInTheDocument()
  })

  it('renders the chart container when months are provided', () => {
    const months = [makeForecastMonth(0), makeForecastMonth(1), makeForecastMonth(2)]
    render(<ForecastChart months={months} />)
    expect(screen.getByLabelText('Forecast charts')).toBeInTheDocument()
  })

  it('shows kWh heading', () => {
    render(<ForecastChart months={[makeForecastMonth(0)]} />)
    expect(screen.getByText(/Electricity Consumption Forecast/i)).toBeInTheDocument()
  })

  it('shows Price heading', () => {
    render(<ForecastChart months={[makeForecastMonth(0)]} />)
    expect(screen.getByText(/Electricity Bill Forecast/i)).toBeInTheDocument()
  })
})
