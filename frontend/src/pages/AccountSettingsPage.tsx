import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// ── Shared style tokens (consistent with rest of app) ────────────────────────

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

// ── Constants ────────────────────────────────────────────────────────────────

const BASE_URL = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'
const TOKEN_KEY = 'wattif_token'

// ── Component ────────────────────────────────────────────────────────────────

export default function AccountSettingsPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  // Password change form state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Inline validation errors
  const [newPasswordError, setNewPasswordError] = useState('')
  const [confirmPasswordError, setConfirmPasswordError] = useState('')

  // API-level feedback
  const [apiError, setApiError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

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

      // Success
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

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '520px' }}>

      {/* ── Account Info ─────────────────────────────────────────────── */}
      <section className="card" aria-labelledby="account-info-hd">
        <h2
          id="account-info-hd"
          style={{ margin: '0 0 0.75rem', fontFamily: 'var(--font-sans)', fontSize: '1rem', fontWeight: 600 }}
        >
          Account
        </h2>
        <div>
          <span style={fieldLabel}>Email</span>
          <p style={{ margin: 0, fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: 'var(--color-text-primary)' }}>
            {user?.email ?? '—'}
          </p>
        </div>
      </section>

      {/* ── Password Change ──────────────────────────────────────────── */}
      <section className="card" aria-labelledby="password-change-hd">
        <h2
          id="password-change-hd"
          style={{ margin: '0 0 0.2rem', fontFamily: 'var(--font-sans)', fontSize: '1rem', fontWeight: 600 }}
        >
          Change Password
        </h2>
        <p style={{ ...meta, margin: '0 0 1rem' }}>
          Update your account password. New password must be at least 8 characters.
        </p>

        <form onSubmit={handlePasswordChange} noValidate>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {/* Current password */}
            <div>
              <label htmlFor="current-password" style={fieldLabel}>
                Current Password
              </label>
              <input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={e => setCurrentPassword(e.target.value)}
                style={inputStyle}
                autoComplete="current-password"
              />
            </div>

            {/* New password */}
            <div>
              <label htmlFor="new-password" style={fieldLabel}>
                New Password
              </label>
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

            {/* Confirm new password */}
            <div>
              <label htmlFor="confirm-password" style={fieldLabel}>
                Confirm New Password
              </label>
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

          {/* API error */}
          {apiError && (
            <p role="alert" style={{ ...errorText, marginTop: '0.75rem' }}>{apiError}</p>
          )}

          {/* Success message */}
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
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '0.5rem',
              }}
            >
              <span>{successMessage}</span>
              <button
                type="button"
                onClick={() => setSuccessMessage(null)}
                aria-label="Dismiss success message"
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  lineHeight: 1,
                  color: 'var(--color-rating-good-text)',
                  padding: '0.1rem 0.3rem',
                }}
              >
                ×
              </button>
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

      {/* ── Logout ───────────────────────────────────────────────────── */}
      <section className="card" aria-labelledby="logout-hd" style={{ borderColor: 'var(--color-red)' }}>
        <h2
          id="logout-hd"
          style={{ margin: '0 0 0.2rem', fontFamily: 'var(--font-sans)', fontSize: '1rem', fontWeight: 600, color: 'var(--color-red)' }}
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
