import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '../../auth/useAuth'
import { Wordmark } from './Wordmark'

/** Centered card for login and register. Logged-in users are sent to the catalog. */
export function AuthLayout() {
  const { isAuthenticated } = useAuth()
  if (isAuthenticated) return <Navigate to="/" replace />

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 py-10">
      <div className="mb-6">
        <Wordmark />
      </div>
      <div className="w-full max-w-sm rounded-xl border border-gray-200 bg-white p-6 shadow-[0_1px_2px_rgb(0_0_0/0.04)] animate-slide-up">
        <Outlet />
      </div>
      <p className="mt-6 max-w-sm text-center text-xs text-gray-400">
        A recognition-ready product catalog. Clean reference data for shelf-recognition cameras.
      </p>
    </div>
  )
}
