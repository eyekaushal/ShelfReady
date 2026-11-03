import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { productsApi } from '../api/productsApi'

const QUERY_KEYS = ['search', 'brand', 'category', 'min_price', 'max_price', 'ordering', 'page', 'page_size']

/** Paginated product list for the current URL filters. */
export function useProducts(filters) {
  const params = {}
  for (const key of QUERY_KEYS) {
    if (filters[key]) params[key] = filters[key]
  }

  return useQuery({
    queryKey: ['products', params],
    queryFn: () => productsApi.list(params),
    // Keep showing the old page while the next one loads, so the list doesn't flash empty.
    placeholderData: keepPreviousData,
  })
}

export function useProduct(id) {
  return useQuery({
    queryKey: ['product', String(id)],
    queryFn: () => productsApi.get(id),
    enabled: Boolean(id),
  })
}
