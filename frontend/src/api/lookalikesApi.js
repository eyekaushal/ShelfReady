import { apiClient } from './apiClient'

export const lookalikesApi = {
  /** params: {status, product, page, page_size} */
  list: (params) => apiClient.get('/lookalikes/', { params }),

  /** status: "resolved_distinct" or "duplicate" */
  resolve: (id, status) => apiClient.post(`/lookalikes/${id}/resolve/`, { status }),

  /** Existing SKUs like the one being typed in the form. params: {name, brand, exclude?} */
  check: (params) => apiClient.get('/lookalikes/check/', { params }),
}
