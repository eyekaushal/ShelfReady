import { useMutation, useQueryClient } from '@tanstack/react-query'

import { productsApi } from '../api/productsApi'

/** Create / update / delete. Each one refreshes the cached lists afterwards. */
export function useProductMutations() {
  const queryClient = useQueryClient()

  const refreshLists = () => {
    queryClient.invalidateQueries({ queryKey: ['products'] })
    queryClient.invalidateQueries({ queryKey: ['brands'] }) // a new brand may have appeared
  }

  const create = useMutation({
    mutationFn: productsApi.create,
    onSuccess: refreshLists,
  })

  const update = useMutation({
    mutationFn: ({ id, data }) => productsApi.update(id, data),
    onSuccess: (product) => {
      queryClient.setQueryData(['product', String(product.id)], product)
      refreshLists()
    },
  })

  const remove = useMutation({
    mutationFn: productsApi.remove,
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: ['product', String(id)] })
      refreshLists()
    },
  })

  return { create, update, remove }
}
