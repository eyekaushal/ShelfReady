import { ChevronDown } from 'lucide-react'

import { cn } from '../../lib/cn'
import { fieldBorder, fieldClasses } from './fieldStyles'

/** Native <select> with our styling. Options: [{value, label}]. */
export function Select({ options, placeholder, invalid = false, className, ...props }) {
  return (
    <div className={cn('relative', className)}>
      <select
        className={cn(fieldClasses, fieldBorder(invalid), 'h-9 appearance-none pl-3 pr-9', !props.value && 'text-gray-500')}
        aria-invalid={invalid || undefined}
        {...props}
      >
        {placeholder !== undefined ? <option value="">{placeholder}</option> : null}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDown
        className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-gray-400"
        aria-hidden="true"
      />
    </div>
  )
}
