import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { lookalikesApi } from '../api/lookalikesApi'

export function useLookalikes(params) {
  return useQuery({
    queryKey: ['lookalikes', params],
    queryFn: () => lookalikesApi.list(params),
    placeholderData: keepPreviousData,
  })
}

export function useResolveLookalike() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }) => lookalikesApi.resolve(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lookalikes'] }),
  })
}

/** The warning under the form. `name` and `brand` should already be debounced. */
export function useSkuCheck({ name, brand, exclude }) {
  return useQuery({
    queryKey: ['sku-check', name, brand, exclude],
    queryFn: () => lookalikesApi.check({ name, brand, ...(exclude ? { exclude } : {}) }),
    enabled: name.length >= 3 && brand.length >= 2,
    retry: false, // only a hint: if it fails, simply show nothing
  })
}
