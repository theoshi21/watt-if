import React, { useCallback, useEffect, useRef, useState } from 'react'
import { getModelInfo, getTrainingStatus, triggerRetrain } from '../api/client'
import type { ModelInfoResponse } from '../api/types'
import { useForecast } from '../context/ForecastContext'

type TrainStatus = 'idle' | 'running' | 'done' | 'failed'

function fmtDate(iso: string | null): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function fmtMonth(ym: string | null): string {
  if (!ym) return '—'
  try {
    const [y, m] = ym.split('-')
    return new Date(Number(y), Number(m) - 1).toLocaleDateString('en-US', {
      month: 'long', year: 'numeric',
    })
  } catch {
    return ym
  }
}

const statusColor: Record<TrainStatus, string> = {
  idle:    'var(--color-text-muted)',
  running: 'var(--color-amber)',
  done:    'var(--color-teal)',
  failed:  'var(--color-red)',
}

const statusLabel: Record<TrainStatus, string> = {
  idle:    'Idle',
  running: '⚙ Training…',
  done:    '✓ Done',
  failed:  '✗ Failed',
}

export const TrainModelPanel: React.FC = () => {
  const [trainStatus, setTrainStatus] = useState<TrainStatus>('idle')
  const [errMsg, setErrMsg] = useState<string | null>(null)
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null)
  const [infoLoading, setInfoLoading] = useState(true)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const { clearMonths } = useForecast()

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
  }

  const fetchModelInfo = useCallback(() => {
    setInfoLoading(true)
    getModelInfo()
      .then(setModelInfo)
      .catch(() => setModelInfo(null))
      .finally(() => setInfoLoading(false))
  }, [])

  // On mount: sync with whatever the server says is already running
  useEffect(() => {
    fetchModelInfo()
    getTrainingStatus()
      .then(s => {
        if (s.status === 'running') {
          setTrainStatus('running')
          startPolling()
        }
      })
      .catch(() => {})
    return stopPolling
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const startPolling = () => {
    stopPolling()
    pollRef.current = setInterval(async () => {
      try {
        const s = await getTrainingStatus()
        if (s.status === 'done') {
          stopPolling()
          setTrainStatus('done')
          fetchModelInfo()
          // Clear stale forecast — user must generate a fresh one with the new model
          clearMonths()
        } else if (s.status === 'failed') {
          stopPolling()
          setTrainStatus('failed')
          setErrMsg(s.error ?? 'Training failed.')
        }
      } catch {
        // network hiccup — keep polling
      }
    }, 3000)
  }

  const handleTrain = async () => {
    setErrMsg(null)
    setTrainStatus('running')
    try {
      await triggerRetrain()
      startPolling()
    } catch (e) {
      setTrainStatus('failed')
      setErrMsg(e instanceof Error ? e.message : 'Failed to start training.')
    }
  }

  const isRunning = trainStatus === 'running'
  const hasModel = modelInfo?.trained_at != null

  return (
    <section className="card" aria-labelledby="train-model-hd">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 id="train-model-hd" style={{ margin: '0 0 0.2rem', fontSize: '1rem', fontWeight: 600 }}>
            Model Training
          </h2>
          <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
            Manually retrain the SARIMAX model on all data currently in the database.
          </p>
        </div>

        <button
          className="btn-primary"
          onClick={handleTrain}
          disabled={isRunning}
          style={{ whiteSpace: 'nowrap', flexShrink: 0 }}
        >
          {isRunning ? '⚙ Training…' : 'Train Model'}
        </button>
      </div>

      {/* Status row */}
      <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginTop: '1rem', fontSize: '0.82rem' }}>
        <span>
          <span style={{ color: 'var(--color-text-muted)' }}>Status: </span>
          <strong style={{ color: statusColor[trainStatus] }}>
            {statusLabel[trainStatus]}
          </strong>
          {trainStatus === 'running' && (
            <span style={{ color: 'var(--color-text-muted)', marginLeft: '0.4rem' }}>
              (this may take ~60 seconds)
            </span>
          )}
        </span>

        {errMsg && (
          <span role="alert" style={{ color: 'var(--color-red)' }}>{errMsg}</span>
        )}
      </div>

      {/* Current model info */}
      {!infoLoading && (
        <div style={{
          marginTop: '0.85rem',
          padding: '0.65rem 0.85rem',
          background: 'var(--color-page-bg)',
          border: '1px solid var(--color-border)',
          borderRadius: '0.5rem',
          display: 'flex', gap: '1.5rem', flexWrap: 'wrap', fontSize: '0.8rem',
        }}>
          {hasModel ? (
            <>
              <span>
                <span style={{ color: 'var(--color-text-muted)' }}>Last trained: </span>
                <strong style={{ fontFamily: 'var(--font-mono)' }}>{fmtDate(modelInfo!.trained_at)}</strong>
              </span>
              <span>
                <span style={{ color: 'var(--color-text-muted)' }}>Training window: </span>
                <strong style={{ fontFamily: 'var(--font-mono)' }}>
                  {fmtMonth(modelInfo!.training_window_start)} – {fmtMonth(modelInfo!.training_window_end)}
                </strong>
              </span>
              {modelInfo!.mape_avg_pct !== null && (
                <span>
                  <span style={{ color: 'var(--color-text-muted)' }}>Avg MAPE: </span>
                  <strong style={{ fontFamily: 'var(--font-mono)' }}>{modelInfo!.mape_avg_pct!.toFixed(1)}%</strong>
                  {' '}
                  <span className={`rating-badge rating-badge--${(modelInfo!.rating ?? 'fair').toLowerCase()}`}
                        style={{ padding: '0.1rem 0.4rem', fontSize: '0.72rem' }}>
                    {modelInfo!.rating}
                  </span>
                </span>
              )}
            </>
          ) : (
            <span style={{ color: 'var(--color-text-muted)' }}>
              No trained model found — click <strong>Train Model</strong> after adding data.
            </span>
          )}
        </div>
      )}
    </section>
  )
}
