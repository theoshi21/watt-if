import React, { useEffect, useRef, useState } from 'react'

interface HealthData {
  status: 'ok' | 'degraded'
  subsystems: Record<string, 'operational' | 'degraded'>
}

type ConnectionState = 'connecting' | 'connected' | 'unreachable'

const BASE_URL: string = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const LABELS: Record<string, string> = {
  data_pipeline: 'Data Pipeline',
  sarimax_model: 'SARIMAX Model',
  vector_store:  'Vector Store',
  llm_service:   'LLM (Ollama)',
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
        background: status === 'operational'
          ? 'var(--color-teal)'
          : 'var(--color-amber)',
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
    // Poll more frequently (10s) when unreachable, normal interval (30s) when connected
    const interval = setInterval(() => {
      if (connState === 'unreachable' || connState === 'connecting') {
        void check()
      } else {
        void check()
      }
    }, connState === 'unreachable' ? 10_000 : 30_000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [connState])

  /* ── Connecting ─────────────────────────────────────────────────────────── */
  if (connState === 'connecting') {
    return (
      <aside aria-label="System health" style={outerStyle}>
        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
          Connecting…
        </span>
      </aside>
    )
  }

  /* ── Unreachable ─────────────────────────────────────────────────────────── */
  if (connState === 'unreachable') {
    return (
      <aside aria-label="System health" style={outerStyle}>
        <span
          style={{
            fontSize: '0.8rem',
            color: 'var(--color-red)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.3rem',
          }}
        >
          <span
            style={{
              width: 9, height: 9,
              borderRadius: '50%',
              background: 'var(--color-red)',
              display: 'inline-block',
              flexShrink: 0,
            }}
          />
          Backend offline
        </span>
      </aside>
    )
  }

  /* ── Connected ───────────────────────────────────────────────────────────── */
  const subsystems = health?.subsystems ?? {}
  const entries = Object.entries(subsystems)
  const allOperational = entries.length > 0 && entries.every(([, st]) => st === 'operational')

  if (allOperational) {
    return (
      <aside aria-label="System health" style={outerStyle}>
        <span
          style={{
            display: 'flex',
            alignItems: 'center',
            fontSize: '0.8rem',
            color: 'var(--color-teal)',
          }}
        >
          <span
            style={{
              width: 9, height: 9,
              borderRadius: '50%',
              background: 'var(--color-teal)',
              marginRight: '0.3rem',
              flexShrink: 0,
            }}
          />
          All systems operational
        </span>
      </aside>
    )
  }

  /* ── Degraded: one dot per subsystem ─────────────────────────────────────── */
  return (
    <aside aria-label="System health" style={outerStyle}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
        {entries.map(([key, st]) => (
          <span
            key={key}
            style={{
              display: 'flex',
              alignItems: 'center',
              fontSize: '0.78rem',
              color: 'var(--color-text-secondary)',
            }}
          >
            <Dot status={st} />
            {LABELS[key] ?? key}
          </span>
        ))}
      </div>
    </aside>
  )
}

const outerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
}
