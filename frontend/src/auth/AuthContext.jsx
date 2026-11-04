import { useCallback, useEffect, useMemo, useState } from 'react'

import { apiClient } from '../api/apiClient'
import { authApi } from '../api/authApi'
import { AuthContext } from './authContext'

/**
 * Knows who is logged in. On page load it asks /auth/me/ if a session exists,
 * so a refresh keeps the user logged in.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(() => apiClient.hasSession())

  useEffect(() => {
    apiClient.onSessionExpired = () => setUser(null)
    if (!apiClient.hasSession()) return
    authApi
      .me()
      .then(setUser)
      .catch((error) => {
        // Only a 401 means the login is bad. A slow or sleeping server must not log anyone out.
        if (error.status === 401) apiClient.clearTokens()
      })
      .finally(() => setIsLoading(false))
  }, [])

  const login = useCallback(async (username, password) => {
    const tokens = await authApi.login(username, password)
    apiClient.setTokens(tokens)
    const me = await authApi.me()
    setUser(me)
    return me
  }, [])

  const register = useCallback(async (form) => {
    const result = await authApi.register(form)
    apiClient.setTokens(result)
    setUser(result.user)
    return result.user
  }, [])

  const logout = useCallback(async () => {
    const refresh = apiClient.getRefreshToken()
    apiClient.clearTokens()
    setUser(null)
    // Best effort: blacklist the refresh token. The UI is already logged out either way.
    if (refresh) await authApi.logout(refresh).catch(() => {})
  }, [])

  const value = useMemo(
    () => ({ user, isLoading, isAuthenticated: Boolean(user), login, register, logout }),
    [user, isLoading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
