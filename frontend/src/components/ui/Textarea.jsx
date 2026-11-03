import { cn } from '../../lib/cn'
import { fieldBorder, fieldClasses } from './fieldStyles'

export function Textarea({ invalid = false, className, rows = 4, ...props }) {
  return (
    <textarea
      rows={rows}
      className={cn(fieldClasses, fieldBorder(invalid), 'px-3 py-2 leading-relaxed resize-y', className)}
      aria-invalid={invalid || undefined}
      {...props}
    />
  )
}
