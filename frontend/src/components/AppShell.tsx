import React, { useEffect, useRef, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { OfflineBanner } from './OfflineBanner'
// Sidebar and TopBar are created in tasks 5.1 and 5.3 respectively.
// These imports will resolve once those tasks are complete.
import Sidebar from './Sidebar'
import TopBar from './TopBar'

/** Selects all focusable elements within a container. */
const FOCUSABLE_SELECTORS =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), ' +
  'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

function getFocusableElements(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS))
}

export default function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Ref to the sidebar wrapper div — used for focus-trap enumeration
  const sidebarRef = useRef<HTMLDivElement>(null)

  // Stores the element that was focused before the drawer opened so focus can
  // be restored when the drawer closes (Req 18.5)
  const returnFocusRef = useRef<Element | null>(null)

  // Close drawer on Escape (Req 4.5)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && sidebarOpen) {
        setSidebarOpen(false)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [sidebarOpen])

  // Focus-trap: when drawer opens, save current focus and move focus into the
  // drawer; when drawer closes, restore focus (Req 18.3, 18.5)
  useEffect(() => {
    if (sidebarOpen) {
      // Save whatever was focused before opening
      returnFocusRef.current = document.activeElement

      // Move focus to the first focusable nav item inside the drawer
      const sidebar = sidebarRef.current
      if (sidebar) {
        const focusable = getFocusableElements(sidebar)
        if (focusable.length > 0) {
          focusable[0].focus()
        }
      }
    } else {
      // Restore focus when drawer closes
      if (returnFocusRef.current && returnFocusRef.current instanceof HTMLElement) {
        returnFocusRef.current.focus()
      }
      returnFocusRef.current = null
    }
  }, [sidebarOpen])

  // Tab / Shift+Tab focus-trap handler — keeps keyboard focus within the open
  // drawer so screen-reader and keyboard users can't accidentally tab behind it
  // (Req 18.3)
  useEffect(() => {
    if (!sidebarOpen) return

    const handleTabTrap = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return
      const sidebar = sidebarRef.current
      if (!sidebar) return

      const focusable = getFocusableElements(sidebar)
      if (focusable.length === 0) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (e.shiftKey) {
        // Shift+Tab: if focus is on the first element, wrap to last
        if (document.activeElement === first) {
          e.preventDefault()
          last.focus()
        }
      } else {
        // Tab: if focus is on the last element, wrap to first
        if (document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }

    document.addEventListener('keydown', handleTabTrap)
    return () => document.removeEventListener('keydown', handleTabTrap)
  }, [sidebarOpen])

  return (
    <>
      {/* OfflineBanner renders above the shell grid; it manages its own
          sticky positioning internally (Req 18.2) */}
      <OfflineBanner />

      {/* Two-column grid: 220px sidebar + 1fr main (collapses to 1fr on
          mobile via CSS). Classes defined in src/styles/index.css. */}
      <div className="app-shell">
        {/* Sidebar column — fixed drawer on mobile, static on desktop */}
        <div
          ref={sidebarRef}
          className={`app-shell__sidebar${sidebarOpen ? ' app-shell__sidebar--open' : ''}`}
        >
          <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        </div>

        {/* Main content column */}
        <div className="app-shell__main">
          <TopBar onMenuClick={() => setSidebarOpen(true)} />
          {/* Page content — flex:1 lets pages like AskPage fill remaining height.
              overflow-y: auto allows scrollable pages (Dashboard, Data Entry) to scroll
              within the fixed-height shell while the TopBar stays pinned. */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflowY: 'auto' }}>
            <Outlet />
          </div>
        </div>

        {/* Semi-transparent overlay — visible only when drawer is open on
            mobile. Clicking it closes the drawer (Req 4.6). */}
        <div
          className={`app-shell__overlay${sidebarOpen ? ' app-shell__overlay--visible' : ''}`}
          onClick={() => setSidebarOpen(false)}
          // aria-hidden so assistive technologies ignore the decorative backdrop
          aria-hidden="true"
        />
      </div>
    </>
  )
}
