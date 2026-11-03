import { cn } from '../../lib/cn'

const tones = {
  gray: 'bg-gray-100 text-gray-700',
  blue: 'bg-blue-50 text-blue-700',
  green: 'bg-green-50 text-green-700',
  amber: 'bg-amber-50 text-amber-700',
  red: 'bg-red-50 text-red-700',
  outline: 'border border-gray-200 text-gray-600 bg-white',
}

const dots = {
  gray: 'bg-gray-400',
  blue: 'bg-blue-500',
  green: 'bg-green-500',
  amber: 'bg-amber-500',
  red: 'bg-red-500',
  outline: 'bg-gray-400',
}

/** Small status label. `dot` adds the Linear-style coloured dot in front. */
export function Badge({ tone = 'gray', dot = false, className, children }) {
  return (
    <span
      className={cn(
        'inline-flex h-6 items-center gap-1.5 rounded-md px-2 text-xs font-medium whitespace-nowrap',
        tones[tone],
        className,
      )}
    >
      {dot ? <span className={cn('size-1.5 rounded-full', dots[tone])} aria-hidden="true" /> : null}
      {children}
    </span>
  )
}
