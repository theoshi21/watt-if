import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import logo from '../../wattif.png'

export default function LoginPage() {
  const { login, user, isLoading } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

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

  // If already authenticated, redirect to home (prevents flash of login form)
  if (user) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await login(email, password)
      // Navigation happens via the redirect above on re-render
    } catch {
      setError('Invalid email or password')
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

        {/* Login form */}
        <form onSubmit={handleSubmit} className="auth-page__form">
          <div className="auth-page__field">
            <label htmlFor="login-email" className="auth-page__label">
              Email
            </label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="you@example.com"
              className="auth-page__input"
            />
          </div>

          <div className="auth-page__field">
            <label htmlFor="login-password" className="auth-page__label">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              placeholder="••••••••"
              className="auth-page__input"
            />
          </div>

          <button
            type="submit"
            className="btn-primary auth-page__submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <p className="auth-page__footer">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="auth-page__link">
            Register
          </Link>
        </p>
      </div>
    </div>
  )
}
