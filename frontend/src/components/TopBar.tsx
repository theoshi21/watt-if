import { useLocation, useNavigate } from 'react-router-dom'
import DarkModeToggle from './DarkModeToggle'

interface TopBarProps {
  onMenuClick: () => void
}

const PAGE_TITLES: Record<string, string> = {
  '/':               'Dashboard',
  '/forecast':       'Forecast',
  '/ask':            'Ask WATT-IF',
  '/data-entry':     'Data Entry',
  '/recommendations': 'Recommendations',
}

function UserCircleIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="10" r="3" />
      <path d="M7 20.662V19a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v1.662" />
    </svg>
  )
}

function HamburgerIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <line x1="3" y1="6"  x2="21" y2="6"  />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  )
}

const iconButtonStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  cursor: 'pointer',
  color: 'var(--color-text-primary)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '0.4rem',
  borderRadius: '0.375rem',
  lineHeight: 1,
}

export default function TopBar({ onMenuClick }: TopBarProps) {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const pageTitle = PAGE_TITLES[pathname] ?? 'Dashboard'

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0.75rem 1.5rem',
    background: 'var(--color-card-bg)',
    borderBottom: '1px solid var(--color-border)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  }

  return (
    <header style={headerStyle} className="topbar-compact">
      {/* Left: hamburger (mobile only) + page title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button
          className="topbar-menu-btn"
          aria-label="Open navigation menu"
          onClick={onMenuClick}
          style={iconButtonStyle}
        >
          <HamburgerIcon />
        </button>

        <h1
          style={{
            margin: 0,
            fontSize: '1.125rem',
            fontWeight: 600,
            fontFamily: 'var(--font-sans)',
            color: 'var(--color-text-primary)',
          }}
        >
          {pageTitle}
        </h1>
      </div>

      {/* Right: icon button row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
        <DarkModeToggle />

        <button
          aria-label="User account"
          style={iconButtonStyle}
          onClick={() => navigate('/account')}
        >
          <UserCircleIcon />
        </button>
      </div>
    </header>
  )
}
