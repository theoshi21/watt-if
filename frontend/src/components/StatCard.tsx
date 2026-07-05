import React from 'react'

// Predefined accent palettes — each has a left-border color, a subtle bg tint,
// and an icon color. All values reference existing tokens where possible.
const ACCENTS = {
  blue: {
    border: 'var(--color-accent-primary)',
    bg: 'color-mix(in srgb, var(--color-accent-primary) 8%, var(--color-card-bg))',
    iconColor: 'var(--color-accent-primary)',
  },
  teal: {
    border: 'var(--color-teal)',
    bg: 'color-mix(in srgb, var(--color-teal) 8%, var(--color-card-bg))',
    iconColor: 'var(--color-teal)',
  },
  amber: {
    border: 'var(--color-amber)',
    bg: 'color-mix(in srgb, var(--color-amber) 8%, var(--color-card-bg))',
    iconColor: 'var(--color-amber)',
  },
  indigo: {
    border: '#6366f1',
    bg: 'color-mix(in srgb, #6366f1 8%, var(--color-card-bg))',
    iconColor: '#6366f1',
  },
} as const

type AccentKey = keyof typeof ACCENTS

interface StatCardProps {
  label: string
  value: string | number
  unit?: string
  accent?: AccentKey
  icon?: React.ReactNode
}

export default function StatCard({ label, value, unit, accent, icon }: StatCardProps) {
  const a = accent ? ACCENTS[accent] : null

  return (
    <div
      className="card"
      style={{
        ...(a && {
          borderLeft: `4px solid ${a.border}`,
          background: a.bg,
        }),
        display: 'flex',
        alignItems: 'center',
        gap: '0.85rem',
        padding: '1rem 1.25rem',
      }}
    >
      {/* Optional icon */}
      {icon && a && (
        <div style={{
          flexShrink: 0,
          width: 36,
          height: 36,
          borderRadius: '0.5rem',
          background: `color-mix(in srgb, ${a.border} 15%, var(--color-card-bg))`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: a.iconColor,
        }}>
          {icon}
        </div>
      )}

      <dl style={{ margin: 0 }}>
        <dt style={{
          fontFamily: 'var(--font-sans)',
          color: 'var(--color-text-muted)',
          fontSize: '0.78rem',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          marginBottom: '0.2rem',
        }}>
          {label}
        </dt>
        <dd style={{
          fontFamily: 'var(--font-mono)',
          color: 'var(--color-text-primary)',
          fontSize: '1.5rem',
          fontWeight: 700,
          margin: 0,
          lineHeight: 1.1,
        }}>
          {value}
          {unit && (
            <span style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.8rem',
              fontWeight: 500,
              color: 'var(--color-text-muted)',
              marginLeft: '0.3rem',
            }}>
              {unit}
            </span>
          )}
        </dd>
      </dl>
    </div>
  )
}
