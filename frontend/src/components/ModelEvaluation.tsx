import React, { useEffect, useState } from 'react'
import { getModelInfo } from '../api/client'
import type { ModelInfoResponse } from '../api/types'

interface Props {
  /** Increment this to re-fetch after a new training run completes. */
  refreshKey?: number
}

const RATING_COLOR: Record<string, string> = {
  Excellent: '#2e7d32',
  Good:      '#1565c0',
  Fair:      '#e65100',
  Poor:      '#c62828',
}

const RATING_BG: Record<string, string> = {
  Excellent: '#e8f5e9',
  Good:      '#e3f2fd',
  Fair:      '#fff3e0',
  Poor:      '#ffebee',
}

function fmtMonth(ym: string | null): string {
  if (!ym) return '—'
  try {
    const [year, month] = ym.split('-')
    const date = new Date(Number(year), Number(month) - 1)
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  } catch {
    return ym
  }
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'long', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function MetricRow({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                  padding: '0.35rem 0', borderBottom: '1px solid #f0f0f0' }}>
      <span style={{ fontSize: '0.85rem', color: '#555', flexShrink: 0, marginRight: '1rem' }}>{label}</span>
      <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#111',
                     textAlign: 'right', whiteSpace: 'nowrap' }}>
        {value}
        {sub && <span style={{ fontWeight: 400, fontSize: '0.78rem', color: '#888', marginLeft: 4 }}>{sub}</span>}
      </span>
    </div>
  )
}

export const ModelEvaluation: React.FC<Props> = ({ refreshKey }) => {
  const [info, setInfo] = useState<ModelInfoResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    getModelInfo()
      .then(setInfo)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load model info.'))
      .finally(() => setLoading(false))
  }, [refreshKey])

  if (loading) {
    return (
      <section aria-label="Model Evaluation" aria-busy="true">
        <h2 style={{ margin: '0 0 0.5rem' }}>Model Evaluation</h2>
        <p style={{ color: '#888', fontSize: '0.9rem' }}>Loading…</p>
      </section>
    )
  }

  if (error) {
    return (
      <section aria-label="Model Evaluation">
        <h2 style={{ margin: '0 0 0.5rem' }}>Model Evaluation</h2>
        <p role="alert" style={{ color: '#c62828', fontSize: '0.9rem' }}>{error}</p>
      </section>
    )
  }

  if (!info || info.trained_at === null) {
    return (
      <section aria-label="Model Evaluation">
        <h2 style={{ margin: '0 0 0.5rem' }}>Model Evaluation</h2>
        <p style={{ color: '#888', fontSize: '0.9rem' }}>
          No trained model found. Upload a CSV to train the model.
        </p>
      </section>
    )
  }

  const rating = info.rating ?? 'Fair'
  const ratingColor = RATING_COLOR[rating] ?? '#555'
  const ratingBg = RATING_BG[rating] ?? '#fafafa'
  const orderStr = info.order ? `(${info.order.join(', ')})` : '—'
  const sOrderStr = info.seasonal_order ? `(${info.seasonal_order.join(', ')})` : '—'

  return (
    <section aria-label="Model Evaluation">
      <h2 style={{ margin: '0 0 0.75rem' }}>Model Evaluation</h2>

      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>

        {/* Accuracy rating badge */}
        <div style={{
          background: ratingBg,
          border: `1px solid ${ratingColor}`,
          borderRadius: 8,
          padding: '0.75rem 1.25rem',
          minWidth: 130,
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: 2 }}>Accuracy Rating</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: ratingColor }}>{rating}</div>
          {info.mape_avg_pct !== null && (
            <div style={{ fontSize: '0.8rem', color: '#888', marginTop: 2 }}>
              {info.mape_avg_pct.toFixed(1)}% avg MAPE
            </div>
          )}
        </div>

        {/* MAPE breakdown */}
        <div style={{
          flex: 1, minWidth: 200,
          background: '#fafafa', border: '1px solid #e8e8e8',
          borderRadius: 8, padding: '0.75rem 1rem',
        }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#888',
                        textTransform: 'uppercase', marginBottom: '0.5rem', letterSpacing: '0.04em' }}>
            Validation Error (MAPE)
          </div>
          {info.mape_kwh_pct !== null && (
            <MetricRow label="kWh Consumption" value={`${info.mape_kwh_pct.toFixed(1)}%`}
                       sub="lower is better" />
          )}
          {info.mape_price_pct !== null && (
            <MetricRow label="Bill Price" value={`${info.mape_price_pct.toFixed(1)}%`} />
          )}
          {info.mape_avg_pct !== null && (
            <MetricRow label="Average" value={`${info.mape_avg_pct.toFixed(1)}%`} />
          )}
        </div>

        {/* Model details */}
        <div style={{
          flex: 1, minWidth: 200,
          background: '#fafafa', border: '1px solid #e8e8e8',
          borderRadius: 8, padding: '0.75rem 1rem',
        }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#888',
                        textTransform: 'uppercase', marginBottom: '0.5rem', letterSpacing: '0.04em' }}>
            Model Details
          </div>
          <MetricRow label="ARIMA Order" value={orderStr} sub="(p,d,q)" />
          <MetricRow label="Seasonal Order" value={sOrderStr} sub="(P,D,Q,m)" />
          <MetricRow label="Training Window"
                     value={`${fmtMonth(info.training_window_start)} – ${fmtMonth(info.training_window_end)}`} />
          <MetricRow label="Trained At" value={fmtDate(info.trained_at)} />
        </div>
      </div>

      {/* MAPE explanation */}
      <p style={{ fontSize: '0.78rem', color: '#999', margin: 0 }}>
        MAPE (Mean Absolute Percentage Error) measures average forecast error on the validation set.
        Under 10% is good for electricity forecasting; under 5% is excellent.
      </p>
    </section>
  )
}
