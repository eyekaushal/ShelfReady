import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'

/**
 * The catalog's search, filters, sort, page and view all live in the URL query string,
 * so a filtered view can be shared or refreshed. Defaults are left out of the URL.
 */
export const FILTER_DEFAULTS = {
  search: '',
  brand: '',
  category: '',
  min_price: '',
  max_price: '',
  ordering: '-created_at',
  page: '1',
  page_size: '12',
  view: 'table',
}

const FILTER_KEYS = ['search', 'brand', 'category', 'min_price', 'max_price']

export function useUrlFilters() {
  const [params, setParams] = useSearchParams()

  const filters = useMemo(() => {
    const result = { ...FILTER_DEFAULTS }
    for (const key of Object.keys(FILTER_DEFAULTS)) {
      const value = params.get(key)
      if (value) result[key] = value
    }
    return result
  }, [params])

  /** Merge a patch into the URL. Any change other than the page itself goes back to page 1. */
  const setFilters = useCallback(
    (patch) => {
      setParams((previous) => {
        const next = new URLSearchParams(previous)
        for (const [key, value] of Object.entries(patch)) {
          const text = value == null ? '' : String(value)
          if (!text || text === FILTER_DEFAULTS[key]) next.delete(key)
          else next.set(key, text)
        }
        if (!('page' in patch)) next.delete('page')
        return next
      })
    },
    [setParams],
  )

  const clearFilters = useCallback(() => {
    setFilters(Object.fromEntries(FILTER_KEYS.map((key) => [key, ''])))
  }, [setFilters])

  const activeFilterCount = FILTER_KEYS.filter((key) => key !== 'search' && filters[key]).length

  return { filters, setFilters, clearFilters, activeFilterCount }
}
