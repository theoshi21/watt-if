import { useEffect, useState } from 'react'
import { getModelInfo } from '../api/client'
import type { ModelInfoResponse } from '../api/types'
import { useAuth } from '../context/AuthContext'

/**
 * ModelStatusPill
 *
 * Polls /model-info on mount and every 60 seconds.
 * - If mape_avg_pct is non-null: green "MODEL ACTIVE · MAPE X.X%" pill
 * - Otherwise: muted "MODEL NOT TRAINED" label
 *
 * Requirements: 5.5, 5.6, 5.7
 */
export default function ModelStatusPill() {
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const { token } = useAuth()

  useEffect(() => {
    if (!token) return

    const fetchInfo = async () => {
      try {
        const info = await getModelInfo()
        setModelInfo(info)
      } catch {
        setModelInfo(null)
      } finally {
        setLoading(false)
      }
    }

    fetchInfo()
    const interval = setInterval(fetchInfo, 60_000)
    return () => clearInterval(interval)
  }, [token])

  if (!loading && modelInfo?.mape_avg_pct != null) {
    return (
      <span
        style={{
          color: 'var(--color-teal)',
          fontSize: '0.75rem',
        }}
      >
        MODEL ACTIVE ·{' '}
        <span style={{ fontFamily: 'var(--font-mono)' }}>
          MAPE {modelInfo.mape_avg_pct.toFixed(1)}%
        </span>
      </span>
    )
  }

  return (
    <span
      style={{
        color: 'var(--color-text-muted)',
        fontSize: '0.75rem',
      }}
    >
      MODEL NOT TRAINED
    </span>
  )
}
