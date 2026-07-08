import React, { useEffect } from 'react'
import { useForecast } from '../context/ForecastContext'
import { HorizonSelector } from '../components/HorizonSelector'
import { ForecastChart } from '../components/ForecastChart'
import type { Horizon } from '../api/types'

export default function ForecastPage() {
  const { months, horizon, loading, error, loadForecast, setHorizon } = useForecast()

  useEffect(() => {
    if (months.length === 0) {
      loadForecast(3)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleHorizonChange = async (h: Horizon) => {
    setHorizon(h)
    await loadForecast(h)
  }

  const is503 =
    error?.includes('503') || error?.includes('No trained model')

  return (
    <div className="page-content" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <HorizonSelector selected={horizon} onChange={handleHorizonChange} disabled={loading} />
      {loading && <span role="status">Loading…</span>}
      {error && is503 && (
        <p role="alert">
          No trained model found — upload a CSV on the Data Entry page to train the model first.
        </p>
      )}
      {error && !is503 && <p role="alert">{error}</p>}
      {!loading && !error && months.length > 0 && <ForecastChart months={months} />}
    </div>
  )
}
