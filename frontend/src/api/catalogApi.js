import { apiClient } from './apiClient'

/** Dropdown data: the category tree and the distinct brand names. */
export const catalogApi = {
  categories: () => apiClient.get('/categories/'),
  brands: () => apiClient.get('/brands/'),
}
