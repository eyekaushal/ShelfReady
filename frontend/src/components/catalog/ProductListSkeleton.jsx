import { Skeleton } from '../ui/Skeleton'

/** Placeholders shaped like the real table rows or cards, so nothing jumps when data arrives. */
export function ProductListSkeleton({ view, rows = 12 }) {
  const items = Array.from({ length: rows }, (_, index) => index)

  if (view === 'grid') {
    return (
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4" aria-busy="true">
        {items.map((item) => (
          <div key={item} className="rounded-lg border border-gray-200 p-3">
            <Skeleton className="aspect-square w-full" />
            <Skeleton className="mt-3 h-3 w-1/3" />
            <Skeleton className="mt-2 h-4 w-4/5" />
            <div className="mt-4 flex justify-between">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="size-4 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200" aria-busy="true">
      <div className="h-10 border-b border-gray-200 bg-gray-50/80" />
      <div className="divide-y divide-gray-100">
        {items.map((item) => (
          <div key={item} className="flex items-center gap-3 px-3 py-2.5">
            <Skeleton className="size-9 rounded-md" />
            <div className="flex-1 space-y-1.5">
              <Skeleton className="h-3.5 w-48 max-w-[50%]" />
              <Skeleton className="h-3 w-24" />
            </div>
            <Skeleton className="h-6 w-20 rounded-md" />
            <Skeleton className="hidden h-3.5 w-28 md:block" />
            <Skeleton className="h-3.5 w-16" />
            <Skeleton className="size-4 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  )
}
