import React, { useState, useEffect, useMemo } from 'react'
import { getMeralcoRate, refreshMeralcoRate, getSettings } from '../api/client'
import type { MeralcoRateResponse, CustomerType, RateBracket } from '../api/types'

// ── Helpers ───────────────────────────────────────────────────────────────

const peso = (n: number) =>
  `${n < 0 ? '−' : ''}₱${Math.abs(n).toLocaleString('en-PH', {
    minimumFractionDigits: 2, maximumFractionDigits: 2,
  })}`

const formatDate = (iso: string) => {
  try {
    return new Date(iso).toLocaleString('en-PH', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return iso }
}

function autoBracket(ct: CustomerType, kwh: number): RateBracket {
  if (ct.type_key === 'Residential') {
    if (kwh <= 50)  return ct.brackets.find(b => b.bracket_key === '0 TO 50 KWH')    ?? ct.brackets[0]
    if (kwh <= 70)  return ct.brackets.find(b => b.bracket_key === '51 TO 70 KWH')   ?? ct.brackets[1]
    if (kwh <= 100) return ct.brackets.find(b => b.bracket_key === '71 TO 100 KWH')  ?? ct.brackets[2]
    if (kwh <= 200) return ct.brackets.find(b => b.bracket_key === '101 TO 200 KWH') ?? ct.brackets[3]
    if (kwh <= 300) return ct.brackets.find(b => b.bracket_key === '201 TO 300 KWH') ?? ct.brackets[4]
    if (kwh <= 400) return ct.brackets.find(b => b.bracket_key === '301 TO 400 KWH') ?? ct.brackets[5]
    return ct.brackets.find(b => b.bracket_key === 'OVER 400 KWH') ?? ct.brackets[ct.brackets.length - 1]
  }
  if (ct.type_key === 'General Service A') {
    if (kwh <= 200) return ct.brackets.find(b => b.bracket_key === '0 TO 200 KWH')   ?? ct.brackets[0]
    if (kwh <= 300) return ct.brackets.find(b => b.bracket_key === '201 TO 300 KWH') ?? ct.brackets[1]
    if (kwh <= 400) return ct.brackets.find(b => b.bracket_key === '301 TO 400 KWH') ?? ct.brackets[2]
    return ct.brackets.find(b => b.bracket_key === 'OVER 400 KWH') ?? ct.brackets[ct.brackets.length - 1]
  }
  return ct.brackets[0]
}

// ── Styles ────────────────────────────────────────────────────────────────

const meta: React.CSSProperties = {
  fontFamily: 'var(--font-sans)',
  fontSize: '0.78rem',
  color: 'var(--color-text-muted)',
}

const badge = (fallback: boolean): React.CSSProperties => ({
  display: 'inline-block',
  padding: '0.12rem 0.5rem',
  borderRadius: '9999px',
  fontSize: '0.72rem',
  fontFamily: 'var(--font-sans)',
  fontWeight: 600,
  background: fallback ? 'var(--color-rating-fair-bg)' : 'var(--color-rating-good-bg)',
  color: fallback ? 'var(--color-rating-fair-text)' : 'var(--color-rating-good-text)',
  border: `1px solid ${fallback ? 'var(--color-rating-fair-border)' : 'var(--color-rating-good-border)'}`,
  marginLeft: '0.4rem',
  verticalAlign: 'middle',
})

const inputStyle: React.CSSProperties = {
  background: 'var(--color-input-fill)',
  border: '1px solid var(--color-input-border)',
  fontFamily: 'var(--font-mono)',
  borderRadius: '0.375rem',
  padding: '0.6rem 0.75rem',
  fontSize: '1.1rem',
  width: '100%',
  boxSizing: 'border-box' as const,
  color: 'var(--color-text-primary)',
}

const selectStyle: React.CSSProperties = {
  background: 'var(--color-input-fill)',
  border: '1px solid var(--color-input-border)',
  fontFamily: 'var(--font-sans)',
  borderRadius: '0.375rem',
  padding: '0.5rem 0.75rem',
  fontSize: '0.875rem',
  width: '100%',
  color: 'var(--color-text-primary)',
  cursor: 'pointer',
}

const fieldLabel: React.CSSProperties = {
  ...meta,
  display: 'block',
  marginBottom: '0.3rem',
  fontWeight: 500,
  color: 'var(--color-text-primary)',
}

// ── Bill line component ───────────────────────────────────────────────────

function BillLine({ label, sublabel, amount, bold, dim, separator, pct }: {
  label: string; sublabel?: string; amount: number
  bold?: boolean; dim?: boolean; separator?: boolean; pct?: number
}) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
      padding: '0.45rem 0',
      borderTop: separator ? '1px solid var(--color-border)' : undefined,
      gap: '0.5rem',
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.1rem', minWidth: 0 }}>
        <span style={{ fontFamily: 'var(--font-sans)', fontSize: bold ? '0.9rem' : '0.85rem', fontWeight: bold ? 700 : 400, color: 'var(--color-text-primary)' }}>
          {label}
          {pct != null && !bold && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--color-text-muted)', marginLeft: '0.4rem' }}>
              {pct.toFixed(2)}%
            </span>
          )}
        </span>
        {sublabel && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>
            {sublabel}
          </span>
        )}
      </div>
      <span style={{
        fontFamily: 'var(--font-mono)', fontSize: bold ? '1rem' : '0.875rem', fontWeight: bold ? 700 : 500,
        color: dim || amount < 0 ? 'var(--color-teal)' : 'var(--color-text-primary)',
        whiteSpace: 'nowrap' as const, flexShrink: 0,
      }}>{peso(amount)}</span>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function PriceCalculatorPage() {
  const [rateData, setRateData] = useState<MeralcoRateResponse | null>(null)
  const [rateError, setRateError] = useState<string | null>(null)
  const [rateLoading, setRateLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const [kwhInput, setKwhInput] = useState('')
  // Customer type selection — defaults to user's saved preference (falls back to Residential)
  const [customerTypeKey, setCustomerTypeKey] = useState('Residential')
  // Bracket selection — 'auto' means auto-select based on kWh
  const [bracketKey, setBracketKey] = useState<string>('auto')

  useEffect(() => {
    getMeralcoRate()
      .then(r => { setRateData(r); setRateError(null) })
      .catch(err => setRateError(err instanceof Error ? err.message : 'Failed to load rate.'))
      .finally(() => setRateLoading(false))
    // Load user's preferred customer type from settings
    getSettings()
      .then(s => { if (s.customer_type) setCustomerTypeKey(s.customer_type) })
      .catch(() => { /* settings unavailable — keep default */ })
  }, [])

  const handleRefresh = async () => {
    setRefreshing(true)
    setRateError(null)
    try { setRateData(await refreshMeralcoRate()) }
    catch (err) { setRateError(err instanceof Error ? err.message : 'Refresh failed.') }
    finally { setRefreshing(false) }
  }

  // Reset bracket to auto when customer type changes
  const handleCustomerTypeChange = (key: string) => {
    setCustomerTypeKey(key)
    setBracketKey('auto')
  }

  const kwh = parseFloat(kwhInput)
  const kwhValid = kwhInput !== '' && !isNaN(kwh) && kwh > 0

  const selectedType: CustomerType | null = useMemo(() =>
    rateData?.customer_types.find(ct => ct.type_key === customerTypeKey) ?? rateData?.customer_types[0] ?? null,
    [rateData, customerTypeKey]
  )

  const bracket: RateBracket | null = useMemo(() => {
    if (!selectedType) return null
    if (bracketKey === 'auto' && kwhValid) return autoBracket(selectedType, kwh)
    if (bracketKey === 'auto') return selectedType.brackets[0]
    return selectedType.brackets.find(b => b.bracket_key === bracketKey) ?? selectedType.brackets[0]
  }, [selectedType, bracketKey, kwhValid, kwh])

  const autoDetectedBracket = kwhValid && selectedType ? autoBracket(selectedType, kwh) : null

  const lines = kwhValid && bracket ? (() => {
    const b = bracket
    const gen    = b.generation_charge_per_kwh    * kwh
    const trans  = b.transmission_charge_per_kwh  * kwh
    const sl     = b.system_loss_per_kwh           * kwh
    const dist   = b.distribution_charge_per_kwh  * kwh
    const supKwh = b.supply_per_kwh               * kwh
    const supFix = b.supply_fixed_monthly
    const metKwh = b.metering_per_kwh             * kwh
    const metFix = b.metering_fixed_monthly
    const other  = b.other_charges_per_kwh         * kwh
    // VAT amounts
    const vatGen    = b.vat_generation         * kwh
    const vatTrans  = b.vat_transmission       * kwh
    const vatSl     = b.vat_system_loss        * kwh
    const vatDist   = b.vat_distribution       * kwh
    const vatSupKwh = b.vat_supply_per_kwh     * kwh
    const vatSupFix = b.vat_supply_fixed
    const vatMetKwh = b.vat_metering_per_kwh   * kwh
    const vatMetFix = b.vat_metering_fixed
    const subtotal = gen + trans + sl + dist + supKwh + supFix + metKwh + metFix + other
    const totalVat = vatGen + vatTrans + vatSl + vatDist + vatSupKwh + vatSupFix + vatMetKwh + vatMetFix
    const total  = subtotal + totalVat
    return { gen, trans, sl, dist, supKwh, supFix, metKwh, metFix, other, subtotal, vatGen, vatTrans, vatSl, vatDist, vatSupKwh, vatSupFix, vatMetKwh, vatMetFix, totalVat, total, effRate: total / kwh }
  })() : null

  return (
    <div className="page-content" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ margin: '0 0 0.2rem', fontFamily: 'var(--font-sans)', fontSize: '1.3rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            Bill Calculator
          </h1>
          <p style={{ ...meta, margin: 0 }}>
            Meralco Summary Schedule of Rates
            {rateData && !rateLoading && (
              <>{rateData.effective_month ? ` · ${rateData.effective_month}` : ''}
                <span style={badge(rateData.is_fallback)}>{rateData.is_fallback ? 'Fallback' : 'Live'}</span>
              </>
            )}
          </p>
        </div>
        <button className="btn-secondary" onClick={handleRefresh} disabled={refreshing || rateLoading}
          style={{ fontSize: '0.82rem', padding: '0.4rem 0.9rem', whiteSpace: 'nowrap' as const }}>
          {refreshing ? 'Refreshing…' : '↻ Refresh Rate'}
        </button>
      </div>

      {rateLoading && <p style={meta} role="status">Loading rate schedule…</p>}
      {rateError && !rateLoading && (
        <div className="card" role="alert" style={{ color: 'var(--color-red)', fontFamily: 'var(--font-sans)', fontSize: '0.875rem' }}>
          {rateError}
        </div>
      )}

      {/* Two-column layout */}
      {!rateLoading && rateData && selectedType && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 400px) 1fr', gap: '1.25rem', alignItems: 'start' }}
          className="calc-layout">

          {/* LEFT: selectors + total */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

            <section className="card" aria-labelledby="input-heading">
              <h2 id="input-heading" style={{ margin: '0 0 0.875rem', fontFamily: 'var(--font-sans)', fontSize: '0.95rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                Your Details
              </h2>

              {/* Customer type */}
              <div style={{ marginBottom: '0.875rem' }}>
                <label htmlFor="customer-type" style={fieldLabel}>Account type</label>
                <select id="customer-type" value={customerTypeKey}
                  onChange={e => handleCustomerTypeChange(e.target.value)} style={selectStyle}>
                  {rateData.customer_types.map(ct => (
                    <option key={ct.type_key} value={ct.type_key}>{ct.type_label}</option>
                  ))}
                </select>
              </div>

              {/* kWh */}
              <div style={{ marginBottom: '0.875rem' }}>
                <label htmlFor="calc-kwh" style={fieldLabel}>Monthly consumption</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <input id="calc-kwh" type="number" min={0} max={99999} step="any" placeholder="e.g. 250"
                    value={kwhInput} onChange={e => {
                      const v = e.target.value
                      if (v === '' || v === '-') { setKwhInput(v); return }
                      const num = parseFloat(v)
                      if (!isNaN(num) && num > 99999) { setKwhInput('99999'); return }
                      setKwhInput(v)
                    }}
                    aria-label="Monthly consumption in kWh" style={inputStyle} />
                  <span style={{ fontFamily: 'var(--font-sans)', fontSize: '0.9rem', color: 'var(--color-text-muted)', flexShrink: 0 }}>kWh</span>
                </div>
              </div>

              {/* Bracket override — only shown when customer type has multiple brackets */}
              {selectedType.brackets.length > 1 && (
                <div>
                  <label htmlFor="bracket-select" style={fieldLabel}>
                    Rate bracket
                    {bracketKey === 'auto' && autoDetectedBracket && (
                      <span style={{ ...meta, marginLeft: '0.4rem', fontWeight: 400 }}>
                        (auto: {autoDetectedBracket.bracket_label})
                      </span>
                    )}
                  </label>
                  <select id="bracket-select" value={bracketKey}
                    onChange={e => setBracketKey(e.target.value)} style={selectStyle}>
                    <option value="auto">Auto-select based on kWh</option>
                    {selectedType.brackets.map(b => (
                      <option key={b.bracket_key} value={b.bracket_key}>{b.bracket_label}</option>
                    ))}
                  </select>
                </div>
              )}
            </section>

            {/* Total card */}
            {lines ? (
              <div style={{
                background: 'var(--color-accent-primary)', borderRadius: '0.5rem',
                padding: '1.125rem 1.25rem', display: 'flex', flexDirection: 'column', gap: '0.3rem',
              }}>
                <span style={{ fontFamily: 'var(--font-sans)', fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: '0.05em', color: 'rgba(255,255,255,0.65)' }}>
                  Estimated Bill
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '2rem', fontWeight: 700, color: '#fff', lineHeight: 1.1 }}>
                  {peso(lines.total)}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'rgba(255,255,255,0.65)' }}>
                  {kwh} kWh · ₱{lines.effRate.toFixed(4)}/kWh effective rate
                </span>
                <span style={{ fontFamily: 'var(--font-sans)', fontSize: '0.7rem', color: 'rgba(255,255,255,0.5)', marginTop: '0.2rem' }}>
                  {selectedType.type_label} · {bracket?.bracket_label} · Total Energy Amount ÷ kWh
                </span>
              </div>
            ) : (
              <div style={{ ...meta, padding: '0.75rem 1rem', background: 'var(--color-input-fill)', borderRadius: '0.375rem', border: '1px solid var(--color-border)' }}>
                Enter your monthly consumption to see your estimated bill.
              </div>
            )}

            <div style={{ ...meta, display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
              <span>Source: <a href="https://company.meralco.com.ph/news-and-advisories/rates-archives" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-accent-primary)' }}>Meralco Rates Archive</a></span>
              <span>Last fetched: {formatDate(rateData.fetched_at)}</span>
            </div>
          </div>

          {/* RIGHT: line-item breakdown */}
          <section className="card" aria-labelledby="breakdown-heading">
            <h2 id="breakdown-heading" style={{ margin: '0 0 0.25rem', fontFamily: 'var(--font-sans)', fontSize: '0.95rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Charges for this billing period
            </h2>
            <p style={{ ...meta, margin: '0 0 0.75rem' }}>
              {selectedType.type_label} · {bracket?.bracket_label} bracket
            </p>

            {lines && bracket ? (
              <div>
                <BillLine label="Generation"       sublabel={`₱${bracket.generation_charge_per_kwh.toFixed(4)} × ${kwh} kWh`}   amount={lines.gen}    pct={lines.gen / lines.total * 100} />
                <BillLine label="Transmission"     sublabel={`₱${bracket.transmission_charge_per_kwh.toFixed(4)} × ${kwh} kWh`} amount={lines.trans}  pct={lines.trans / lines.total * 100} />
                <BillLine label="System Loss"      sublabel={`₱${bracket.system_loss_per_kwh.toFixed(4)} × ${kwh} kWh`}          amount={lines.sl}     pct={lines.sl / lines.total * 100} />
                <BillLine label="Distribution"     sublabel={`₱${bracket.distribution_charge_per_kwh.toFixed(4)} × ${kwh} kWh`}    amount={lines.dist}   pct={lines.dist / lines.total * 100} />
                <BillLine label="Supply"           sublabel={`₱${bracket.supply_per_kwh.toFixed(4)} × ${kwh} kWh`}                 amount={lines.supKwh} pct={lines.supKwh / lines.total * 100} />
                <BillLine label="Supply (fixed)"   sublabel={`₱${bracket.supply_fixed_monthly.toFixed(4)}/mo`}                      amount={lines.supFix} pct={lines.supFix / lines.total * 100} />
                <BillLine label="Metering"         sublabel={`₱${bracket.metering_per_kwh.toFixed(4)} × ${kwh} kWh`}               amount={lines.metKwh} pct={lines.metKwh / lines.total * 100} />
                <BillLine label="Metering (fixed)" sublabel={`₱${bracket.metering_fixed_monthly.toFixed(4)}/mo`}                   amount={lines.metFix} pct={lines.metFix / lines.total * 100} />
                <BillLine label="UC / FIT / GEA / AWAT / Other" sublabel={`₱${bracket.other_charges_per_kwh.toFixed(4)} × ${kwh} kWh · VAT-exempt`} amount={lines.other} dim={lines.other < 0} pct={lines.other / lines.total * 100} />
                <BillLine label="Subtotal (before VAT)" amount={lines.subtotal} bold separator />

                {/* VAT Section — separate card-like container */}
                <div style={{
                  marginTop: '1rem',
                  padding: '0.875rem 1rem',
                  background: 'var(--color-input-fill)',
                  borderRadius: '0.375rem',
                  border: '1px solid var(--color-border)',
                }}>
                  <h3 style={{ margin: '0 0 0.4rem', fontFamily: 'var(--font-sans)', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                    Value-Added Tax (VAT)
                  </h3>
                  <BillLine label="Generation VAT"     sublabel={`9.22% of ₱${lines.gen.toFixed(2)}`}    amount={lines.vatGen}    pct={lines.vatGen / lines.total * 100} />
                  <BillLine label="Transmission VAT"   sublabel={`11.14% of ₱${lines.trans.toFixed(2)}`} amount={lines.vatTrans}  pct={lines.vatTrans / lines.total * 100} />
                  <BillLine label="System Loss VAT"    sublabel={`9.46% of ₱${lines.sl.toFixed(2)}`}     amount={lines.vatSl}     pct={lines.vatSl / lines.total * 100} />
                  <BillLine label="Distribution VAT"   sublabel={`12% of ₱${lines.dist.toFixed(2)}`}     amount={lines.vatDist}   pct={lines.vatDist / lines.total * 100} />
                  <BillLine label="Supply VAT"         sublabel={`12% of ₱${(lines.supKwh + lines.supFix).toFixed(2)}`} amount={lines.vatSupKwh + lines.vatSupFix} pct={(lines.vatSupKwh + lines.vatSupFix) / lines.total * 100} />
                  <BillLine label="Metering VAT"       sublabel={`12% of ₱${(lines.metKwh + lines.metFix).toFixed(2)}`} amount={lines.vatMetKwh + lines.vatMetFix} pct={(lines.vatMetKwh + lines.vatMetFix) / lines.total * 100} />
                  <BillLine label="Total VAT" amount={lines.totalVat} bold separator />
                </div>

                <BillLine label="Total Amount Due" amount={lines.total} bold separator />
                <p style={{ ...meta, marginTop: '0.75rem' }}>
                  Does not include bill deposit, applied credits, lifeline/senior discounts, or LFT charges.
                </p>
              </div>
            ) : (
              <p style={{ ...meta, padding: '1.5rem 0', textAlign: 'center' as const }}>
                Enter a kWh value on the left to see the breakdown.
              </p>
            )}

            {rateData.is_fallback && (
              <p style={{ ...meta, marginTop: '0.5rem', color: 'var(--color-rating-fair-text)' }}>
                Live PDF unavailable — using hardcoded June 2026 rates. Hit ↻ Refresh to retry.
              </p>
            )}
          </section>
        </div>
      )}

      <style>{`
        @media (max-width: 767px) {
          .calc-layout { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}
