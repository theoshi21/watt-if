import React, { createContext, useContext, useEffect, useState } from 'react'

const TOKEN_KEY = 'wattif_token'

declare const __LOCAL_IP__: string
const BASE_URL =
  import.meta.env.VITE_API_BASE ||
  `http://${typeof __LOCAL_IP__ !== 'undefined' ? __LOCAL_IP__ : 'localhost'}:8000`

interface User {
  email: string
  id: number
}

interface AuthContextValue {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

/**
 * Decode a JWT payload without verifying the signature.
 * Returns null if the token is malformed.
 */
function decodeJwtPayload(token: string): { sub: number; email: string; exp: number; iat: number } | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    // Base64url decode the payload (second part)
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const decoded = atob(payload)
    return JSON.parse(decoded)
  } catch {
    return null
  }
}

/**
 * Check whether a JWT token is expired based on its exp claim.
 */
function isTokenExpired(payload: { exp: number }): boolean {
  const nowSeconds = Math.floor(Date.now() / 1000)
  return payload.exp <= nowSeconds
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Listen for forced logout events dispatched by the API client on 401 responses.
  // This avoids hard page reloads (window.location.href) that cause infinite refresh loops.
  useEffect(() => {
    const handleForceLogout = () => {
      setToken(null)
      setUser(null)
    }
    window.addEventListener('auth-logout', handleForceLogout)
    return () => window.removeEventListener('auth-logout', handleForceLogout)
  }, [])

  // On mount: check localStorage for an existing token, or auto-login with default account
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY)
      if (storedToken) {
        const payload = decodeJwtPayload(storedToken)
        if (payload && !isTokenExpired(payload)) {
          setToken(storedToken)
          setUser({ email: payload.email, id: payload.sub })
          setIsLoading(false)
          return
        }
        // Token expired or invalid — clear it
        localStorage.removeItem(TOKEN_KEY)
      }

      // No valid token: check if only the default account exists
      // If so, auto-login with default credentials (Req 1.2, 1.6)
      try {
        const res = await fetch(`${BASE_URL}/auth/has-users`)
        if (res.ok) {
          const data = (await res.json()) as { has_other_users: boolean }
          if (!data.has_other_users) {
            // Only default account exists — auto-login
            try {
              const loginRes = await fetch(`${BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: 'wattif@gmail.com', password: 'wattif' }),
              })
              if (loginRes.ok) {
                const loginData = (await loginRes.json()) as { token: string; email: string }
                localStorage.setItem(TOKEN_KEY, loginData.token)
                setToken(loginData.token)
                const payload = decodeJwtPayload(loginData.token)
                if (payload) {
                  setUser({ email: payload.email, id: payload.sub })
                } else {
                  setUser({ email: loginData.email, id: 0 })
                }
              }
            } catch {
              // Auto-login failed (e.g., default password changed) — user will see Login page
            }
          }
          // If has_other_users is true, do NOT auto-login — user sees Login page
        }
      } catch {
        // Network error checking has-users — fall through to Login page
      }

      setIsLoading(false)
    }

    initAuth()
  }, [])

  const login = async (email: string, password: string): Promise<void> => {
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })

    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      const detail = (body as { detail?: string }).detail ?? res.statusText
      throw new Error(detail)
    }

    const data = (await res.json()) as { token: string; email: string }
    localStorage.setItem(TOKEN_KEY, data.token)
    setToken(data.token)

    // Decode the token to get the user info
    const payload = decodeJwtPayload(data.token)
    if (payload) {
      setUser({ email: payload.email, id: payload.sub })
    } else {
      setUser({ email: data.email, id: 0 })
    }
  }

  const register = async (email: string, password: string): Promise<void> => {
    const res = await fetch(`${BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })

    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      const detail = (body as { detail?: string }).detail ?? res.statusText
      throw new Error(detail)
    }

    // Auto-login after successful registration
    await login(email, password)
  }

  const logout = (): void => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
