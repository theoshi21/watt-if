interface AnomalyCardProps {
  month: string
  percentAbove: number
}

export default function AnomalyCard({ month, percentAbove }: AnomalyCardProps) {
  return (
    <div className="card" style={{ borderLeft: '4px solid var(--color-teal)' }}>
      <p style={{ margin: 0, color: 'var(--color-text-primary)' }}>
        ⚠️ Anomaly Detected: forecast consumption for <strong>{month}</strong> is{' '}
        <strong>{percentAbove.toFixed(1)}%</strong> above your average.
      </p>
    </div>
  )
}
