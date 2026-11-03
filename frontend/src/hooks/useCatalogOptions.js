import { useQuery } from '@tanstack/react-query'

import { catalogApi } from '../api/catalogApi'

const FIVE_MINUTES = 5 * 60 * 1000

/** Categories and brands for dropdowns. They rarely change, so they're cached for 5 minutes. */
export function useCategories() {
  return useQuery({ queryKey: ['categories'], queryFn: catalogApi.categories, staleTime: FIVE_MINUTES })
}

export function useBrands() {
  return useQuery({ queryKey: ['brands'], queryFn: catalogApi.brands, staleTime: FIVE_MINUTES })
}
