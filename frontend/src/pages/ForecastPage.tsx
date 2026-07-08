import React, { useEffect } from 'react'
import { useForecast } from '../context/ForecastContext'
import { HorizonSelector } from '../components/HorizonSelector'
import { ForecastChart } from '../components/ForecastChart'
import type { Horizon } from '../api/types'

export default function ForecastPage() {
  const { months, horizon, loading, error, warnings, loadForecast, setHorizon } = useForecast()

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
      {!loading && !error && warnings.length > 0 && (
        <div
          role="alert"
          style={{
            padding: '0.75rem 1rem',
            background: 'var(--color-rating-fair-bg)',
            border: '1px solid var(--color-rating-fair-border)',
            borderRadius: '0.5rem',
            fontFamily: 'var(--font-sans)',
            fontSize: '0.82rem',
            color: 'var(--color-rating-fair-text)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.3rem',
          }}
        >
          <strong style={{ fontSize: '0.85rem' }}>⚠️ Budget Alerts</strong>
          {warnings.map((w, i) => <span key={i}>• {w}</span>)}
        </div>
      )}
      {!loading && !error && months.length > 0 && <ForecastChart months={months} />}
    </div>
  )
}
