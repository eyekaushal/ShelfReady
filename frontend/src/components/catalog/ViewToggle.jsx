import { LayoutGrid, List } from 'lucide-react'

import { cn } from '../../lib/cn'

/** Segmented control: table rows or image cards. */
export function ViewToggle({ value, onChange }) {
  const options = [
    { value: 'table', icon: List, label: 'Table view' },
    { value: 'grid', icon: LayoutGrid, label: 'Grid view' },
  ]

  return (
    <div className="inline-flex h-9 items-center rounded-md border border-gray-200 bg-gray-50 p-0.5" role="group">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          aria-label={option.label}
          aria-pressed={value === option.value}
          title={option.label}
          className={cn(
            'flex h-full w-8 items-center justify-center rounded transition-colors',
            value === option.value
              ? 'bg-white text-gray-900 shadow-[0_1px_2px_rgb(0_0_0/0.08),0_0_0_1px_rgb(0_0_0/0.04)]'
              : 'text-gray-500 hover:text-gray-900',
          )}
        >
          <option.icon className="size-4" aria-hidden="true" />
        </button>
      ))}
    </div>
  )
}
