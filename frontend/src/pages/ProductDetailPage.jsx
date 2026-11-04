import { ExternalLink, PackageX, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { canEditProduct, useAuth } from '../auth/useAuth'
import { ProductImage } from '../components/catalog/ProductImage'
import { PossibleLookalikes } from '../components/lookalikes/PossibleLookalikes'
import { ReadinessRing } from '../components/catalog/ReadinessRing'
import { isScored } from '../lib/readiness'
import { Avatar } from '../components/ui/Avatar'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { ConfirmModal } from '../components/ui/ConfirmModal'
import { DescriptionList } from '../components/ui/DescriptionList'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { PageHeader } from '../components/ui/PageHeader'
import { Skeleton } from '../components/ui/Skeleton'
import { useToast } from '../components/ui/toastContext'
import { useProductMutations } from '../hooks/useProductMutations'
import { useProduct } from '../hooks/useProducts'
import { formatDate, formatPrice } from '../lib/format'

/** One of the "Highlights" tiles under the title. */
function Highlight({ label, value, missing = false, children }) {
  return (
    <div className="rounded-lg border border-gray-200 px-4 py-3">
      <p className="text-xs text-gray-500">{label}</p>
      <div className="mt-1 text-[15px] font-semibold tabular text-gray-900">
        {children || (value ? value : <span className={missing ? 'text-amber-600' : 'text-gray-400'}>{missing ? 'Not set' : '—'}</span>)}
      </div>
    </div>
  )
}

function DetailSkeleton() {
  return (
    <div aria-busy="true">
      <Skeleton className="mb-3 h-3.5 w-32" />
      <Skeleton className="h-7 w-72 max-w-full" />
      <Skeleton className="mt-2 h-4 w-48" />
      <div className="mt-8 grid gap-8 lg:grid-cols-[320px_1fr]">
        <Skeleton className="aspect-square w-full rounded-lg" />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-[66px] rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  )
}

export function ProductDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const product = useProduct(id)
  const { remove } = useProductMutations()
  const toast = useToast()
  const [confirmOpen, setConfirmOpen] = useState(false)

  if (product.isPending) return <DetailSkeleton />

  if (product.isError) {
    if (product.error.status === 404) {
      return (
        <EmptyState
          icon={PackageX}
          title="Product not found"
          description="It may have been deleted, or the link is wrong."
          action={<Button to="/">Back to catalog</Button>}
        />
      )
    }
    return <ErrorState error={product.error} onRetry={product.refetch} title="Couldn't load this product" />
  }

  const item = product.data
  const editable = canEditProduct(user, item)
  const scored = isScored(item)

  const confirmDelete = () => {
    remove.mutate(item.id, {
      onSuccess: () => {
        toast.success(`Deleted “${item.name}”.`)
        navigate('/', { replace: true })
      },
      onError: (error) => {
        toast.error(error.message)
        setConfirmOpen(false)
      },
    })
  }

  return (
    <div className="animate-fade-in">
      <PageHeader
        breadcrumb={[{ label: 'Catalog', to: '/' }, { label: item.name }]}
        title={item.name}
        subtitle={
          <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <Badge tone="outline">{item.brand}</Badge>
            <span className="text-gray-400">·</span>
            <span>{item.category_detail?.full_path}</span>
          </span>
        }
        actions={
          editable ? (
            <>
              <Button to={`/products/${item.id}/edit`}>
                <Pencil className="size-4 text-gray-500" />
                Edit
              </Button>
              <Button onClick={() => setConfirmOpen(true)} className="text-red-600 hover:bg-red-50 hover:border-red-200">
                <Trash2 className="size-4" />
                Delete
              </Button>
            </>
          ) : null
        }
      />

      <div className="grid gap-8 lg:grid-cols-[320px_1fr]">
        <div>
          <ProductImage src={item.image_url} alt={item.name} className="aspect-square w-full rounded-lg" iconClassName="size-10" />
          {item.image_url ? (
            <a
              href={item.image_url}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-900"
            >
              Open original image
              <ExternalLink className="size-3" aria-hidden="true" />
            </a>
          ) : null}
        </div>

        <div className="space-y-8">
          <section>
            <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-gray-400">Highlights</h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <Highlight label="Price" value={formatPrice(item.price)} />
              <Highlight label="Pack size" value={item.pack_size} missing />
              <Highlight label="Variant" value={item.variant} missing />
              <Highlight label="GTIN" value={item.gtin ? <span className="font-mono text-sm">{item.gtin}</span> : ''} />
              <Highlight label="Category" value={item.category_detail?.name} />
              <Highlight label="Recognition readiness">
                <span className="flex items-center gap-2">
                  <ReadinessRing score={item.readiness_score} scored={scored} size={22} showLabel={false} />
                  {scored ? `${item.readiness_score}%` : <span className="text-sm font-normal text-gray-400">Not scored yet</span>}
                </span>
              </Highlight>
            </div>
          </section>

          <section>
            <h2 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Description</h2>
            <p className="max-w-prose text-sm leading-relaxed text-gray-700">{item.description}</p>
            {item.tags?.length ? (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {item.tags.map((tag) => (
                  <Badge key={tag} tone="gray">
                    {tag}
                  </Badge>
                ))}
              </div>
            ) : null}
          </section>

          <PossibleLookalikes productId={item.id} />

          <section className="rounded-lg border border-gray-200 px-4 py-1">
            <DescriptionList
              items={[
                { label: 'Brand', value: item.brand },
                { label: 'Category', value: item.category_detail?.full_path },
                { label: 'GTIN', value: item.gtin ? <span className="font-mono">{item.gtin}</span> : '' },
                { label: 'Pack size', value: item.pack_size },
                { label: 'Variant', value: item.variant },
                {
                  label: 'Image URL',
                  value: item.image_url ? (
                    <a href={item.image_url} target="_blank" rel="noreferrer" className="break-all text-accent hover:underline">
                      {item.image_url}
                    </a>
                  ) : '',
                },
                {
                  label: 'Created by',
                  value: item.created_by ? (
                    <span className="inline-flex items-center gap-1.5">
                      <Avatar name={item.created_by} className="size-5 text-[10px]" />
                      {item.created_by}
                    </span>
                  ) : '',
                },
                { label: 'Created', value: formatDate(item.created_at) },
                { label: 'Updated', value: formatDate(item.updated_at) },
                { label: 'Product ID', value: <span className="font-mono text-gray-500">#{item.id}</span> },
              ]}
            />
          </section>
        </div>
      </div>

      <ConfirmModal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={confirmDelete}
        loading={remove.isPending}
        danger
        title="Delete this product?"
        description={`“${item.name}” will be removed from the catalog. A shelf camera would no longer be able to recognise it.`}
        confirmLabel="Delete product"
      />
    </div>
  )
}
