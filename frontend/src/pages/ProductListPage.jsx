import { PackageSearch, Plus } from 'lucide-react'
import { useState } from 'react'

import { useAuth } from '../auth/useAuth'
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
import { useBrands, useCategories } from '../hooks/useCatalogOptions'
import { useProductMutations } from '../hooks/useProductMutations'
import { useProducts } from '../hooks/useProducts'
import { useUrlFilters } from '../hooks/useUrlFilters'
import { cn } from '../lib/cn'

export function ProductListPage() {
  const { filters, setFilters, clearFilters, activeFilterCount } = useUrlFilters()
  const { user } = useAuth()
  const products = useProducts(filters)
  const categories = useCategories()
  const brands = useBrands()
  const { remove } = useProductMutations()
  const toast = useToast()
  const [deleting, setDeleting] = useState(null)

  const page = Number(filters.page)
  const pageSize = Number(filters.page_size)
  const hasAnyFilter = activeFilterCount > 0 || Boolean(filters.search)

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
          <SearchBar value={filters.search} onChange={(search) => setFilters({ search })} />
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
