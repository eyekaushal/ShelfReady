import { CopyCheck, LogIn } from 'lucide-react'
import { useLocation, useSearchParams } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Pagination } from '../components/catalog/Pagination'
import { LookalikePairCard } from '../components/lookalikes/LookalikePairCard'
import { STATUS_LABELS } from '../components/lookalikes/statusLabels'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { PageHeader } from '../components/ui/PageHeader'
import { Skeleton } from '../components/ui/Skeleton'
import { useToast } from '../components/ui/toastContext'
import { useLookalikes, useResolveLookalike } from '../hooks/useLookalikes'
import { toApiError } from '../lib/apiError'
import { cn } from '../lib/cn'

const EMPTY_TEXT = {
  unresolved: 'Every look-alike in the catalog has something that tells it apart.',
  resolved_distinct: 'Pairs whose pack size or variant differ will show up here.',
  duplicate: 'Pairs marked as the same SKU listed twice will show up here.',
}

export function LookalikesPage() {
  const [params, setParams] = useSearchParams()
  const status = STATUS_LABELS[params.get('status')] ? params.get('status') : 'unresolved'
  const page = Number(params.get('page')) || 1
  const pageSize = Number(params.get('page_size')) || 12
  const pairs = useLookalikes({ status, page, page_size: pageSize })
  const resolve = useResolveLookalike()
  const toast = useToast()
  const { user, isLoading: authLoading } = useAuth()
  const location = useLocation()

  const onResolve = (id, nextStatus) => {
    resolve.mutate(
      { id, status: nextStatus },
      {
        onSuccess: () => toast.success(nextStatus === 'duplicate' ? 'Marked as duplicate.' : 'Marked as distinct.'),
        onError: (error) => {
          const apiError = toApiError(error)
          toast.error(apiError.fieldErrors().status || apiError.message)
        },
      },
    )
  }

  let body
  if (pairs.isPending) {
    body = (
      <div className="space-y-4" aria-busy="true">
        <Skeleton className="h-56 rounded-lg" />
        <Skeleton className="h-56 rounded-lg" />
      </div>
    )
  } else if (pairs.isError) {
    body = <ErrorState error={pairs.error} onRetry={pairs.refetch} title="Couldn't load look-alikes" />
  } else if (pairs.data.results.length === 0) {
    body = (
      <EmptyState
        icon={CopyCheck}
        title={`No ${STATUS_LABELS[status].label.toLowerCase()} pairs`}
        description={EMPTY_TEXT[status]}
        className="rounded-lg border border-dashed border-gray-200"
      />
    )
  } else {
    body = (
      <div className={cn('space-y-4 transition-opacity duration-150', pairs.isFetching && 'opacity-60')}>
        {pairs.data.results.map((pair) => (
          <LookalikePairCard key={pair.id} pair={pair} onResolve={onResolve} resolving={resolve.isPending} />
        ))}
        <Pagination
          count={pairs.data.count}
          page={page}
          pageSize={pageSize}
          onPageChange={(next) => setParams({ status, page: next, page_size: pageSize })}
          onPageSizeChange={(size) => setParams({ status, page_size: size })}
        />
      </div>
    )
  }

  return (
    <>
      <PageHeader
        title="Look-alikes"
        subtitle="Same-brand products a shelf camera could confuse. Record what tells them apart."
      />
      {!user && !authLoading ? (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-accent-ring bg-accent-soft px-4 py-2.5">
          <p className="text-[13px] text-gray-700">
            Sign in to mark pairs as distinct or duplicate. The sign-in page has a one-click demo account.
          </p>
          <Button to="/login" state={{ from: location }} size="sm" variant="primary">
            <LogIn className="size-3.5" />
            Sign in
          </Button>
        </div>
      ) : null}
      <div className="mb-4 inline-flex h-9 items-center rounded-md border border-gray-200 bg-gray-50 p-0.5" role="group">
        {Object.entries(STATUS_LABELS).map(([value, { label }]) => (
          <button
            key={value}
            type="button"
            onClick={() => setParams({ status: value })}
            aria-pressed={status === value}
            className={cn(
              'flex h-full items-center rounded px-3 text-[13px] font-medium transition-colors',
              status === value
                ? 'bg-white text-gray-900 shadow-[0_1px_2px_rgb(0_0_0/0.08),0_0_0_1px_rgb(0_0_0/0.04)]'
                : 'text-gray-500 hover:text-gray-900',
            )}
          >
            {label}
          </button>
        ))}
      </div>
      {body}
    </>
  )
}
