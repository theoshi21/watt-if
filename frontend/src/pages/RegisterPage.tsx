import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import logo from '../../wattif.png'

const SPECIAL_CHARS = '!@#$%^&*()_+-=[]{}|;:,.<>?'

function checkStrength(pw: string) {
  return {
    length:   pw.length >= 8,
    upper:    /[A-Z]/.test(pw),
    lower:    /[a-z]/.test(pw),
    digit:    /\d/.test(pw),
    special:  /[!@#$%^&*()\\_+\-=\[\]{}|;:,.<>?]/.test(pw),
  }
}

export default function RegisterPage() {
  const { register, user, isLoading } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const strength = checkStrength(password)
  const passwordValid = Object.values(strength).every(Boolean)
  const passwordsMatch = password === confirmPassword && confirmPassword.length > 0
  const canSubmit = passwordValid && passwordsMatch && !isSubmitting

  if (isLoading) {
    return (
      <div className="auth-page">
        <div className="auth-page__loading">
          <div className="auth-spinner" role="status" aria-label="Loading" />
        </div>
      </div>
    )
  }

  if (user) return <Navigate to="/" replace />

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      await register(email, password)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  const EyeIcon = ({ visible }: { visible: boolean }) => visible ? (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  ) : (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )

  const eyeBtn = (show: boolean, toggle: () => void, label: string) => (
    <button type="button" onClick={toggle} aria-label={label} className="auth-page__eye-btn">
      <EyeIcon visible={show} />
    </button>
  )

  const reqLine = (met: boolean, text: string) => (
    <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontFamily: 'var(--font-sans)', fontSize: '0.72rem', color: met ? 'var(--color-teal)' : 'var(--color-text-muted)' }}>
      <span aria-hidden="true">{met ? '✓' : '○'}</span>{text}
    </span>
  )

  return (
    <div className="auth-page">
      <div className="auth-page__card">
        <div className="auth-page__brand">
          <img src={logo} alt="WATT-IF logo" className="auth-page__logo-img" />
          <h1 className="auth-page__title">WATT-IF</h1>
          <p className="auth-page__subtitle">Energy Intelligence</p>
        </div>

        {error && <div className="auth-page__error" role="alert">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-page__form">
          <div className="auth-page__field">
            <label htmlFor="register-email" className="auth-page__label">Email</label>
            <input id="register-email" type="email" required autoComplete="email"
              placeholder="you@example.com" value={email}
              onChange={(e) => setEmail(e.target.value)} className="auth-page__input" />
          </div>

          <div className="auth-page__field">
            <label htmlFor="register-password" className="auth-page__label">Password</label>
            <div className="auth-page__input-wrap">
              <input id="register-password" type={showPassword ? 'text' : 'password'} required
                autoComplete="new-password" placeholder="••••••••" value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="auth-page__input" />
              {eyeBtn(showPassword, () => setShowPassword(v => !v), showPassword ? 'Hide password' : 'Show password')}
            </div>
            {password.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem 0.75rem', marginTop: '0.4rem' }}>
                {reqLine(strength.length,   'At least 8 characters')}
                {reqLine(strength.upper,    'Uppercase letter')}
                {reqLine(strength.lower,    'Lowercase letter')}
                {reqLine(strength.digit,    'Number')}
                {reqLine(strength.special,  `Special character (${SPECIAL_CHARS.slice(0, 8)}…)`)}
              </div>
            )}
          </div>

          <div className="auth-page__field">
            <label htmlFor="register-confirm-password" className="auth-page__label">Confirm Password</label>
            <div className="auth-page__input-wrap">
              <input id="register-confirm-password" type={showConfirm ? 'text' : 'password'} required
                autoComplete="new-password" placeholder="••••••••" value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="auth-page__input" />
              {eyeBtn(showConfirm, () => setShowConfirm(v => !v), showConfirm ? 'Hide password' : 'Show password')}
            </div>
            {confirmPassword.length > 0 && !passwordsMatch && (
              <span className="auth-page__hint auth-page__hint--error">Passwords do not match</span>
            )}
          </div>

          <button type="submit" className="btn-primary auth-page__submit" disabled={!canSubmit}>
            {isSubmitting ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <p className="auth-page__footer">
          Already have an account?{' '}
          <Link to="/login" className="auth-page__link">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
