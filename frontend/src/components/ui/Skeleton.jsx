import { cn } from '../../lib/cn'

/** Grey placeholder block that pulses while data loads. Size it with className. */
export function Skeleton({ className }) {
  return <div className={cn('animate-pulse rounded bg-gray-100', className)} aria-hidden="true" />
}
