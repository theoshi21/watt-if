import React from 'react'
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
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
  price: number
  price_lower: number
  price_upper: number
  price_band: number
}

const colors = {
  kwh: '#1d4ed8',
  price: '#c2410c',
  grid: '#d1d5db',
  text: '#111827',
  muted: '#4b5563',
  border: '#d1d5db',
  card: '#ffffff',
  background: '#f9fafb',
}

const chartCardStyle: React.CSSProperties = {
  background: colors.card,
  border: `1px solid ${colors.border}`,
  borderRadius: '1rem',
  padding: '1.25rem',
  marginBottom: '1.25rem',
  boxShadow: '0 4px 14px rgba(0, 0, 0, 0.05)',
}

const titleStyle: React.CSSProperties = {
  margin: '0',
  fontSize: '1rem',
  fontWeight: 700,
  color: colors.text,
}

const subtitleStyle: React.CSSProperties = {
  margin: '0.25rem 0 1rem',
  fontSize: '0.85rem',
  color: colors.muted,
}

const tooltipBoxStyle: React.CSSProperties = {
  background: colors.card,
  border: `1px solid ${colors.border}`,
  borderRadius: '0.75rem',
  padding: '0.75rem',
  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
  fontSize: '0.85rem',
  color: colors.text,
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

        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={data} margin={{ top: 16, right: 28, bottom: 16, left: 8 }}>
            <CartesianGrid strokeDasharray="4 4" stroke={colors.grid} vertical={false} />

            <XAxis
              dataKey="label"
              tick={{ fill: colors.muted, fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              dy={10}
            />

            <YAxis
              unit=" kWh"
              tick={{ fill: colors.muted, fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={72}
            />

            <Tooltip content={<KwhTooltip />} />

            <Area
              type="monotone"
              dataKey="kwh_lower"
              stackId="kwh-ci"
              stroke="none"
              fill="transparent"
              legendType="none"
              tooltipType="none"
              activeDot={false}
            />

            <Area
              type="monotone"
              dataKey="kwh_band"
              stackId="kwh-ci"
              stroke="none"
              fill={colors.kwh}
              fillOpacity={0.16}
              legendType="none"
              activeDot={false}
            />

            <Line
              type="monotone"
              dataKey="kwh"
              stroke={colors.kwh}
              strokeWidth={3}
              dot={{ r: 4, strokeWidth: 2, fill: colors.card, stroke: colors.kwh }}
              activeDot={{ r: 6, strokeWidth: 2, fill: colors.kwh, stroke: colors.card }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div style={chartCardStyle}>
        <h3 style={titleStyle}>Electricity Bill Forecast</h3>
        <p style={subtitleStyle}>Monthly estimated price with 95% confidence interval</p>

        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={data} margin={{ top: 16, right: 28, bottom: 16, left: 8 }}>
            <CartesianGrid strokeDasharray="4 4" stroke={colors.grid} vertical={false} />

            <XAxis
              dataKey="label"
              tick={{ fill: colors.muted, fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              dy={10}
            />

            <YAxis
              unit=" ₱"
              tick={{ fill: colors.muted, fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={72}
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