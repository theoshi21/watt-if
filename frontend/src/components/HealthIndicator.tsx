import React, { useEffect, useRef, useState } from 'react'

interface HealthData {
  status: 'ok' | 'degraded'
  subsystems: Record<string, 'operational' | 'degraded'>
  model_trained_at: string | null
  last_upload_at: string | null
}

type ConnectionState = 'connecting' | 'connected' | 'unreachable'

const BASE_URL = (import.meta as Record<string, unknown> & { env?: Record<string, string> })
  .env?.VITE_API_BASE ?? 'http://localhost:8000'

const LABELS: Record<string, string> = {
  data_pipeline: 'Data Pipeline',
  sarimax_model: 'SARIMAX Model',
  vector_store:  'Vector Store',
  llm_service:   'LLM (Ollama)',
}

/** Format an ISO timestamp to a human-friendly local string */
function fmtTime(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function Dot({ status }: { status: 'operational' | 'degraded' }) {
  return (
    <span
      aria-hidden="true"
      title={status}
      style={{
        display: 'inline-block',
        width: 9, height: 9,
        borderRadius: '50%',
        background: status === 'operational' ? '#43a047' : '#fb8c00',
        marginRight: '0.3rem',
        verticalAlign: 'middle',
        flexShrink: 0,
      }}
    />
  )
}

export const HealthIndicator: React.FC = () => {
  const [connState, setConnState] = useState<ConnectionState>('connecting')
  const [health, setHealth] = useState<HealthData | null>(null)
  // Only flip to 'unreachable' after the first attempt has had time to settle
  const firstCheckDone = useRef(false)

  useEffect(() => {
    let cancelled = false

    const check = async () => {
      try {
        const res = await fetch(`${BASE_URL}/health`, {
          signal: AbortSignal.timeout(6000),
        })
        const data: HealthData = await res.json()
        if (!cancelled) {
          setHealth(data)
          setConnState('connected')
          firstCheckDone.current = true
        }
      } catch {
        if (!cancelled) {
          firstCheckDone.current = true
          setConnState('unreachable')
        }
      }
    }

    void check()
    const interval = setInterval(check, 30_000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [])

  /* ── Connecting state: shown only briefly on first load ─────────────────── */
  if (connState === 'connecting') {
    return (
      <aside aria-label="System health" style={outerStyle}>
        <span style={{ color: '#888', fontSize: '0.8rem' }}>Connecting to backend…</span>
      </aside>
    )
  }

  /* ── Unreachable ─────────────────────────────────────────────────────────── */
  if (connState === 'unreachable') {
    return (
      <aside aria-label="System health" style={outerStyle}>
        <span
          style={{
            fontSize: '0.8rem', color: '#c62828',
            display: 'flex', alignItems: 'center', gap: '0.3rem',
          }}
        >
          <span style={{ width: 9, height: 9, borderRadius: '50%', background: '#e53935', display: 'inline-block', flexShrink: 0 }} />
          Backend not running — start uvicorn first
        </span>
      </aside>
    )
  }

  /* ── Connected ───────────────────────────────────────────────────────────── */
  return (
    <aside aria-label="System health" style={{ ...outerStyle, flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem' }}>
      {/* Subsystem dots */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem' }}>
        {health && Object.entries(health.subsystems).map(([key, st]) => (
          <span key={key} style={{ display: 'flex', alignItems: 'center', fontSize: '0.78rem', color: '#444' }}>
            <Dot status={st} />
            {LABELS[key] ?? key}
          </span>
        ))}
      </div>

      {/* Last upload / trained info */}
      {health && (
        <div style={{ fontSize: '0.72rem', color: '#888', textAlign: 'right', lineHeight: 1.5 }}>
          {health.last_upload_at && (
            <span>Last upload: <strong style={{ color: '#555' }}>{fmtTime(health.last_upload_at)}</strong></span>
          )}
          {health.last_upload_at && health.model_trained_at && <span> · </span>}
          {health.model_trained_at && (
            <span>Model trained: <strong style={{ color: '#555' }}>{fmtTime(health.model_trained_at)}</strong></span>
          )}
          {!health.last_upload_at && !health.model_trained_at && (
            <span>No data uploaded yet</span>
          )}
        </div>
      )}
    </aside>
  )
}

const outerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
}
