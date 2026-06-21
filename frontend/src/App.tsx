import React, { useState, useCallback, useEffect } from 'react'
import { getForecast, getTrainingStatus } from './api/client'
import type { ForecastMonth, Horizon } from './api/types'
import { ChatPanel } from './components/ChatPanel'
import { ForecastChart } from './components/ForecastChart'
import { HealthIndicator } from './components/HealthIndicator'
import { HorizonSelector } from './components/HorizonSelector'
import { ModelEvaluation } from './components/ModelEvaluation'
import { OfflineBanner } from './components/OfflineBanner'
import { UploadPanel } from './components/UploadPanel'

export const App: React.FC = () => {
  const [horizon, setHorizon] = useState<Horizon>(3)
  const [months, setMonths] = useState<ForecastMonth[]>([])
  const [forecastLoading, setForecastLoading] = useState(false)
  const [forecastError, setForecastError] = useState<string | null>(null)
  const [modelReady, setModelReady] = useState(false)
  const [evalRefreshKey, setEvalRefreshKey] = useState(0)

  const loadForecast = useCallback(async (h: Horizon) => {
    setForecastLoading(true)
    setForecastError(null)
    try {
      const res = await getForecast(h)
      setMonths(res.months)
      setModelReady(true)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load forecast.'
      if (msg.includes('503') || msg.includes('artefact')) {
        setForecastError('No trained model found — upload a CSV to train the model first.')
      } else {
        setForecastError(msg)
      }
      setMonths([])
    } finally {
      setForecastLoading(false)
    }
  }, [])

  // On mount: check if a model is already trained and auto-load the forecast.
  // This prevents retraining on every refresh.
  useEffect(() => {
    const checkAndLoad = async () => {
      try {
        const s = await getTrainingStatus()
        // Only auto-load if not currently training
        if (s.status !== 'running') {
          await loadForecast(horizon)
        }
      } catch {
        // Backend not reachable yet — silently skip
      }
    }
    void checkAndLoad()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // intentionally run once on mount only

  const handleHorizonChange = (h: Horizon) => {
    setHorizon(h)
    void loadForecast(h)
  }

  const handleUploadSuccess = useCallback(() => {
    // Auto-load forecast and refresh evaluation after successful upload + training
    setEvalRefreshKey((k) => k + 1)
    void loadForecast(horizon)
  }, [horizon, loadForecast])

  return (
    <>
      <OfflineBanner />

      <div
        style={{
          maxWidth: '900px',
          margin: '0 auto',
          padding: '1rem',
          fontFamily: 'system-ui, sans-serif',
        }}
      >
        {/* Header */}
       <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1rem',
          borderBottom: '1px solid #eee',
          paddingBottom: '0.5rem',
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: '1.4rem',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <img
            src="wattif.png"
            alt="WATT-IF Logo"
            style={{
              width: '40px',
              height: '40px',
              objectFit: 'contain',
            }}
          />
          WATT-IF
        </h1>

  <HealthIndicator />
</header>

        {/* Chat — at the top for quick access */}
        <section style={{ marginBottom: '1.5rem' }}>
          <ChatPanel />
        </section>

        {/* Upload */}
        <section style={{ marginBottom: '1.5rem' }}>
          <UploadPanel onUploadSuccess={handleUploadSuccess} />
        </section>

        {/* Model Evaluation */}
        <section style={{ marginBottom: '1.5rem' }}>
          <ModelEvaluation refreshKey={evalRefreshKey} />
        </section>

        {/* Forecast */}
        <section style={{ marginBottom: '1.5rem' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              marginBottom: '0.75rem',
            }}
          >
            <h2 style={{ margin: 0 }}>Forecast</h2>
            <HorizonSelector
              selected={horizon}
              onChange={handleHorizonChange}
              disabled={forecastLoading}
            />
            {forecastLoading && (
              <span role="status" aria-label="Loading forecast" style={{ color: '#888' }}>
                Loading…
              </span>
            )}
          </div>

          {!modelReady && !forecastLoading && months.length === 0 && !forecastError && (
            <p style={{ color: '#888', fontSize: '0.9rem' }}>
              Upload a CSV above to train the model, then select a horizon to see your forecast.
            </p>
          )}

          {forecastError && (
            <p role="alert" style={{ color: '#c62828', fontSize: '0.9rem' }}>
              {forecastError}
            </p>
          )}

          <ForecastChart months={months} />
        </section>
      </div>
    </>
  )
}
