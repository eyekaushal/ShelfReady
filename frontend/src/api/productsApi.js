import { apiClient } from './apiClient'

export const productsApi = {
  /** params: {search, brand, category, min_price, max_price, ordering, page, page_size} */
  list: (params) => apiClient.get('/products/', { params }),

  get: (id) => apiClient.get(`/products/${id}/`),

  create: (data) => apiClient.post('/products/', data),

  update: (id, data) => apiClient.put(`/products/${id}/`, data),

  remove: (id) => apiClient.delete(`/products/${id}/`),
}
