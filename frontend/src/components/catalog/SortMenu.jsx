import { ArrowUpDown, ChevronDown } from 'lucide-react'

import { Button } from '../ui/Button'
import { Menu } from '../ui/Menu'
import { SORT_OPTIONS } from './sortOptions'

export function SortMenu({ value, onChange }) {
  const current = SORT_OPTIONS.find((option) => option.value === value) || SORT_OPTIONS[0]

  return (
    <Menu
      trigger={(open) => (
        <Button aria-expanded={open} aria-haspopup="menu">
          <ArrowUpDown className="size-4 text-gray-500" />
          <span className="hidden text-gray-500 sm:inline">Sort:</span>
          {current.label}
          <ChevronDown className="size-3.5 text-gray-400" />
        </Button>
      )}
      items={SORT_OPTIONS.map((option) => ({
        label: option.label,
        selected: option.value === current.value,
        onSelect: () => onChange(option.value),
      }))}
    />
  )
}
