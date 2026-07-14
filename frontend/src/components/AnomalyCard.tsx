interface AnomalyCardProps {
  month: string
  percentAbove: number
}

export default function AnomalyCard({ month, percentAbove }: AnomalyCardProps) {
  return (
    <div
      className="card"
      role="alert"
      style={{
        borderLeft: '4px solid var(--color-red)',
        background: 'var(--color-rating-poor-bg)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
      }}
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="var(--color-red)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        style={{ flexShrink: 0 }}
      >
        <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
      <p style={{ margin: 0, fontFamily: 'var(--font-sans)', color: 'var(--color-rating-poor-text)' }}>
        <strong>Anomaly Detected:</strong> forecast consumption for{' '}
        <strong>{month}</strong> is <strong>{percentAbove.toFixed(1)}%</strong>{' '}
        above your average.
      </p>
    </div>
  )
}
