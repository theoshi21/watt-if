import React from 'react'
import {
  BarChart,
  Bar,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ErrorBar,
} from 'recharts'
import type { ForecastMonth } from '../api/types'

interface Props {
  months: ForecastMonth[]
}

function formatMonth(ym: string): string {
  const [year, month] = ym.split('-')
  const date = new Date(parseInt(year), parseInt(month) - 1, 1)
  return date.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' })
}

const round = (n: number) => Number(n.toFixed(2))

interface ChartRow {
  label: string
  kwh: number
  kwh_lower: number
  kwh_upper: number
  kwh_band: number
  kwh_error: [number, number]   // [below, above] for ErrorBar
  price: number
  price_lower: number
  price_upper: number
  price_band: number
}

const colors = {
  kwh: 'var(--color-accent-primary)',
  price: 'var(--color-red)',
  grid: 'var(--color-border)',
  text: 'var(--color-text-primary)',
  muted: 'var(--color-text-muted)',
  border: 'var(--color-border)',
  card: 'var(--color-card-bg)',
  background: 'var(--color-page-bg)',
}

const chartCardStyle: React.CSSProperties = {
  background: 'var(--color-card-bg)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-card)',
  boxShadow: 'var(--shadow-card)',
  padding: '1.25rem',
  marginBottom: '1.25rem',
  overflow: 'hidden',
}

const titleStyle: React.CSSProperties = {
  margin: '0',
  fontSize: '1rem',
  fontWeight: 700,
  color: 'var(--color-text-primary)',
}

const subtitleStyle: React.CSSProperties = {
  margin: '0.25rem 0 1rem',
  fontSize: '0.85rem',
  color: 'var(--color-text-muted)',
}

const tooltipBoxStyle: React.CSSProperties = {
  background: 'var(--color-card-bg)',
  border: '1px solid var(--color-border)',
  borderRadius: '0.75rem',
  padding: '0.75rem',
  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
  fontSize: '0.85rem',
  color: 'var(--color-text-primary)',
}

function KwhTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  const row: ChartRow = payload[0].payload

  return (
    <div style={tooltipBoxStyle}>
      <div style={{ fontWeight: 700, marginBottom: '0.5rem' }}>{label}</div>
      <div>
        <strong>Forecast:</strong> {row.kwh.toFixed(2)} kWh
      </div>
      <div>
        <strong>95% CI:</strong> {row.kwh_lower.toFixed(2)} – {row.kwh_upper.toFixed(2)} kWh
      </div>
    </div>
  )
}

function PriceTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  const row: ChartRow = payload[0].payload

  return (
    <div style={tooltipBoxStyle}>
      <div style={{ fontWeight: 700, marginBottom: '0.5rem' }}>{label}</div>
      <div>
        <strong>Forecast:</strong> ₱{row.price.toFixed(2)}
      </div>
      <div>
        <strong>95% CI:</strong> ₱{row.price_lower.toFixed(2)} – ₱{row.price_upper.toFixed(2)}
      </div>
    </div>
  )
}

export const ForecastChart: React.FC<Props> = ({ months }) => {
  // Detect narrow screens for responsive chart margins
  const [isMobile, setIsMobile] = React.useState(() => window.innerWidth < 768)
  React.useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  const chartMargin = isMobile
    ? { top: 10, right: 8, bottom: 10, left: -10 }
    : { top: 16, right: 28, bottom: 16, left: 8 }
  const yAxisWidth = isMobile ? 52 : 72
  const xAxisFontSize = isMobile ? 10 : 12
  const yAxisFontSize = isMobile ? 10 : 12

  if (months.length === 0) {
    return (
      <div
        role="status"
        aria-label="No forecast data"
        style={{
          textAlign: 'center',
          padding: '2rem',
          color: colors.muted,
          border: `1px dashed ${colors.border}`,
          borderRadius: '1rem',
          background: colors.background,
        }}
      >
        No forecast data. Select a horizon above to generate a forecast.
      </div>
    )
  }

  const data: ChartRow[] = months.map((m) => ({
    label: formatMonth(m.year_month),

    kwh: round(m.kwh_forecast),
    kwh_lower: round(m.kwh_lower_95),
    kwh_upper: round(m.kwh_upper_95),
    kwh_band: round(m.kwh_upper_95 - m.kwh_lower_95),
    kwh_error: [
      round(m.kwh_forecast - m.kwh_lower_95),
      round(m.kwh_upper_95 - m.kwh_forecast),
    ],

    price: round(m.price_forecast),
    price_lower: round(m.price_lower_95),
    price_upper: round(m.price_upper_95),
    price_band: round(m.price_upper_95 - m.price_lower_95),
  }))

  return (
    <div aria-label="Forecast charts">
      <div style={chartCardStyle}>
        <h3 style={titleStyle}>Electricity Consumption Forecast</h3>
        <p style={subtitleStyle}>Monthly kWh forecast with 95% confidence interval</p>

        <ResponsiveContainer width="100%" height={340} className="chart-container-responsive">
          <BarChart data={data} margin={chartMargin}
            barCategoryGap="30%">
            <CartesianGrid strokeDasharray="4 4" stroke={colors.grid} vertical={false} />

            <XAxis
              dataKey="label"
              tick={{ fill: colors.muted, fontSize: xAxisFontSize }}
              axisLine={false}
              tickLine={false}
              dy={10}
            />

            <YAxis
              unit=" kWh"
              tick={{ fill: colors.muted, fontSize: yAxisFontSize }}
              axisLine={false}
              tickLine={false}
              width={yAxisWidth}
            />

            <Tooltip content={<KwhTooltip />} cursor={{ fill: 'var(--color-border)', opacity: 0.4 }} />

            <Bar
              dataKey="kwh"
              fill={colors.kwh}
              fillOpacity={0.85}
              radius={[4, 4, 0, 0]}
              maxBarSize={52}
            >
              <ErrorBar
                dataKey="kwh_error"
                width={6}
                strokeWidth={2}
                stroke={colors.kwh}
                direction="y"
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={chartCardStyle}>
        <h3 style={titleStyle}>Electricity Bill Forecast</h3>
        <p style={subtitleStyle}>Monthly estimated price with 95% confidence interval</p>

        <ResponsiveContainer width="100%" height={340} className="chart-container-responsive">
          <ComposedChart data={data} margin={chartMargin}>
            <CartesianGrid strokeDasharray="4 4" stroke={colors.grid} vertical={false} />

            <XAxis
              dataKey="label"
              tick={{ fill: colors.muted, fontSize: xAxisFontSize }}
              axisLine={false}
              tickLine={false}
              dy={10}
            />

            <YAxis
              unit=" ₱"
              tick={{ fill: colors.muted, fontSize: yAxisFontSize }}
              axisLine={false}
              tickLine={false}
              width={yAxisWidth}
            />

            <Tooltip content={<PriceTooltip />} />

            <Area
              type="monotone"
              dataKey="price_lower"
              stackId="price-ci"
              stroke="none"
              fill="transparent"
              legendType="none"
              tooltipType="none"
              activeDot={false}
            />

            <Area
              type="monotone"
              dataKey="price_band"
              stackId="price-ci"
              stroke="none"
              fill={colors.price}
              fillOpacity={0.16}
              legendType="none"
              activeDot={false}
            />

            <Line
              type="monotone"
              dataKey="price"
              stroke={colors.price}
              strokeWidth={3}
              dot={{ r: 4, strokeWidth: 2, fill: colors.card, stroke: colors.price }}
              activeDot={{ r: 6, strokeWidth: 2, fill: colors.price, stroke: colors.card }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}