import React from 'react'
import type { Horizon } from '../api/types'

interface Props {
  selected: Horizon
  onChange: (h: Horizon) => void
  disabled?: boolean
}

const HORIZONS: Horizon[] = [1, 3, 6]
const LABELS: Record<Horizon, string> = { 1: '1m', 3: '3m', 6: '6m' }

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
            border: selected === h ? '2px solid #4f8ef7' : '2px solid #ccc',
            borderRadius: '4px',
            cursor: disabled ? 'not-allowed' : 'pointer',
            background: selected === h ? '#4f8ef7' : '#fff',
            color: selected === h ? '#fff' : '#333',
          }}
        >
          {LABELS[h]}
        </button>
      ))}
    </div>
  )
}
