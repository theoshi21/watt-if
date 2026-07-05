import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { getForecast, getTrainingStatus } from '../api/client'
import type { ForecastMonth, Horizon } from '../api/types'

interface ForecastContextValue {
  months: ForecastMonth[]
  horizon: Horizon
  loading: boolean
  error: string | null
  setHorizon: (h: Horizon) => void
  loadForecast: (h: Horizon) => Promise<void>
  setMonths: (m: ForecastMonth[]) => void
}

const ForecastContext = createContext<ForecastContextValue | null>(null)

export const ForecastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [horizon, setHorizon] = useState<Horizon>(3)
  const [months, setMonths] = useState<ForecastMonth[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadForecast = useCallback(async (h: Horizon) => {
    setLoading(true)
    setError(null)
    try {
      const res = await getForecast(h)
      setMonths(res.months)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load forecast.'
      if (msg.includes('503') || msg.includes('artefact')) {
        setError('No trained model found — upload a CSV to train the model first.')
      } else {
        setError(msg)
      }
      setMonths([])
    } finally {
      setLoading(false)
    }
  }, [])

  // On mount: auto-load 3-month forecast only if no forecast is cached yet.
  // We check /status first — if training is running we skip to avoid
  // generating a stale forecast. We do NOT re-run on every mount so that
  // a 12-month forecast the user generated on the Forecast page stays as
  // the active RAG context.
  useEffect(() => {
    const checkAndLoad = async () => {
      // Skip if we already have months in state (navigating back to Dashboard)
      if (months.length > 0) return
      try {
        const s = await getTrainingStatus()
        if (s.status !== 'running') {
          await loadForecast(3)
        }
      } catch {
        // Backend not reachable yet — silently skip
      }
    }
    void checkAndLoad()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // intentionally run once on mount only

  const value: ForecastContextValue = {
    months,
    horizon,
    loading,
    error,
    setHorizon,
    loadForecast,
    setMonths,
  }

  return <ForecastContext.Provider value={value}>{children}</ForecastContext.Provider>
}

export function useForecast(): ForecastContextValue {
  const ctx = useContext(ForecastContext)
  if (!ctx) {
    throw new Error('useForecast must be used within a ForecastProvider')
  }
  return ctx
}
