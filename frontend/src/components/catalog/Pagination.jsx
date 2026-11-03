import { ChevronLeft, ChevronRight } from 'lucide-react'

import { cn } from '../../lib/cn'
import { Button } from '../ui/Button'
import { Select } from '../ui/Select'

const PAGE_SIZES = [12, 24, 48]

/** Which page numbers to show: first, last, and a window around the current page. */
function pageNumbers(current, total) {
  const pages = new Set([1, total, current - 1, current, current + 1])
  const sorted = [...pages].filter((page) => page >= 1 && page <= total).sort((a, b) => a - b)
  const withGaps = []
  sorted.forEach((page, index) => {
    if (index > 0 && page - sorted[index - 1] > 1) withGaps.push('…')
    withGaps.push(page)
  })
  return withGaps
}

export function Pagination({ count, page, pageSize, onPageChange, onPageSizeChange }) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  const first = count === 0 ? 0 : (page - 1) * pageSize + 1
  const last = Math.min(count, page * pageSize)

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-gray-200 pt-4 text-[13px] text-gray-500">
      <p className="tabular">
        {count === 0 ? 'No results' : `${first}–${last} of ${count}`}
      </p>

      <div className="flex items-center gap-3">
        <label className="flex items-center gap-2">
          <span className="hidden sm:inline">Per page</span>
          <Select
            value={String(pageSize)}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
            options={PAGE_SIZES.map((size) => ({ value: String(size), label: String(size) }))}
            className="w-20"
            aria-label="Products per page"
          />
        </label>

        <nav className="flex items-center gap-1" aria-label="Pagination">
          <Button size="icon" onClick={() => onPageChange(page - 1)} disabled={page <= 1} aria-label="Previous page">
            <ChevronLeft className="size-4" />
          </Button>
          {pageNumbers(page, totalPages).map((item, index) =>
            item === '…' ? (
              <span key={`gap-${index}`} className="w-6 text-center text-gray-400">
                …
              </span>
            ) : (
              <button
                key={item}
                type="button"
                onClick={() => onPageChange(item)}
                aria-current={item === page ? 'page' : undefined}
                className={cn(
                  'h-8 min-w-8 rounded-md px-2 text-[13px] font-medium tabular transition-colors',
                  item === page ? 'bg-gray-900 text-white' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                )}
              >
                {item}
              </button>
            ),
          )}
          <Button size="icon" onClick={() => onPageChange(page + 1)} disabled={page >= totalPages} aria-label="Next page">
            <ChevronRight className="size-4" />
          </Button>
        </nav>
      </div>
    </div>
  )
}
