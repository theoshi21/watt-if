import React, { useEffect, useState } from 'react'

export const OfflineBanner: React.FC = () => {
  const [offline, setOffline] = useState(!navigator.onLine)

  useEffect(() => {
    const goOnline = () => setOffline(false)
    const goOffline = () => setOffline(true)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => {
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
    }
  }, [])

  if (!offline) return null

  return (
    <div
      role="alert"
      aria-live="assertive"
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        background: 'var(--color-accent-primary)',
        color: 'var(--color-sidebar-bg)',
        padding: '0.5rem 1rem',
        textAlign: 'center',
        fontWeight: 'bold',
        fontSize: '0.9rem',
      }}
    >
      You are offline. Showing cached forecast data (may be up to 24 hours old).
    </div>
  )
}
