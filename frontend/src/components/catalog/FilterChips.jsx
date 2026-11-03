import { FILTER_DEFAULTS } from '../../hooks/useUrlFilters'
import { formatPrice } from '../../lib/format'
import { Chip } from '../ui/Chip'
import { SORT_OPTIONS } from './sortOptions'

/**
 * Shows every active filter as a removable chip, so the user always sees exactly
 * how the list is narrowed down. The AI search (Block 8) reuses this row.
 */
export function FilterChips({ filters, setFilters, clearFilters, categories }) {
  const chips = []

  if (filters.search) chips.push({ key: 'search', label: 'Search', value: `“${filters.search}”` })
  if (filters.brand) chips.push({ key: 'brand', label: 'Brand', value: filters.brand })
  if (filters.category) {
    const category = categories.find((item) => item.slug === filters.category)
    chips.push({ key: 'category', label: 'Category', value: category?.full_path || filters.category })
  }
  if (filters.min_price) chips.push({ key: 'min_price', label: 'Min', value: formatPrice(filters.min_price) })
  if (filters.max_price) chips.push({ key: 'max_price', label: 'Max', value: formatPrice(filters.max_price) })
  if (filters.ordering !== FILTER_DEFAULTS.ordering) {
    const option = SORT_OPTIONS.find((item) => item.value === filters.ordering)
    chips.push({ key: 'ordering', label: 'Sort', value: option?.label || filters.ordering })
  }

  if (chips.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-2 animate-fade-in">
      {chips.map((chip) => (
        <Chip key={chip.key} label={chip.label} value={chip.value} onRemove={() => setFilters({ [chip.key]: '' })} />
      ))}
      <button
        type="button"
        onClick={() => {
          clearFilters()
          setFilters({ ordering: '' })
        }}
        className="ml-1 text-xs font-medium text-accent hover:text-accent-hover"
      >
        Clear all
      </button>
    </div>
  )
}
