import { cn } from '../../lib/cn'
import { fieldBorder, fieldClasses } from './fieldStyles'

/** Text input. `leading` / `trailing` put an icon or a unit (₹) inside the field. */
export function Input({ invalid = false, leading, trailing, className, ...props }) {
  return (
    <div className={cn('relative', className)}>
      {leading ? (
        <span className="pointer-events-none absolute inset-y-0 left-0 flex w-9 items-center justify-center text-gray-400">
          {leading}
        </span>
      ) : null}
      <input
        className={cn(fieldClasses, fieldBorder(invalid), 'h-9 px-3', leading && 'pl-9', trailing && 'pr-9')}
        aria-invalid={invalid || undefined}
        {...props}
      />
      {trailing ? (
        <span className="pointer-events-none absolute inset-y-0 right-0 flex w-9 items-center justify-center text-gray-400">
          {trailing}
        </span>
      ) : null}
    </div>
  )
}
