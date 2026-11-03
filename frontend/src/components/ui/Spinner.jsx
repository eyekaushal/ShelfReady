import { Loader2 } from 'lucide-react'

export function Spinner({ className = 'size-5' }) {
  return <Loader2 className={`animate-spin text-gray-400 ${className}`} aria-label="Loading" />
}

/** Full-height spinner for whole-page waits (e.g. checking the session on load). */
export function PageSpinner() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <Spinner />
    </div>
  )
}
