import { cn } from '../../lib/cn'

/**
 * Label + control + hint/error, laid out the Stripe way.
 * The child control gets `id` from `htmlFor` so the label is clickable.
 * `badge` (e.g. <AiBadge />) sits at the right end of the label row.
 */
export function FormField({ label, htmlFor, hint, error, optional = false, badge, className, children }) {
  return (
    <div className={cn('space-y-1.5', className)}>
      <label htmlFor={htmlFor} className="flex items-baseline gap-2 text-[13px] font-medium text-gray-700">
        {label}
        {optional ? <span className="text-xs font-normal text-gray-400">Optional</span> : null}
        {badge ? <span className="ml-auto self-center">{badge}</span> : null}
      </label>
      {children}
      {error ? (
        <p className="text-xs text-red-600" role="alert">
          {error}
        </p>
      ) : hint ? (
        <p className="text-xs text-gray-500">{hint}</p>
      ) : null}
    </div>
  )
}
