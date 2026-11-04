import { useMutation } from '@tanstack/react-query'
import { PackageSearch, Plus, Sparkles } from 'lucide-react'
import { useState } from 'react'

import { aiApi } from '../api/aiApi'
import { useAuth } from '../auth/useAuth'
import { AiSearchNotice } from '../components/catalog/AiSearchNotice'
import { AskAiPanel } from '../components/catalog/AskAiPanel'
import { FilterChips } from '../components/catalog/FilterChips'
import { FilterPanel } from '../components/catalog/FilterPanel'
import { Pagination } from '../components/catalog/Pagination'
import { ProductGrid } from '../components/catalog/ProductGrid'
import { ProductListSkeleton } from '../components/catalog/ProductListSkeleton'
import { ProductTable } from '../components/catalog/ProductTable'
import { SearchBar } from '../components/catalog/SearchBar'
import { SortMenu } from '../components/catalog/SortMenu'
import { ViewToggle } from '../components/catalog/ViewToggle'
import { Button } from '../components/ui/Button'
import { ConfirmModal } from '../components/ui/ConfirmModal'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { PageHeader } from '../components/ui/PageHeader'
import { useToast } from '../components/ui/toastContext'
import { useAiStatus } from '../hooks/useAiStatus'
import { useBrands, useCategories } from '../hooks/useCatalogOptions'
import { useProductMutations } from '../hooks/useProductMutations'
import { useProducts } from '../hooks/useProducts'
import { useUrlFilters } from '../hooks/useUrlFilters'
import { toApiError } from '../lib/apiError'
import { cn } from '../lib/cn'

/** Why AI search fell back to keywords, in plain words. */
function fallbackMessage(error) {
  if (error.status === 429) return "You've used AI search a lot this hour."
  if (error.code === 'ai_not_configured') return 'AI search is unavailable right now.'
  return "AI search couldn't understand that right now."
}

