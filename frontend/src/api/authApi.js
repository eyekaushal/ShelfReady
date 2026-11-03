import { apiClient } from './apiClient'

export const authApi = {
  login: (username, password) =>
    apiClient.post('/auth/login/', { username, password }, { skipAuth: true }),

  register: ({ username, email, password }) =>
    apiClient.post('/auth/register/', { username, email, password }, { skipAuth: true }),

  logout: (refresh) => apiClient.post('/auth/logout/', { refresh }, { skipAuth: true }),

  me: () => apiClient.get('/auth/me/'),
}
