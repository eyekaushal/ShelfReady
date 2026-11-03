import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { PageSpinner } from '../components/ui/Spinner'
import { useAuth } from './useAuth'

/** Wraps routes that need a login. Sends guests to /login and brings them back afterwards. */
export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) return <PageSpinner />
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />
  return <Outlet />
}