export function ProductListPage() {
  const { filters, setFilters, clearFilters, activeFilterCount } = useUrlFilters()
  const { user } = useAuth()
  const products = useProducts(filters)
  const categories = useCategories()
  const brands = useBrands()
  const { remove } = useProductMutations()
  const toast = useToast()
  const [deleting, setDeleting] = useState(null)
  const ai = useAiStatus()
  const parseSearch = useMutation({ mutationFn: aiApi.parseSearch })
  const [aiNotice, setAiNotice] = useState(null) // {kind: 'ai' | 'fallback', query, message?}
  const [aiOpen, setAiOpen] = useState(false)

  /**
   * AI search: the sentence becomes filters (already whitelisted by the server), which go into
   * the URL like manual filters, so the normal product list does the actual search.
   * If AI fails, we fall back to a plain keyword search for the same words.
   */
  const askAi = (query) => {
    parseSearch.mutate(query, {
      onSuccess: ({ filters: parsed }) => {
        setFilters({
          search: parsed.search,
          brand: parsed.brand,
          category: parsed.category,
          min_price: parsed.min_price ?? '',
          max_price: parsed.max_price ?? '',
          ordering: parsed.ordering,
        })
        setAiNotice({ kind: 'ai', query })
      },
      onError: (error) => {
        setFilters({ search: query, brand: '', category: '', min_price: '', max_price: '', ordering: '' })
        setAiNotice({ kind: 'fallback', query, message: fallbackMessage(toApiError(error)) })
      },
    })
  }

  const page = Number(filters.page)
  const pageSize = Number(filters.page_size)
  const hasAnyFilter = activeFilterCount > 0 || Boolean(filters.search)
  // Hide the AI note once the user has cleared everything it set.
  const showAiNotice = aiNotice && (hasAnyFilter || filters.ordering !== '-created_at')

  const confirmDelete = () => {
    remove.mutate(deleting.id, {
      onSuccess: () => {
        toast.success(`Deleted “${deleting.name}”.`)
        setDeleting(null)
      },
      onError: (error) => toast.error(error.message),
    })
  }

  let body
  if (products.isPending) {
    body = <ProductListSkeleton view={filters.view} rows={Math.min(pageSize, 12)} />
  } else if (products.isError && products.error.status === 404 && page > 1) {
    // A shared link to a page that no longer exists (e.g. after deletions).
    body = (
      <EmptyState
        icon={PackageSearch}
        title="This page doesn't exist"
        description="The catalog has fewer pages than this link points to."
        action={<Button onClick={() => setFilters({ page: 1 })}>Go to the first page</Button>}
        className="rounded-lg border border-dashed border-gray-200"
      />
    )
  } else if (products.isError) {
    body = <ErrorState error={products.error} onRetry={products.refetch} title="Couldn't load the catalog" />
  } else if (products.data.results.length === 0) {
    body = (
      <EmptyState
        icon={PackageSearch}
        title={hasAnyFilter ? 'No products match' : 'The catalog is empty'}
        description={
          hasAnyFilter
            ? 'Try different words, or remove a filter to widen the search.'
            : 'Add the first product to start building a recognition-ready SKU master.'
        }
        action={
          hasAnyFilter ? (
            <Button onClick={clearFilters}>Clear filters</Button>
          ) : (
            <Button variant="primary" to={user ? '/products/new' : '/login'}>
              <Plus className="size-4" />
              Add product
            </Button>
          )
        }
        className="rounded-lg border border-dashed border-gray-200"
      />
    )
  } else {
    body = (
      <div className={cn('space-y-4 transition-opacity duration-150', products.isFetching && 'opacity-60')}>
        {filters.view === 'grid' ? (
          <ProductGrid products={products.data.results} />
        ) : (
          <ProductTable products={products.data.results} onDelete={setDeleting} />
        )}
        <Pagination
          count={products.data.count}
          page={page}
          pageSize={pageSize}
          onPageChange={(next) => setFilters({ page: next })}
          onPageSizeChange={(size) => setFilters({ page_size: size })}
        />
      </div>
    )
  }

  return (
    <>
      <PageHeader
        title="Catalog"
        subtitle={
          products.data ? `${products.data.count} products in the SKU master` : 'Recognition-ready SKU master'
        }
        actions={
          <Button variant="primary" to={user ? '/products/new' : '/login'}>
            <Plus className="size-4" />
            Add product
          </Button>
        }
      />

      <div className="mb-4 space-y-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex w-full items-center gap-2 sm:max-w-lg">
            <SearchBar value={filters.search} onChange={(search) => setFilters({ search })} />
            {ai.enabled ? (
              <button
                type="button"
                onClick={() => setAiOpen(!aiOpen)}
                aria-expanded={aiOpen}
                className={cn(
                  'inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md border px-3 text-sm font-medium transition-colors duration-150',
                  aiOpen
                    ? 'border-accent-ring bg-accent-soft text-accent-hover'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50',
                )}
              >
                <Sparkles className={cn('size-4', aiOpen ? 'text-accent' : 'text-gray-500')} aria-hidden="true" />
                Ask AI
              </button>
            ) : null}
          </div>
          <div className="flex items-center gap-2">
            <FilterPanel
              filters={filters}
              activeCount={activeFilterCount}
              onApply={setFilters}
              brands={brands.data || []}
              categories={categories.data || []}
            />
            <SortMenu value={filters.ordering} onChange={(ordering) => setFilters({ ordering })} />
            <ViewToggle value={filters.view} onChange={(view) => setFilters({ view, page: filters.page })} />
          </div>
        </div>
        {aiOpen ? <AskAiPanel onAsk={askAi} asking={parseSearch.isPending} onClose={() => setAiOpen(false)} /> : null}
        <AiSearchNotice notice={showAiNotice ? aiNotice : null} onDismiss={() => setAiNotice(null)} />
        <FilterChips
          filters={filters}
          setFilters={setFilters}
          clearFilters={clearFilters}
          categories={categories.data || []}
        />
      </div>

      {body}

      <ConfirmModal
        open={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={confirmDelete}
        loading={remove.isPending}
        danger
        title="Delete this product?"
        description={
          deleting
            ? `“${deleting.name}” will be removed from the catalog. A shelf camera would no longer be able to recognise it.`
            : ''
        }
        confirmLabel="Delete product"
      />
    </>
  )
}
