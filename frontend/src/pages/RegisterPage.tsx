import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import logo from '../../wattif.png'

export default function RegisterPage() {
  const { register, user, isLoading } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const passwordLongEnough = password.length >= 8
  const passwordsMatch = password === confirmPassword && confirmPassword.length > 0
  const canSubmit = passwordLongEnough && passwordsMatch && !isSubmitting

  // Prevent flicker: while auth is initializing, show a loading state
  if (isLoading) {
    return (
      <div className="auth-page">
        <div className="auth-page__loading">
          <div
            className="auth-spinner"
            role="status"
            aria-label="Loading"
          />
        </div>
      </div>
    )
  }

  // If already authenticated, redirect to home
  if (user) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await register(email, password)
      // Navigation happens via redirect above on re-render
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Registration failed'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-page__card">
        {/* Brand header */}
        <div className="auth-page__brand">
          <img
            src={logo}
            alt="WATT-IF logo"
            className="auth-page__logo-img"
          />
          <h1 className="auth-page__title">WATT-IF</h1>
          <p className="auth-page__subtitle">Energy Intelligence</p>
        </div>

        {/* Error alert */}
        {error && (
          <div className="auth-page__error" role="alert">
            {error}
          </div>
        )}

        {/* Register form */}
        <form onSubmit={handleSubmit} className="auth-page__form">
          <div className="auth-page__field">
            <label htmlFor="register-email" className="auth-page__label">
              Email
            </label>
            <input
              id="register-email"
              type="email"
              required
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="auth-page__input"
            />
          </div>

          <div className="auth-page__field">
            <label htmlFor="register-password" className="auth-page__label">
              Password
            </label>
            <input
              id="register-password"
              type="password"
              required
              autoComplete="new-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="auth-page__input"
            />
            {password.length > 0 && !passwordLongEnough && (
              <span className="auth-page__hint">
                Must be at least 8 characters
              </span>
            )}
          </div>

          <div className="auth-page__field">
            <label htmlFor="register-confirm-password" className="auth-page__label">
              Confirm Password
            </label>
            <input
              id="register-confirm-password"
              type="password"
              required
              autoComplete="new-password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="auth-page__input"
            />
            {confirmPassword.length > 0 && !passwordsMatch && (
              <span className="auth-page__hint auth-page__hint--error">
                Passwords do not match
              </span>
            )}
          </div>

          <button
            type="submit"
            className="btn-primary auth-page__submit"
            disabled={!canSubmit}
          >
            {isSubmitting ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <p className="auth-page__footer">
          Already have an account?{' '}
          <Link to="/login" className="auth-page__link">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
