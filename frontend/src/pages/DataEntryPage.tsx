import React, { useState, useEffect, useCallback } from 'react'
import { UploadPanel } from '../components/UploadPanel'
import { TrainModelPanel } from '../components/TrainModelPanel'
import {
  getDataEntries, createDataEntry, updateDataEntry,
  deleteDataEntry, clearAllData, getMeralcoRate,
} from '../api/client'
import type { DataEntryRow, DataEntryUpdate } from '../api/types'

// ── Shared style tokens (mirrors PriceCalculatorPage / rest of app) ──────────

const meta: React.CSSProperties = {
  fontFamily: 'var(--font-sans)',
  fontSize: '0.78rem',
  color: 'var(--color-text-muted)',
}

const fieldLabel: React.CSSProperties = {
  display: 'block',
  fontFamily: 'var(--font-sans)',
  fontSize: '0.8rem',
  fontWeight: 600,
  color: 'var(--color-text-muted)',
  marginBottom: '0.25rem',
}

const inputStyle: React.CSSProperties = {
  background: 'var(--color-input-fill)',
  border: '1px solid var(--color-input-border)',
  borderRadius: '0.375rem',
  padding: '0.5rem 0.75rem',
  fontSize: '0.875rem',
  width: '100%',
  maxWidth: '100%',
  minWidth: 0,
  boxSizing: 'border-box',
  color: 'var(--color-text-primary)',
  fontFamily: 'var(--font-sans)',
}

const miniInput: React.CSSProperties = {
  ...inputStyle,
  padding: '0.25rem 0.4rem',
  fontSize: '0.8rem',
  minWidth: '72px',
  width: 'auto',
}

const miniInputText: React.CSSProperties = {
  ...miniInput,
  minWidth: '90px',
  fontFamily: 'var(--font-sans)',
}

const errorText: React.CSSProperties = {
  fontFamily: 'var(--font-sans)',
  color: 'var(--color-red)',
  fontSize: '0.78rem',
  marginTop: '0.2rem',
}

const th: React.CSSProperties = {
  padding: '0.45rem 0.6rem',
  fontWeight: 600,
  whiteSpace: 'nowrap',
  textAlign: 'left',
  fontSize: '0.75rem',
  color: 'var(--color-text-muted)',
  fontFamily: 'var(--font-sans)',
  letterSpacing: '0.02em',
}

const td: React.CSSProperties = {
  padding: '0.4rem 0.6rem',
  whiteSpace: 'nowrap',
  fontSize: '0.82rem',
  fontFamily: 'var(--font-sans)',
}

const mono: React.CSSProperties = { fontFamily: 'var(--font-mono)' }
const muted: React.CSSProperties = { color: 'var(--color-text-muted)' }

const btnGhost = (color = 'var(--color-text-primary)'): React.CSSProperties => ({
  padding: '0.22rem 0.6rem',
  fontSize: '0.75rem',
  background: 'none',
  border: `1px solid var(--color-border)`,
  borderRadius: '0.3rem',
  cursor: 'pointer',
  color,
  fontFamily: 'var(--font-sans)',
})

// ── ENSO badge ────────────────────────────────────────────────────────────────

function EnsoBadge({ phase }: { phase: number | null }) {
  if (phase === 1)
    return (
      <span style={{ background: 'var(--color-rating-poor-bg)', color: 'var(--color-rating-poor-text)', border: '1px solid var(--color-rating-poor-border)', borderRadius: '0.25rem', padding: '0.1rem 0.45rem', fontSize: '0.72rem', fontWeight: 700, fontFamily: 'var(--font-sans)' }}>
        El Niño
      </span>
    )
  if (phase === -1)
    return (
      <span style={{ background: 'var(--color-rating-good-bg)', color: 'var(--color-rating-good-text)', border: '1px solid var(--color-rating-good-border)', borderRadius: '0.25rem', padding: '0.1rem 0.45rem', fontSize: '0.72rem', fontWeight: 700, fontFamily: 'var(--font-sans)' }}>
        La Niña
      </span>
    )
  if (phase === null)
    return <span style={{ ...muted, fontSize: '0.78rem', fontFamily: 'var(--font-sans)' }}>—</span>
  return (
    <span style={{ background: 'var(--color-input-fill)', color: 'var(--color-text-muted)', border: '1px solid var(--color-border)', borderRadius: '0.25rem', padding: '0.1rem 0.45rem', fontSize: '0.72rem', fontFamily: 'var(--font-sans)' }}>
      Neutral
    </span>
  )
}

