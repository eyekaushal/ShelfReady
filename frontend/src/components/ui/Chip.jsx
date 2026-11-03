import { XCircle } from 'lucide-react'

/**
 * Removable filter chip, Stripe style: (x) Label | Value.
 * The whole chip is one button so it's an easy target on mobile.
 */
export function Chip({ label, value, onRemove }) {
  return (
    <button
      type="button"
      onClick={onRemove}
      aria-label={`Remove filter ${label}: ${value}`}
      className="group inline-flex h-7 items-center gap-1.5 rounded-full border border-gray-200 bg-white pl-1.5 pr-2.5 text-xs transition-colors hover:border-gray-300 hover:bg-gray-50"
    >
      <XCircle className="size-3.5 text-gray-400 transition-colors group-hover:text-gray-700" aria-hidden="true" />
      <span className="text-gray-500">{label}</span>
      <span className="h-3 w-px bg-gray-200" aria-hidden="true" />
      <span className="font-medium text-gray-800">{value}</span>
    </button>
  )
}
