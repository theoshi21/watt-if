import { useForecast } from '../context/ForecastContext'
import StatCard from '../components/StatCard'
import AnomalyCard from '../components/AnomalyCard'
import { ForecastChart } from '../components/ForecastChart'
import type { ForecastMonth } from '../api/types'

// ── Pure helper: format "YYYY-MM" → "MMM YYYY" (e.g. "Jan 2025") ──────────────
function formatYearMonth(ym: string): string {
  const [year, month] = ym.split('-')
  const date = new Date(parseInt(year, 10), parseInt(month, 10) - 1, 1)
  return date.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' })
}

// ── Anomaly detection (exported for testing) ──────────────────────────────────
export function detectAnomaly(
  months: ForecastMonth[],
): { monthLabel: string; percentAbove: number } | null {
  if (months.length < 2) return null
  const mean = months.reduce((s, m) => s + m.kwh_forecast, 0) / months.length
  const first = months[0].kwh_forecast
  if (first > mean * 1.1) {
    return {
      monthLabel: formatYearMonth(months[0].year_month),
      percentAbove: ((first - mean) / mean) * 100,
    }
  }
  return null
}

// ── Loading skeleton ──────────────────────────────────────────────────────────
function LoadingSkeleton() {
  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div className="stat-grid">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="card"
            style={{
              height: '90px',
              background: 'var(--color-border)',
              animation: 'pulse 1.5s ease-in-out infinite',
              opacity: 0.6,
            }}
            aria-hidden="true"
          />
        ))}
      </div>
      <div
        className="card"
        style={{
          height: '300px',
          background: 'var(--color-border)',
          animation: 'pulse 1.5s ease-in-out infinite',
          opacity: 0.6,
        }}
        aria-hidden="true"
      />
    </div>
  )
}

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyState() {
  return (
    <div style={{ padding: '1.5rem' }}>
      <div className="card" style={{ textAlign: 'center', padding: '2.5rem' }}>
        <p
          style={{
            color: 'var(--color-text-primary)',
            fontSize: '1rem',
            marginBottom: '0.5rem',
          }}
        >
          No forecast data yet.
        </p>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', margin: 0 }}>
          Head to <strong>Data Entry</strong> to upload a CSV or add a reading — once the model
          trains, your dashboard will populate automatically.
        </p>
      </div>
    </div>
  )
}

// ── Dashboard page ────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { months, loading, error } = useForecast()
  const anomaly = detectAnomaly(months)

  if (loading) return <LoadingSkeleton />

  if (months.length === 0 && !loading && !error) return <EmptyState />

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {anomaly && (
        <AnomalyCard month={anomaly.monthLabel} percentAbove={anomaly.percentAbove} />
      )}

      <div className="stat-grid">
        <StatCard
          label="This Month"
          value={months[0].kwh_forecast.toFixed(2)}
          unit="kWh"
          accent="blue"
          icon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
          }
        />
        <StatCard
          label="Daily Average"
          value={(months[0].kwh_forecast / 30).toFixed(2)}
          unit="kWh/day"
          accent="teal"
          icon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
          }
        />
        <StatCard
          label="Avg Temp"
          value={months.length > 0 && Number.isFinite(months[0].avg_temperature)
            ? months[0].avg_temperature.toFixed(1)
            : '—'}
          unit="°C"
          accent="amber"
          icon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z" />
            </svg>
          }
        />
        <StatCard
          label="Avg Humidity"
          value={months.length > 0 && Number.isFinite(months[0].avg_humidity)
            ? months[0].avg_humidity.toFixed(1)
            : '—'}
          unit="%"
          accent="indigo"
          icon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
          }
        />
      </div>

      <section>
        <h2
          style={{
            fontFamily: 'var(--font-sans)',
            color: 'var(--color-text-primary)',
            fontSize: '1.1rem',
            fontWeight: 600,
            margin: '0 0 1rem',
          }}
        >
          Consumption History
        </h2>
        <ForecastChart months={months} />
      </section>
    </div>
  )
}
