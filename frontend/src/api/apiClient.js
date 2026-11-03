import axios from 'axios'

import { ApiError } from '../lib/apiError'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const BASE_URL = API_BASE_URL
const ACCESS_KEY = 'shelfready.access'
const REFRESH_KEY = 'shelfready.refresh'

/**
 * The one place the frontend talks to the API.
 *
 * - Adds "Authorization: Bearer <access>" to every request.
 * - When the access token has expired (401 "token_not_valid"), it silently gets a new one
 *   with the refresh token and retries the request once. Many requests failing at the same
 *   time share a single refresh call.
 * - Turns every failure into an ApiError with the backend's {code, message, details}.
 */
class ApiClient {
  constructor() {
    this.http = axios.create({ baseURL: BASE_URL, timeout: 20000 })
    this.refreshing = null // the in-flight refresh promise, so we only refresh once
    this.onSessionExpired = null // AuthContext sets this to log the user out in the UI

    this.http.interceptors.request.use((config) => {
      const token = this.getAccessToken()
      if (token && !config.skipAuth) config.headers.Authorization = `Bearer ${token}`
      return config
    })
    this.http.interceptors.response.use(
      (response) => response,
      (error) => this.handleError(error),
    )
  }

  // --- tokens (localStorage, so a page refresh keeps the user logged in) ---

  getAccessToken() {
    return localStorage.getItem(ACCESS_KEY)
  }

  getRefreshToken() {
    return localStorage.getItem(REFRESH_KEY)
  }

  hasSession() {
    return Boolean(this.getRefreshToken())
  }

  setTokens({ access, refresh }) {
    if (access) localStorage.setItem(ACCESS_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  }

  clearTokens() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  }

  // --- errors and refresh ---

  async handleError(error) {
    const { config, response } = error
    if (!response) {
      throw new ApiError({
        code: 'network_error',
        message: "Can't reach the server. Check your connection and try again.",
      })
    }

    const body = response.data?.error || {}
    const accessExpired =
      response.status === 401 &&
      body.code === 'token_not_valid' &&
      !config.skipAuth &&
      !config.retried &&
      this.hasSession()

    if (accessExpired) {
      try {
        const access = await this.refreshAccessToken()
        config.retried = true
        config.headers.Authorization = `Bearer ${access}`
        return this.http(config)
      } catch {
        // Refresh token is gone or expired too: the user has to log in again.
        this.clearTokens()
        this.onSessionExpired?.()
      }
    }

    throw new ApiError({
      code: body.code,
      message: body.message,
      details: body.details,
      status: response.status,
    })
  }

  refreshAccessToken() {
    if (!this.refreshing) {
      this.refreshing = this.http
        .post('/auth/refresh/', { refresh: this.getRefreshToken() }, { skipAuth: true })
        .then(({ data }) => {
          this.setTokens(data) // rotation: the response carries a new refresh token too
          return data.access
        })
        .finally(() => {
          this.refreshing = null
        })
    }
    return this.refreshing
  }

  // --- verbs: each returns the JSON body ---

  get(url, config) {
    return this.http.get(url, config).then((r) => r.data)
  }

  post(url, data, config) {
    return this.http.post(url, data, config).then((r) => r.data)
  }

  put(url, data, config) {
    return this.http.put(url, data, config).then((r) => r.data)
  }

  patch(url, data, config) {
    return this.http.patch(url, data, config).then((r) => r.data)
  }

  delete(url, config) {
    return this.http.delete(url, config).then((r) => r.data)
  }
}

export const apiClient = new ApiClient()
