import { cn } from '../../lib/cn'

/** Stripe-style empty state: soft icon circle, one bold line, one grey line, an action. */
export function EmptyState({ icon: Icon, title, description, action, className }) {
  return (
    <div className={cn('flex flex-col items-center px-6 py-16 text-center', className)}>
      {Icon ? (
        <div className="mb-4 flex size-11 items-center justify-center rounded-full bg-gray-100 text-gray-500">
          <Icon className="size-5" aria-hidden="true" />
        </div>
      ) : null}
      <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
      {description ? <p className="mt-1 max-w-sm text-sm text-gray-500">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  )
}
