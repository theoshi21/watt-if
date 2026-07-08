import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * AuthGuard wraps protected routes as a layout route.
 * - Shows a loading spinner while auth state is initializing.
 * - Redirects unauthenticated users to /login.
 * - Redirects authenticated users away from /login and /register to /.
 */
export default function AuthGuard() {
  const { user, isLoading } = useAuth()
  const { pathname } = useLocation()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen w-screen">
        <div
          className="h-10 w-10 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600"
          role="status"
          aria-label="Loading"
        />
      </div>
    )
  }

  const isAuthPage = pathname === '/login' || pathname === '/register'

  // Authenticated user on auth pages → redirect to home
  if (user && isAuthPage) {
    return <Navigate to="/" replace />
  }

  // Unauthenticated user on protected pages → redirect to login
  if (!user && !isAuthPage) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
