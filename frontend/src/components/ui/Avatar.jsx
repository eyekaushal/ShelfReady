import { cn } from '../../lib/cn'
import { initials } from '../../lib/format'

/** Circle with the first letter of the name. Same look as Attio's user avatars. */
export function Avatar({ name, className }) {
  return (
    <span
      className={cn(
        'inline-flex size-6 shrink-0 items-center justify-center rounded-full bg-accent-soft text-[11px] font-semibold text-accent',
        className,
      )}
      title={name}
    >
      {initials(name)}
    </span>
  )
}
