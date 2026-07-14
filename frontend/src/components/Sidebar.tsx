import React, { useEffect, useRef } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { HealthIndicator } from './HealthIndicator'
import ModelStatusPill from './ModelStatusPill'
import { useAuth } from '../context/AuthContext'
import logo from '../../wattif.png'

/**
 * Sidebar
 *
 * Persistent navigation sidebar containing:
 * - WATT-IF logo + "ENERGY INTELLIGENCE" subtitle
 * - 5 NavLink items with active class callback
 * - HealthIndicator below nav
 * - ModelStatusPill above user info
 * - User email display (truncated at 24 chars) + Logout button
 *
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.8, 10.1, 10.2, 10.3, 10.4, 10.5, 14.1, 18.1
 */

export interface SidebarProps {
  open: boolean
  onClose: () => void
}

interface NavItem {
  label: string
  path: string
  end?: boolean
  icon: React.ReactNode
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    path: '/',
    end: true,
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
  },
  {
    label: 'Forecast',
    path: '/forecast',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
  },
  {
    label: 'Ask WATT-IF',
    path: '/ask',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    label: 'Price Calculator',
    path: '/calculator',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <rect x="2" y="3" width="20" height="18" rx="2" ry="2" />
        <line x1="8" y1="12" x2="16" y2="12" />
        <line x1="8" y1="8" x2="10" y2="8" />
        <line x1="8" y1="16" x2="10" y2="16" />
        <line x1="12" y1="8" x2="16" y2="8" />
        <line x1="12" y1="16" x2="16" y2="16" />
      </svg>
    ),
  },
  {
    label: 'Data Entry',
    path: '/data-entry',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
    ),
  },
]

/** Truncate email to 24 characters + ellipsis if needed */
function truncateEmail(email: string): string {
  if (email.length > 24) {
    return email.slice(0, 24) + '\u2026'
  }
  return email
}

const emailDisplayStyle: React.CSSProperties = {
  padding: '0.25rem 1.25rem',
  fontSize: '0.75rem',
  color: 'var(--color-text-muted)',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
}

const logoutButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.5rem',
  width: '100%',
  padding: '0.5rem 1.25rem',
  border: 'none',
  background: 'none',
  color: 'var(--color-text-secondary)',
  fontSize: '0.85rem',
  cursor: 'pointer',
  textAlign: 'left',
}

const sidebarStyle: React.CSSProperties = {
  height: '100vh',
  background: 'var(--color-sidebar-bg)',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',       // never scroll — everything must fit
  color: 'var(--color-text-secondary)',
}

const logoSectionStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: '0.25rem',
  padding: '0.85rem 1.25rem 0.75rem',
  borderBottom: '1px solid rgba(255,255,255,0.08)',
  flexShrink: 0,            // never compress the logo area
}

const nameStyle: React.CSSProperties = {
  fontFamily: 'var(--font-sans)',
  fontWeight: 700,
  fontSize: '0.95rem',
  color: 'var(--color-text-secondary)',
  textAlign: 'center' as const,
}

const subtitleStyle: React.CSSProperties = {
  fontSize: '0.6rem',
  fontFamily: 'var(--font-mono)',
  letterSpacing: '0.12em',
  color: 'var(--color-text-muted)',
  textTransform: 'uppercase' as const,
  textAlign: 'center' as const,
}

const navListStyle: React.CSSProperties = {
  listStyle: 'none',
  margin: 0,
  padding: '0.25rem 0',
  flex: '1 1 0',            // takes all remaining space, can shrink
  minHeight: 0,             // critical: allows flex child to shrink below content size
}

const dividerStyle: React.CSSProperties = {
  border: 'none',
  borderTop: '1px solid rgba(255,255,255,0.08)',
  margin: '0',
  flexShrink: 0,
}

const bottomSectionStyle: React.CSSProperties = {
  padding: '0.5rem 0 0.5rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.25rem',
  flexShrink: 0,            // never compress the bottom items
}

const pillWrapperStyle: React.CSSProperties = {
  padding: '0 1.25rem 0.25rem',
}

const healthWrapperStyle: React.CSSProperties = {
  padding: '0.35rem 1.25rem',
  flexShrink: 0,
}

export default function Sidebar({ open: _open, onClose: _onClose }: SidebarProps) {
  const firstNavRef = useRef<HTMLAnchorElement>(null)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (_open && firstNavRef.current) {
      firstNavRef.current.focus()
    }
  }, [_open])

  const handleLogout = () => {
    try { logout() } catch { /* token already cleared */ }
    navigate('/login')
  }

  return (
    <nav aria-label="Main navigation" style={sidebarStyle}>
      {/* ── Logo + subtitle ─────────────────────────────────── */}
      <div style={logoSectionStyle}>
        <img
          src={logo}
          alt="WATT-IF logo"
          style={{ width: 40, height: 40, objectFit: 'contain' }}
        />
        <span style={nameStyle}>WATT-IF</span>
        <span style={subtitleStyle}>ENERGY INTELLIGENCE</span>
      </div>

      {/* ── Nav links ───────────────────────────────────────── */}
      <ul style={navListStyle} role="list">
        {navItems.map((item, idx) => (
          <li key={item.path}>
            <NavLink
              to={item.path}
              end={item.end}
              className={({ isActive }) =>
                isActive ? 'nav-item nav-item--active' : 'nav-item'
              }
              ref={idx === 0 ? firstNavRef : undefined}
            >
              {item.icon}
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>

      <hr style={dividerStyle} />

      {/* ── Health indicator ────────────────────────────────── */}
      <div style={healthWrapperStyle}>
        <HealthIndicator />
      </div>

      <hr style={dividerStyle} />

      {/* ── Bottom section: ModelStatusPill + User email + Logout ── */}
      <div style={bottomSectionStyle}>
        <div style={pillWrapperStyle}>
          <ModelStatusPill />
        </div>

        {user && (
          <>
            <div
              style={emailDisplayStyle}
              title={user.email}
              aria-label={`Logged in as ${user.email}`}
            >
              {truncateEmail(user.email)}
            </div>
            <button
              onClick={handleLogout}
              style={logoutButtonStyle}
              className="nav-item"
              aria-label="Logout"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              Logout
            </button>
          </>
        )}
      </div>
    </nav>
  )
}
