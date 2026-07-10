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
          className="card"
          style={{
            borderLeft: '4px solid var(--color-red)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.75rem',
          }}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--color-red)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            style={{ flexShrink: 0, marginTop: '0.1rem' }}
          >
            <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontFamily: 'var(--font-sans)', fontSize: '0.82rem' }}>
            <strong style={{ fontSize: '0.85rem', color: 'var(--color-red)' }}>Budget Alerts</strong>
            {warnings.map((w, i) => <p key={i} style={{ margin: 0, color: 'var(--color-text-primary)' }}>• {w}</p>)}
          </div>
        </div>
      )}
      {!loading && !error && months.length > 0 && <ForecastChart months={months} />}
      {!loading && !error && months.length === 0 && (
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
          No forecast available. Select a horizon above and click to generate a new forecast.
        </p>
      )}
    </div>
  )
}