// ── Inline edit row ───────────────────────────────────────────────────────────

interface EditRowProps {
  entry: DataEntryRow
  onSave: (id: number, u: DataEntryUpdate) => Promise<void>
  onCancel: () => void
}

function EditRow({ entry, onSave, onCancel }: EditRowProps) {
  const [kwh, setKwh] = useState(String(entry.kwh))
  const [bill, setBill] = useState(entry.bill_amount != null ? String(entry.bill_amount) : '')
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const save = async () => {
    const n = parseFloat(kwh)
    if (isNaN(n) || n <= 0 || n > 1_000_000) { setErr('kWh must be 0–1,000,000'); return }
    setSaving(true); setErr(null)
    try {
      await onSave(entry.id, {
        kwh: n,
        bill_amount: bill !== '' ? parseFloat(bill) : null,
        label: entry.label ?? null,
      })
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Save failed')
      setSaving(false)
    }
  }

  return (
    <tr style={{ background: 'var(--color-input-fill)', outline: '2px solid var(--color-accent-primary)', outlineOffset: '-1px' }}>
      <td style={{ ...td, ...mono }}>{entry.year_month}</td>
      <td style={td}><input type="number" min={0} max={1000000} value={kwh} onChange={e => {
        const v = e.target.value
        if (v === '') { setKwh(v); return }
        setKwh(v)
      }} style={miniInput} /></td>
      <td style={td}><input type="number" min={0} max={9999999} value={bill} onChange={e => {
        const v = e.target.value
        if (v === '') { setBill(v); return }
        const num = parseFloat(v)
        if (!isNaN(num) && num > 9999999) { setBill('9999999'); return }
        setBill(v)
      }} style={miniInput} /></td>
      <td style={{ ...td, ...muted }}>{entry.source}</td>
      <td style={{ ...td, ...mono, ...muted }}>{entry.meralco_rate != null ? `₱${entry.meralco_rate.toFixed(4)}` : '—'}</td>
      <td style={{ ...td, ...mono, ...muted }}>{entry.avg_temperature != null ? `${entry.avg_temperature.toFixed(1)}` : '—'}</td>
      <td style={{ ...td, ...mono, ...muted }}>{entry.avg_humidity != null ? `${entry.avg_humidity.toFixed(1)}` : '—'}</td>
      <td style={{ ...td, ...mono, ...muted }}>{entry.total_rainfall_mm != null ? `${entry.total_rainfall_mm.toFixed(1)}` : '—'}</td>
      <td style={{ ...td, ...mono, ...muted }}>{entry.hot_days_count ?? '—'}</td>
      <td style={{ ...td, ...mono, ...muted }}>{entry.rainy_days_count ?? '—'}</td>
      <td style={{ ...td, ...mono, ...muted }}>{entry.holiday_count ?? '—'}</td>
      <td style={{ ...td, ...mono, ...muted }}>{entry.weekend_count ?? '—'}</td>
      <td style={td}><EnsoBadge phase={entry.enso_phase} /></td>
      <td style={td}>
        <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button onClick={save} disabled={saving} className="btn-primary"
            style={{ padding: '0.22rem 0.7rem', fontSize: '0.75rem' }}>
            {saving ? '…' : 'Save'}
          </button>
          <button onClick={onCancel} style={btnGhost()}>Cancel</button>
          {err && <span role="alert" style={errorText}>{err}</span>}
        </div>
      </td>
    </tr>
  )
}

// ── Delete confirm dialog (overlay, not inline row) ──────────────────────────

