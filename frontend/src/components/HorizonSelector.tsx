import React from 'react'
import type { Horizon } from '../api/types'

interface Props {
  selected: Horizon
  onChange: (h: Horizon) => void
  disabled?: boolean
}

const HORIZONS: Horizon[] = [1, 3, 6, 9, 12]
const LABELS: Record<Horizon, string> = { 1: '1 Mo', 3: '3 Mo', 6: '6 Mo', 9: '9 Mo', 12: '12 Mo' }

export const HorizonSelector: React.FC<Props> = ({ selected, onChange, disabled }) => {
  return (
    <div role="group" aria-label="Forecast horizon" style={{ display: 'flex', gap: '0.5rem' }}>
      {HORIZONS.map((h) => (
        <button
          key={h}
          aria-pressed={selected === h}
          disabled={disabled}
          onClick={() => onChange(h)}
          style={{
            padding: '0.4rem 1rem',
            fontWeight: selected === h ? 'bold' : 'normal',
            border: selected === h ? '2px solid var(--color-accent-primary)' : '2px solid var(--color-border)',
            borderRadius: 'var(--radius-card)',
            cursor: disabled ? 'not-allowed' : 'pointer',
            background: selected === h ? 'var(--color-accent-primary)' : 'var(--color-input-fill)',
            color: selected === h ? 'var(--color-text-on-accent)' : 'var(--color-text-primary)',
            fontFamily: 'var(--font-sans)',
            transition: 'background 0.15s ease, color 0.15s ease, border-color 0.15s ease',
          }}
        >
          {LABELS[h]}
        </button>
      ))}
    </div>
  )
}
