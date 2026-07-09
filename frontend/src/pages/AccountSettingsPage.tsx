import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getSettings, updateSettings, clearChatHistory, clearAllData, getDataEntries } from '../api/client'
import type { UserSettings, UserSettingsUpdate } from '../api/types'

// ── Shared style tokens ──────────────────────────────────────────────────────

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

const selectStyle: React.CSSProperties = {
  ...inputStyle,
  cursor: 'pointer',
}

const errorText: React.CSSProperties = {
  fontFamily: 'var(--font-sans)',
  color: 'var(--color-red)',
  fontSize: '0.78rem',
  marginTop: '0.2rem',
}

const meta: React.CSSProperties = {
  fontFamily: 'var(--font-sans)',
  fontSize: '0.78rem',
  color: 'var(--color-text-muted)',
}

const sectionHeading: React.CSSProperties = {
  margin: '0 0 0.2rem',
  fontFamily: 'var(--font-sans)',
  fontSize: '1rem',
  fontWeight: 600,
}

const toggleRow: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '0.75rem',
}

// ── Constants ────────────────────────────────────────────────────────────────

const BASE_URL = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'
const TOKEN_KEY = 'wattif_token'

// ── Component ────────────────────────────────────────────────────────────────

export default function AccountSettingsPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  // Settings state
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [loadingSettings, setLoadingSettings] = useState(true)
  const [savingSection, setSavingSection] = useState<string | null>(null)
  const [settingsError, setSettingsError] = useState<string | null>(null)
  const [settingsSuccess, setSettingsSuccess] = useState<string | null>(null)

  // Password change form state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [newPasswordError, setNewPasswordError] = useState('')
  const [confirmPasswordError, setConfirmPasswordError] = useState('')
  const [apiError, setApiError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Data & privacy state
  const [confirmClearChat, setConfirmClearChat] = useState(false)
  const [confirmClearAll, setConfirmClearAll] = useState(false)

  // Data count for min_datapoints validation feedback
  const [dataEntryCount, setDataEntryCount] = useState<number | null>(null)

  // ── Load settings on mount ─────────────────────────────────────────────────
  useEffect(() => {
    getSettings()
      .then(s => setSettings(s))
      .catch(err => setSettingsError(err.message))
      .finally(() => setLoadingSettings(false))
    // Fetch current data entry count for min_datapoints validation
    getDataEntries()
      .then(entries => setDataEntryCount(entries.length))
      .catch(() => { /* non-critical */ })
  }, [])

  // ── Save helper ────────────────────────────────────────────────────────────
  const saveSettings = async (section: string, patch: UserSettingsUpdate) => {
    setSavingSection(section)
    setSettingsError(null)
    setSettingsSuccess(null)
    try {
      const updated = await updateSettings(patch)
      setSettings(updated)
      setSettingsSuccess(`${section} saved.`)
      setTimeout(() => setSettingsSuccess(null), 3000)
    } catch (err) {
      setSettingsError(err instanceof Error ? err.message : 'Failed to save settings.')
    } finally {
      setSavingSection(null)
    }
  }

  // ── Password validation ────────────────────────────────────────────────────
  const validate = (): boolean => {
    let valid = true
    setNewPasswordError('')
    setConfirmPasswordError('')

    if (newPassword.length < 8) {
      setNewPasswordError('Password must be at least 8 characters.')
      valid = false
    }

    if (newPassword !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match.')
      valid = false
    }

    return valid
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setApiError(null)
    setSuccessMessage(null)

    if (!validate()) return

    setSubmitting(true)
    try {
      const token = localStorage.getItem(TOKEN_KEY)
      const res = await fetch(`${BASE_URL}/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        const detail = (body as { detail?: string }).detail ?? res.statusText
        if (res.status === 401 || detail.toLowerCase().includes('current password')) {
          setApiError('Current password is incorrect.')
        } else {
          setApiError(detail)
        }
        return
      }

      setSuccessMessage('Password updated successfully.')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'An unexpected error occurred.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  if (loadingSettings) {
    return (
      <div style={{ padding: '1.5rem', fontFamily: 'var(--font-sans)', color: 'var(--color-text-muted)' }}>
        Loading settings…
      </div>
    )
  }

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '580px' }}>

      {/* ── Global feedback ─────────────────────────────────────────── */}
      {settingsSuccess && (
        <div
          role="status"
          style={{
            padding: '0.5rem 0.75rem',
            background: 'var(--color-rating-good-bg)',
            border: '1px solid var(--color-rating-good-border)',
            borderRadius: '0.375rem',
            fontFamily: 'var(--font-sans)',
            fontSize: '0.82rem',
            color: 'var(--color-rating-good-text)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span>{settingsSuccess}</span>
          <button
            type="button"
            onClick={() => setSettingsSuccess(null)}
            aria-label="Dismiss"
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1rem', color: 'var(--color-rating-good-text)', padding: '0.1rem 0.3rem' }}
          >×</button>
        </div>
      )}
      {settingsError && (
        <p role="alert" style={{ ...errorText, margin: 0 }}>{settingsError}</p>
      )}

      {/* ── Account Info ─────────────────────────────────────────────── */}
      <section className="card" aria-labelledby="account-info-hd">
        <h2 id="account-info-hd" style={sectionHeading}>Account</h2>
        <div>
          <span style={fieldLabel}>Email</span>
          <p style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: 'var(--color-text-primary)' }}>
            {user?.email ?? '—'}
          </p>
        </div>
      </section>

      {/* ── Password Change ──────────────────────────────────────────── */}
      <section className="card" aria-labelledby="password-change-hd">
        <h2 id="password-change-hd" style={sectionHeading}>Change Password</h2>
        <p style={{ ...meta, margin: '0 0 1rem' }}>
          Update your account password. New password must be at least 8 characters.
        </p>

        <form onSubmit={handlePasswordChange} noValidate>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div>
              <label htmlFor="current-password" style={fieldLabel}>Current Password</label>
              <input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={e => setCurrentPassword(e.target.value)}
                style={inputStyle}
                autoComplete="current-password"
              />
            </div>
            <div>
              <label htmlFor="new-password" style={fieldLabel}>New Password</label>
              <input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={e => { setNewPassword(e.target.value); setNewPasswordError('') }}
                style={inputStyle}
                autoComplete="new-password"
                aria-invalid={!!newPasswordError}
                aria-describedby={newPasswordError ? 'new-pw-err' : undefined}
              />
              {newPasswordError && (
                <span id="new-pw-err" role="alert" style={errorText}>{newPasswordError}</span>
              )}
            </div>
            <div>
              <label htmlFor="confirm-password" style={fieldLabel}>Confirm New Password</label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={e => { setConfirmPassword(e.target.value); setConfirmPasswordError('') }}
                style={inputStyle}
                autoComplete="new-password"
                aria-invalid={!!confirmPasswordError}
                aria-describedby={confirmPasswordError ? 'confirm-pw-err' : undefined}
              />
              {confirmPasswordError && (
                <span id="confirm-pw-err" role="alert" style={errorText}>{confirmPasswordError}</span>
              )}
            </div>
          </div>

          {apiError && (
            <p role="alert" style={{ ...errorText, marginTop: '0.75rem' }}>{apiError}</p>
          )}
          {successMessage && (
            <div
              role="status"
              style={{
                marginTop: '0.75rem',
                padding: '0.5rem 0.75rem',
                background: 'var(--color-rating-good-bg)',
                border: '1px solid var(--color-rating-good-border)',
                borderRadius: '0.375rem',
                fontFamily: 'var(--font-sans)',
                fontSize: '0.82rem',
                color: 'var(--color-rating-good-text)',
              }}
            >
              {successMessage}
            </div>
          )}

          <button
            type="submit"
            className="btn-primary"
            disabled={submitting}
            style={{ marginTop: '1rem' }}
          >
            {submitting ? 'Updating…' : 'Update Password'}
          </button>
        </form>
      </section>

      {/* ── 1. Customer Type ───────────────────────────────────────── */}
      <section className="card" aria-labelledby="customer-type-hd">
        <h2 id="customer-type-hd" style={sectionHeading}>Customer Type</h2>
        <p style={{ ...meta, margin: '0 0 0.75rem' }}>
          Your Meralco customer classification. Affects rate bracket selection in the price calculator.
        </p>
        <label htmlFor="customer-type-select" style={fieldLabel}>Type</label>
        <select
          id="customer-type-select"
          style={selectStyle}
          value={settings?.customer_type ?? 'Residential'}
          onChange={e => saveSettings('Customer type', { customer_type: e.target.value })}
          disabled={savingSection === 'Customer type'}
        >
          <option value="Residential">Residential</option>
          <option value="General Service A">General Service A</option>
          <option value="General Service B">General Service B</option>
        </select>
      </section>

      {/* ── 2. Default Forecast Horizon ────────────────────────────── */}
      <section className="card" aria-labelledby="forecast-horizon-hd">
        <h2 id="forecast-horizon-hd" style={sectionHeading}>Default Forecast Horizon</h2>
        <p style={{ ...meta, margin: '0 0 0.75rem' }}>
          Pre-selected horizon when you open the Forecast page.
        </p>
        <label htmlFor="horizon-select" style={fieldLabel}>Horizon (months)</label>
        <select
          id="horizon-select"
          style={selectStyle}
          value={settings?.default_forecast_horizon ?? 3}
          onChange={e => saveSettings('Forecast horizon', { default_forecast_horizon: Number(e.target.value) })}
          disabled={savingSection === 'Forecast horizon'}
        >
          <option value={1}>1 month</option>
          <option value={3}>3 months</option>
          <option value={6}>6 months</option>
          <option value={9}>9 months</option>
          <option value={12}>12 months</option>
        </select>
      </section>

      {/* ── 3. Rate Override ───────────────────────────────────────── */}
      <section className="card" aria-labelledby="rate-override-hd">
        <h2 id="rate-override-hd" style={sectionHeading}>Electricity Rate Override</h2>
        <p style={{ ...meta, margin: '0 0 0.75rem' }}>
          Set a manual ₱/kWh rate instead of using the auto-scraped Meralco rate. Leave empty to use the live rate.
        </p>
        <label htmlFor="rate-override-input" style={fieldLabel}>Rate (₱/kWh)</label>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input
            id="rate-override-input"
            type="number"
            step="0.01"
            min="0"
            max="100"
            placeholder="e.g. 11.80"
            style={{ ...inputStyle, maxWidth: '160px' }}
            defaultValue={settings?.rate_override ?? ''}
            onBlur={e => {
              const val = e.target.value ? Math.min(100, Math.max(0, parseFloat(e.target.value))) : null
              if (val !== null && isNaN(val)) return
              saveSettings('Rate override', { rate_override: val })
            }}
          />
          {settings?.rate_override && (
            <button
              type="button"
              className="btn-secondary"
              style={{ fontSize: '0.78rem', padding: '0.35rem 0.6rem' }}
              onClick={() => saveSettings('Rate override', { rate_override: null })}
            >
              Clear
            </button>
          )}
        </div>
      </section>

      {/* ── 4. Chat Preferences ────────────────────────────────────── */}
      <section className="card" aria-labelledby="chat-prefs-hd">
        <h2 id="chat-prefs-hd" style={sectionHeading}>Chat Preferences</h2>
        <p style={{ ...meta, margin: '0 0 0.75rem' }}>
          Control how the AI chat assistant manages message history.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div>
            <label htmlFor="chat-max-history" style={fieldLabel}>Max messages shown</label>
            <input
              id="chat-max-history"
              type="number"
              min={10}
              max={500}
              step={10}
              style={{ ...inputStyle, maxWidth: '120px' }}
              defaultValue={settings?.chat_max_history ?? 100}
              onBlur={e => {
                const val = Math.max(10, Math.min(500, parseInt(e.target.value) || 100))
                saveSettings('Chat preferences', { chat_max_history: val })
              }}
            />
          </div>
          <div style={toggleRow}>
            <div>
              <span style={fieldLabel}>Auto-clear chat on logout</span>
              <span style={{ ...meta, display: 'block' }}>Automatically delete chat history when you log out.</span>
            </div>
            <label className="toggle" style={{ flexShrink: 0 }}>
              <input
                type="checkbox"
                checked={settings?.chat_auto_clear ?? false}
                onChange={e => saveSettings('Chat preferences', { chat_auto_clear: e.target.checked })}
              />
              <span className="toggle-slider" />
            </label>
          </div>
        </div>
      </section>

      {/* ── 7. Data & Privacy ──────────────────────────────────────── */}
      <section className="card" aria-labelledby="data-privacy-hd">
        <h2 id="data-privacy-hd" style={sectionHeading}>Data &amp; Privacy</h2>
        <p style={{ ...meta, margin: '0 0 0.75rem' }}>
          Manage your stored data. These actions are irreversible.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {/* Clear chat */}
          {!confirmClearChat ? (
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setConfirmClearChat(true)}
            >
              Clear Chat History
            </button>
          ) : (
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <span style={{ ...meta, color: 'var(--color-red)' }}>Are you sure?</span>
              <button
                type="button"
                className="btn-danger"
                style={{ fontSize: '0.78rem', padding: '0.35rem 0.6rem' }}
                onClick={async () => {
                  await clearChatHistory()
                  setConfirmClearChat(false)
                  setSettingsSuccess('Chat history cleared.')
                }}
              >
                Yes, clear
              </button>
              <button
                type="button"
                className="btn-secondary"
                style={{ fontSize: '0.78rem', padding: '0.35rem 0.6rem' }}
                onClick={() => setConfirmClearChat(false)}
              >
                Cancel
              </button>
            </div>
          )}

          {/* Clear all data */}
          {!confirmClearAll ? (
            <button
              type="button"
              className="btn-danger"
              onClick={() => setConfirmClearAll(true)}
            >
              Clear All Data &amp; Model
            </button>
          ) : (
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <span style={{ ...meta, color: 'var(--color-red)' }}>This deletes everything. Are you sure?</span>
              <button
                type="button"
                className="btn-danger"
                style={{ fontSize: '0.78rem', padding: '0.35rem 0.6rem' }}
                onClick={async () => {
                  await clearAllData()
                  setConfirmClearAll(false)
                  setSettingsSuccess('All data and model cleared.')
                }}
              >
                Yes, delete all
              </button>
              <button
                type="button"
                className="btn-secondary"
                style={{ fontSize: '0.78rem', padding: '0.35rem 0.6rem' }}
                onClick={() => setConfirmClearAll(false)}
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </section>

      {/* ── 6. Notification Thresholds ─────────────────────────────── */}
      <section className="card" aria-labelledby="notifications-hd">
        <h2 id="notifications-hd" style={sectionHeading}>Notification Thresholds</h2>
        <p style={{ ...meta, margin: '0 0 0.75rem' }}>
          Set budget limits to get warnings when forecasts exceed your targets. Leave empty to disable.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div>
            <label htmlFor="notify-kwh-budget" style={fieldLabel}>Monthly kWh budget</label>
            <input
              id="notify-kwh-budget"
              type="number"
              min={0}
              max={99999}
              step={10}
              placeholder="e.g. 300"
              style={{ ...inputStyle, maxWidth: '160px' }}
              defaultValue={settings?.notify_kwh_budget ?? ''}
              onBlur={e => {
                const val = e.target.value ? Math.min(99999, Math.max(0, parseFloat(e.target.value))) : null
                if (val !== null && isNaN(val)) return
                saveSettings('Notifications', { notify_kwh_budget: val })
              }}
            />
          </div>
          <div>
            <label htmlFor="notify-bill-ceiling" style={fieldLabel}>Bill ceiling (₱)</label>
            <input
              id="notify-bill-ceiling"
              type="number"
              min={0}
              max={999999}
              step={100}
              placeholder="e.g. 5000"
              style={{ ...inputStyle, maxWidth: '160px' }}
              defaultValue={settings?.notify_bill_ceiling ?? ''}
              onBlur={e => {
                const val = e.target.value ? Math.min(999999, Math.max(0, parseFloat(e.target.value))) : null
                if (val !== null && isNaN(val)) return
                saveSettings('Notifications', { notify_bill_ceiling: val })
              }}
            />
          </div>
          <div>
            <label htmlFor="notify-high-consumption" style={fieldLabel}>High consumption warning (kWh)</label>
            <input
              id="notify-high-consumption"
              type="number"
              min={0}
              max={99999}
              step={10}
              placeholder="e.g. 400"
              style={{ ...inputStyle, maxWidth: '160px' }}
              defaultValue={settings?.notify_high_consumption ?? ''}
              onBlur={e => {
                const val = e.target.value ? Math.min(99999, Math.max(0, parseFloat(e.target.value))) : null
                if (val !== null && isNaN(val)) return
                saveSettings('Notifications', { notify_high_consumption: val })
              }}
            />
          </div>
        </div>
      </section>

      {/* ── 7. Model Retraining ────────────────────────────────────── */}
      <section className="card" aria-labelledby="retrain-hd">
        <h2 id="retrain-hd" style={sectionHeading}>Model Retraining</h2>
        <p style={{ ...meta, margin: '0 0 0.75rem' }}>
          Control when the SARIMAX forecast model retrains.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={toggleRow}>
            <div>
              <span style={fieldLabel}>Auto-retrain on CSV upload</span>
              <span style={{ ...meta, display: 'block' }}>Automatically retrain the model after every CSV upload.</span>
            </div>
            <label className="toggle" style={{ flexShrink: 0 }}>
              <input
                type="checkbox"
                checked={settings?.auto_retrain_on_upload ?? false}
                onChange={e => saveSettings('Model retraining', { auto_retrain_on_upload: e.target.checked })}
              />
              <span className="toggle-slider" />
            </label>
          </div>
          <div>
            <label htmlFor="min-datapoints" style={fieldLabel}>Minimum data points before training</label>
            <input
              id="min-datapoints"
              type="number"
              min={3}
              max={60}
              step={1}
              style={{ ...inputStyle, maxWidth: '120px' }}
              defaultValue={settings?.min_datapoints_to_train ?? 12}
              onBlur={e => {
                const val = Math.max(3, Math.min(60, parseInt(e.target.value) || 12))
                saveSettings('Model retraining', { min_datapoints_to_train: val })
              }}
            />
            <span style={{ ...meta, display: 'block', marginTop: '0.25rem' }}>
              Model won't train until you have at least this many months of data.
            </span>
            {dataEntryCount !== null && settings?.min_datapoints_to_train != null && dataEntryCount < settings.min_datapoints_to_train && (
              <span style={{ display: 'block', marginTop: '0.3rem', fontFamily: 'var(--font-sans)', fontSize: '0.78rem', color: 'var(--color-red)' }}>
                ⚠ You currently have {dataEntryCount} month(s) of data — need at least {settings.min_datapoints_to_train} to train.
              </span>
            )}
          </div>
        </div>
      </section>

      {/* ── Logout ───────────────────────────────────────────────────── */}
      <section className="card" aria-labelledby="logout-hd" style={{ borderColor: 'var(--color-red)' }}>
        <h2
          id="logout-hd"
          style={{ ...sectionHeading, color: 'var(--color-red)' }}
        >
          Session
        </h2>
        <p style={{ ...meta, margin: '0 0 1rem' }}>
          Log out of your account. You will be redirected to the login page.
        </p>
        <button
          type="button"
          className="btn-danger"
          onClick={handleLogout}
        >
          Logout
        </button>
      </section>
    </div>
  )
}