interface DeleteDialogProps {
  entry: DataEntryRow
  onConfirm: () => Promise<void>
  onCancel: () => void
}

function DeleteConfirmDialog({ entry, onConfirm, onCancel }: DeleteDialogProps) {
  const [deleting, setDeleting] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const confirm = async () => {
    setDeleting(true); setErr(null)
    try {
      await onConfirm()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Delete failed')
      setDeleting(false)
    }
  }

  return (
    // Backdrop
    <div
      onClick={deleting ? undefined : onCancel}
      style={{
        position: 'fixed', inset: 0, zIndex: 300,
        background: 'rgba(0,0,0,0.35)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '1rem',
      }}
    >
      {/* Dialog box */}
      <div
        onClick={e => e.stopPropagation()}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="del-dialog-title"
        style={{
          background: 'var(--color-card-bg)',
          border: '1px solid var(--color-red)',
          borderRadius: 'var(--radius-card)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
          padding: '1.25rem',
          maxWidth: '420px',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}
      >
        <p id="del-dialog-title" style={{
          margin: 0,
          fontFamily: 'var(--font-sans)',
          fontSize: '0.9rem',
          fontWeight: 500,
          color: 'var(--color-red)',
        }}>
          Delete entry for{' '}
          <strong style={{ fontFamily: 'var(--font-mono)' }}>{entry.year_month}</strong>?
          {' '}This will also remove the corresponding training record.
        </p>
        {err && (
          <p role="alert" style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: '0.82rem', color: 'var(--color-red)' }}>
            {err}
          </p>
        )}
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
          <button onClick={onCancel} disabled={deleting} className="btn-secondary">
            Cancel
          </button>
          <button
            onClick={confirm}
            disabled={deleting}
            className="btn-danger"
            style={{ fontWeight: 700 }}
          >
            {deleting ? 'Deleting…' : 'Yes, delete'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function DataEntryPage() {
  const nowYM = () => {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  }

  // form state
  const [yearMonth, setYearMonth] = useState(nowYM)
  const [kwh, setKwh] = useState('')
  const [bill, setBill] = useState('')
  const [rateOverride, setRateOverride] = useState('')
  const [kwhErr, setKwhErr] = useState('')
  const [submitErr, setSubmitErr] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // live Meralco rate for bill preview
  const [liveRate, setLiveRate] = useState<number | null>(null)
  useEffect(() => {
    getMeralcoRate()
      .then(r => {
        const residential = r.customer_types.find(ct => ct.type_key === 'Residential')
        if (residential) {
          // Use the >300 kWh bracket as the representative rate
          const bracket = residential.brackets.find(b => b.bracket_key === 'OVER 400 KWH')
            ?? residential.brackets[residential.brackets.length - 1]
          setLiveRate(bracket.residential_rate_per_kwh)
        }
      })
      .catch(() => { /* non-fatal — preview just won't show */ })
  }, [])

  // table state
  const [rows, setRows] = useState<DataEntryRow[]>([])
  const [fetchErr, setFetchErr] = useState<string | null>(null)
  const [editId, setEditId] = useState<number | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  // pagination
  const PAGE_SIZE = 10
  const [page, setPage] = useState(1)

  // clear-all state
  const [clearPhase, setClearPhase] = useState<'idle' | 'confirm' | 'clearing'>('idle')
  const [clearErr, setClearErr] = useState<string | null>(null)

  const load = useCallback(() => {
    getDataEntries()
      .then(data => { setRows(data); setPage(1) })
      .catch(e => setFetchErr(e instanceof Error ? e.message : 'Failed to load history.'))
  }, [])

  useEffect(() => { load() }, [load])

  // ── form submit ──────────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setKwhErr(''); setSubmitErr(null)
    const n = parseFloat(kwh)
    if (!kwh || isNaN(n) || n <= 0 || n > 1_000_000) {
      setKwhErr('Must be a number between 0 (exclusive) and 1,000,000'); return
    }
    setSubmitting(true)
    try {
      const row = await createDataEntry({
        year_month: yearMonth,
        kwh: n,
        bill_amount: bill !== '' ? parseFloat(bill) : null,
        rate_override: rateOverride !== '' ? parseFloat(rateOverride) : null,
        label: null,
        source: 'Manual',
      })
      setRows(prev => [row, ...prev])
      // Keep yearMonth as-is (better UX for consecutive entries) — only clear value fields
      setKwh(''); setBill(''); setRateOverride('')
    } catch (e) {
      setSubmitErr(e instanceof Error ? e.message : 'Submit failed.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleSave = async (id: number, update: DataEntryUpdate) => {
    const updated = await updateDataEntry(id, update)
    setRows(prev => prev.map(r => r.id === id ? updated : r))
    setEditId(null)
  }

  const handleDelete = async (id: number) => {
    await deleteDataEntry(id)
    setRows(prev => prev.filter(r => r.id !== id))
    setDeleteId(null)
  }

  const handleClearAll = async () => {
    setClearPhase('clearing'); setClearErr(null)
    try {
      await clearAllData()
      setRows([])
      setClearPhase('idle')
    } catch (e) {
      setClearErr(e instanceof Error ? e.message : 'Clear failed.')
      setClearPhase('confirm')
    }
  }

  const fmt = (v: number | null | undefined, d = 1) => v != null ? v.toFixed(d) : '—'

  return (
    <div className="page-content" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', boxSizing: 'border-box', width: '100%', overflowX: 'hidden' }}>

      {/* ── New Reading ──────────────────────────────────────────────────── */}
      <section className="card" aria-labelledby="new-reading-hd">
        <h2 id="new-reading-hd" style={{ margin: '0 0 0.2rem', fontFamily: 'var(--font-sans)', fontSize: '1rem', fontWeight: 600 }}>
          New Reading
        </h2>
        <p style={{ ...meta, margin: '0 0 1rem' }}>
          Enter the month and kWh from your bill. Rate, weather, and ENSO are resolved automatically.
        </p>

        <form onSubmit={handleSubmit} noValidate>
          {/* Required fields */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.85rem', marginBottom: '1rem' }}>
            <div>
              <label style={fieldLabel}>
                Month <span style={{ color: 'var(--color-red)' }}>*</span>
              </label>
              {/* Two selects instead of input[type=month] — avoids native picker overflow on mobile */}
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                <select
                  aria-label="Month"
                  value={yearMonth.slice(5, 7)}
                  onChange={e => setYearMonth(`${yearMonth.slice(0, 4)}-${e.target.value}`)}
                  style={{ ...inputStyle, flex: '1 1 0', minWidth: 0 }}
                >
                  {['01','02','03','04','05','06','07','08','09','10','11','12'].map((m, i) => (
                    <option key={m} value={m}>
                      {new Date(2000, i).toLocaleString('en-US', { month: 'short' })}
                    </option>
                  ))}
                </select>
                <select
                  aria-label="Year"
                  value={yearMonth.slice(0, 4)}
                  onChange={e => setYearMonth(`${e.target.value}-${yearMonth.slice(5, 7)}`)}
                  style={{ ...inputStyle, flex: '1 1 0', minWidth: 0 }}
                >
                  {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - 7 + i).map(y => (
                    <option key={y} value={String(y)}>{y}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label htmlFor="r-kwh" style={fieldLabel}>
                kWh <span style={{ color: 'var(--color-red)' }}>*</span>
              </label>
              <input id="r-kwh" type="number" min={0} max={99999} step="any"
                value={kwh} onChange={e => {
                  const v = e.target.value
                  if (v === '') { setKwh(v); return }
                  const num = parseFloat(v)
                  if (!isNaN(num) && num > 99999) { setKwh('99999'); return }
                  setKwh(v)
                }}
                style={inputStyle} aria-invalid={!!kwhErr}
                aria-describedby={kwhErr ? 'kwh-err' : undefined} />
              {kwhErr && <span id="kwh-err" role="alert" style={errorText}>{kwhErr}</span>}
              {/* Live bill preview */}
              {(() => {
                const n = parseFloat(kwh)
                const rate = rateOverride !== '' ? parseFloat(rateOverride) : liveRate
                if (!isNaN(n) && n > 0 && rate && rate > 0 && bill === '') {
                  return (
                    <span style={{ ...meta, marginTop: '0.3rem', display: 'block' }}>
                      Est. bill: <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-primary)' }}>
                        ₱{(n * rate).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </strong>
                      {' '}@ ₱{rate.toFixed(4)}/kWh
                    </span>
                  )
                }
                return null
              })()}
            </div>
          </div>

          {/* Optional overrides */}
          <details style={{ marginBottom: '1rem' }}>
            <summary style={{ cursor: 'pointer', ...meta, userSelect: 'none' }}>
              Optional overrides
            </summary>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.85rem', marginTop: '0.75rem' }}>
              <div>
                <label htmlFor="r-bill" style={fieldLabel}>Actual Bill Amount (PHP)</label>
                <input id="r-bill" type="number" min={0} step="any"
                  value={bill} onChange={e => setBill(e.target.value)}
                  style={inputStyle} placeholder="Auto: kWh × rate" />
              </div>
              <div>
                <label htmlFor="r-rate" style={fieldLabel}>Rate Override (₱/kWh)</label>
                <input id="r-rate" type="number" min={0} step="any"
                  value={rateOverride} onChange={e => setRateOverride(e.target.value)}
                  style={inputStyle} placeholder="Auto: live Meralco rate" />
              </div>
            </div>
            <p style={{ ...meta, margin: '0.5rem 0 0' }}>
              Leave blank to use automatically resolved values.
            </p>
          </details>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Submitting…' : 'Submit'}
            </button>
          </div>
          {submitErr && <p role="alert" style={{ ...errorText, marginTop: '0.5rem' }}>{submitErr}</p>}
        </form>
      </section>

      {/* ── Upload ───────────────────────────────────────────────────────── */}
      <UploadPanel onUploadSuccess={() => load()} />

      {/* ── Train Model ──────────────────────────────────────────────────── */}
      <TrainModelPanel />

      {/* ── Entry History ────────────────────────────────────────────────── */}
      <section
        className="card"
        aria-labelledby="history-hd"
        style={{ padding: 0 }}
      >
        {/* Header — padded normally */}
        <div style={{ padding: '1.25rem 1.25rem 0', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h2 id="history-hd" style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: '1rem', fontWeight: 600 }}>
            Entry History
            {rows.length > 0 && (
              <span style={{ ...meta, marginLeft: '0.5rem', fontWeight: 400 }}>({rows.length} entries)</span>
            )}
          </h2>
          <span style={meta}>
            Columns marked <em>auto</em> are resolved from real data and cannot be edited here.
          </span>
        </div>

        <div style={{ padding: '0 1.25rem' }}>
          {fetchErr && <p role="alert" style={{ ...errorText, marginBottom: '0.75rem' }}>{fetchErr}</p>}
        </div>

        {rows.length === 0 ? (
          <p style={{ ...meta, margin: 0, padding: '0 1.25rem 1.25rem' }}>No entries recorded yet.</p>
        ) : (
          <>
          {/* Delete confirm dialog — rendered as overlay, not inline row */}
          {deleteId !== null && (() => {
            const entry = rows.find(r => r.id === deleteId)
            if (!entry) return null
            return (
              <DeleteConfirmDialog
                entry={entry}
                onConfirm={() => handleDelete(entry.id)}
                onCancel={() => setDeleteId(null)}
              />
            )
          })()}
          {/* Table scrolls horizontally — bleeds to card edges so no double scrollbar */}
          <div style={{ overflowX: 'auto', width: '100%' }}>
            <table style={{ borderCollapse: 'collapse', fontSize: '0.82rem', fontFamily: 'var(--font-sans)', minWidth: '900px' }}>
              <colgroup>
                <col /><col /><col /><col />
                {/* Auto columns — shaded */}
                <col style={{ background: 'var(--color-input-fill)' }} />
                <col style={{ background: 'var(--color-input-fill)' }} />
                <col style={{ background: 'var(--color-input-fill)' }} />
                <col style={{ background: 'var(--color-input-fill)' }} />
                <col style={{ background: 'var(--color-input-fill)' }} />
                <col style={{ background: 'var(--color-input-fill)' }} />
                <col style={{ background: 'var(--color-input-fill)' }} />
                <col style={{ background: 'var(--color-input-fill)' }} />
                <col style={{ background: 'var(--color-input-fill)' }} />
                <col />
              </colgroup>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--color-border)' }}>
                  <th style={th}>Month</th>
                  <th style={th}>kWh</th>
                  <th style={th}>Bill (PHP)</th>
                  <th style={th}>Source</th>
                  <th style={th} title="Live Meralco residential rate">Rate ₱/kWh <em style={{ fontWeight: 400 }}>auto</em></th>
                  <th style={th} title="Open-Meteo monthly mean temperature">Temp °C <em style={{ fontWeight: 400 }}>auto</em></th>
                  <th style={th} title="Open-Meteo monthly mean humidity">Humidity % <em style={{ fontWeight: 400 }}>auto</em></th>
                  <th style={th} title="Open-Meteo total monthly rainfall">Rain mm <em style={{ fontWeight: 400 }}>auto</em></th>
                  <th style={th} title="Days with max temp ≥ 33 °C">Hot Days <em style={{ fontWeight: 400 }}>auto</em></th>
                  <th style={th} title="Days with any precipitation">Rainy Days <em style={{ fontWeight: 400 }}>auto</em></th>
                  <th style={th} title="Philippine public holidays">Holidays <em style={{ fontWeight: 400 }}>auto</em></th>
                  <th style={th} title="Calendar weekend days">Weekends <em style={{ fontWeight: 400 }}>auto</em></th>
                  <th style={th} title="ENSO phase from NOAA ONI">ENSO <em style={{ fontWeight: 400 }}>auto</em></th>
                  <th style={th}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE).map(entry => {
                  if (editId === entry.id) {
                    return (
                      <EditRow
                        key={entry.id}
                        entry={entry}
                        onSave={handleSave}
                        onCancel={() => setEditId(null)}
                      />
                    )
                  }
                  return (
                    <tr key={entry.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                      <td style={{ ...td, ...mono }}>{entry.year_month}</td>
                      <td style={{ ...td, ...mono }}>{entry.kwh}</td>
                      <td style={{ ...td, ...mono }}>{entry.bill_amount != null ? entry.bill_amount.toFixed(2) : '—'}</td>
                      <td style={{ ...td, ...muted }}>{entry.source}</td>
                      <td style={{ ...td, ...mono }}>{entry.meralco_rate != null ? `₱${entry.meralco_rate.toFixed(4)}` : '—'}</td>
                      <td style={{ ...td, ...mono }}>{fmt(entry.avg_temperature)}</td>
                      <td style={{ ...td, ...mono }}>{fmt(entry.avg_humidity)}</td>
                      <td style={{ ...td, ...mono }}>{fmt(entry.total_rainfall_mm)}</td>
                      <td style={{ ...td, ...mono }}>{entry.hot_days_count ?? '—'}</td>
                      <td style={{ ...td, ...mono }}>{entry.rainy_days_count ?? '—'}</td>
                      <td style={{ ...td, ...mono }}>{entry.holiday_count ?? '—'}</td>
                      <td style={{ ...td, ...mono }}>{entry.weekend_count ?? '—'}</td>
                      <td style={td}><EnsoBadge phase={entry.enso_phase} /></td>
                      <td style={td}>
                        <div style={{ display: 'flex', gap: '0.35rem' }}>
                          <button
                            onClick={() => { setDeleteId(null); setEditId(entry.id) }}
                            style={btnGhost()}
                            aria-label={`Edit ${entry.year_month}`}
                          >Edit</button>
                          <button
                            onClick={() => { setEditId(null); setDeleteId(entry.id) }}
                            style={btnGhost('var(--color-red)')}
                            aria-label={`Delete ${entry.year_month}`}
                          >Delete</button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination controls */}
          {(() => {
            const totalPages = Math.ceil(rows.length / PAGE_SIZE)
            if (totalPages <= 1) return null
            return (
              <div style={{ padding: '0.75rem 1.25rem 1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                <span style={{ ...meta, fontSize: '0.8rem' }}>
                  Page {page} of {totalPages} · {rows.length} entries
                </span>
                <div style={{ display: 'flex', gap: '0.35rem' }}>
                  <button onClick={() => setPage(1)} disabled={page === 1} style={btnGhost()} aria-label="First page">«</button>
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} style={btnGhost()} aria-label="Previous page">‹</button>
                  {Array.from({ length: totalPages }, (_, i) => i + 1)
                    .filter(p => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
                    .reduce<(number | '…')[]>((acc, p, i, arr) => {
                      if (i > 0 && p - (arr[i - 1] as number) > 1) acc.push('…')
                      acc.push(p)
                      return acc
                    }, [])
                    .map((p, i) =>
                      p === '…'
                        ? <span key={`ellipsis-${i}`} style={{ ...meta, padding: '0.2rem 0.3rem' }}>…</span>
                        : <button key={p} onClick={() => setPage(p as number)}
                            style={{ ...btnGhost(), fontWeight: page === p ? 700 : 400, borderColor: page === p ? 'var(--color-accent-primary)' : 'var(--color-border)', color: page === p ? 'var(--color-accent-primary)' : 'var(--color-text-primary)' }}>
                            {p}
                          </button>
                    )
                  }
                  <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} style={btnGhost()} aria-label="Next page">›</button>
                  <button onClick={() => setPage(totalPages)} disabled={page === totalPages} style={btnGhost()} aria-label="Last page">»</button>
                </div>
              </div>
            )
          })()}
          </>
        )}
      </section>

      {/* ── Danger Zone ──────────────────────────────────────────────────── */}
      <section className="card" aria-labelledby="danger-zone-hd"
        style={{ borderColor: 'var(--color-red)' }}>
        <h2 id="danger-zone-hd" style={{ margin: '0 0 0.2rem', fontFamily: 'var(--font-sans)', fontSize: '1rem', fontWeight: 600, color: 'var(--color-red)' }}>
          Danger Zone
        </h2>
        <p style={{ ...meta, margin: '0 0 1rem' }}>
          Permanently deletes all bill records, entry history, and the trained model. This cannot be undone.
        </p>

        <div style={{ minHeight: '2.5rem' }}>
          {clearPhase === 'idle' && (
          <button
            onClick={() => { setClearErr(null); setClearPhase('confirm') }}
            className="btn-danger"
            style={{ fontSize: '0.85rem' }}
          >
            Clear All Data…
          </button>
        )}

        {(clearPhase === 'confirm' || clearPhase === 'clearing') && (
          <div style={{
            background: 'var(--color-rating-poor-bg)',
            border: '1px solid var(--color-red)',
            borderRadius: '0.5rem',
            padding: '1rem',
            display: 'flex', flexDirection: 'column', gap: '0.75rem',
          }}>
            <p style={{ margin: 0, fontFamily: 'var(--font-sans)', fontWeight: 600, color: 'var(--color-red)', fontSize: '0.9rem' }}>
              Are you sure? This will wipe <strong>all</strong> monthly records, entry history,
              and the trained model artefact. There is no undo.
            </p>
            {clearErr && (
              <p role="alert" style={{ ...errorText, margin: 0 }}>{clearErr}</p>
            )}
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={handleClearAll}
                disabled={clearPhase === 'clearing'}
                className="btn-danger"
                style={{ fontWeight: 700 }}
              >
                {clearPhase === 'clearing' ? 'Clearing…' : 'Yes, clear everything'}
              </button>
              <button
                onClick={() => { setClearPhase('idle'); setClearErr(null) }}
                disabled={clearPhase === 'clearing'}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
        </div>
      </section>
    </div>
  )
}

export default DataEntryPage
