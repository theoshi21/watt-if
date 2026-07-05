import React, { useEffect, useRef } from 'react'
import { NavLink } from 'react-router-dom'
import { HealthIndicator } from './HealthIndicator'
import ModelStatusPill from './ModelStatusPill'
import logo from '../../wattif.png'

/**
 * Sidebar
 *
 * Persistent navigation sidebar containing:
 * - WATT-IF logo + "ENERGY INTELLIGENCE" subtitle
 * - 5 NavLink items with active class callback
 * - HealthIndicator below nav
 * - ModelStatusPill above Settings
 * - Settings link at the bottom
 *
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.8, 14.1, 18.1
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

const settingsIcon = (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
)

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

  // Move focus to first nav link when sidebar opens on mobile
  useEffect(() => {
    if (_open && firstNavRef.current) {
      firstNavRef.current.focus()
    }
  }, [_open])

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

      {/* ── Bottom section: ModelStatusPill + Settings ──────── */}
      <div style={bottomSectionStyle}>
        <div style={pillWrapperStyle}>
          <ModelStatusPill />
        </div>

        <a
          href="#"
          className="nav-item"
          style={{ textDecoration: 'none' }}
          aria-label="Settings"
        >
          {settingsIcon}
          Settings
        </a>
      </div>
    </nav>
  )
}
