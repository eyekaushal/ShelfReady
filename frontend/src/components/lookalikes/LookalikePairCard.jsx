import { Check, Copy, Pencil } from 'lucide-react'
import { Link } from 'react-router-dom'

import { canEditProduct, useAuth } from '../../auth/useAuth'
import { cn } from '../../lib/cn'
import { formatPrice } from '../../lib/format'
import { ProductImage } from '../catalog/ProductImage'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { STATUS_LABELS } from './statusLabels'

/** One attribute row. Green when it tells the pair apart, amber when it's missing. */
function Attribute({ label, value, differs }) {
  return (
    <div className="flex items-baseline justify-between gap-3 text-[13px]">
      <dt className="text-gray-500">{label}</dt>
      <dd className={cn('truncate font-medium', differs ? 'text-green-700' : value ? 'text-gray-900' : 'text-amber-600')}>
        {value || 'Not set'}
      </dd>
    </div>
  )
}

function ProductSide({ product, differing, editable }) {
  return (
    <div className="min-w-0 flex-1 p-4">
      <div className="flex gap-3">
        <ProductImage src={product.image_url} alt={product.name} className="size-20" iconClassName="size-5" />
        <div className="min-w-0">
          <p className="text-xs text-gray-500">{product.brand}</p>
          <Link to={`/products/${product.id}`} className="line-clamp-2 text-sm font-medium text-gray-900 hover:text-accent">
            {product.name}
          </Link>
          <p className="mt-0.5 text-[13px] tabular text-gray-600">{formatPrice(product.price)}</p>
        </div>
      </div>
      <dl className="mt-3 space-y-1">
        <Attribute label="Pack size" value={product.pack_size} differs={differing.includes('pack_size')} />
        <Attribute label="Variant" value={product.variant} differs={differing.includes('variant')} />
      </dl>
      {editable ? (
        <Button to={`/products/${product.id}/edit`} size="sm" className="mt-3">
          <Pencil className="size-3.5 text-gray-500" />
          Edit
        </Button>
      ) : null}
    </div>
  )
}

/** Why these two were flagged, in plain words. */
function reason(pair) {
  const parts = []
  if (pair.text_similarity !== null) parts.push(`Names ${Math.round(pair.text_similarity * 100)}% alike`)
  if (pair.image_distance !== null) parts.push(`photos ${pair.image_distance} of 64 bits apart`)
  return parts.join(' · ')
}

/**
 * Two look-alike products side by side. Pack size and variant are what a camera team needs to
 * tell them apart, so those are the rows on show.
 */
export function LookalikePairCard({ pair, onResolve, resolving }) {
  const { user } = useAuth()
  const { product_a: first, product_b: second, differing_attributes: differing } = pair
  const canEditEither = canEditProduct(user, first) || canEditProduct(user, second)
  const status = STATUS_LABELS[pair.status]

  return (
    <article className="rounded-lg border border-gray-200 bg-white">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 px-4 py-2.5">
        <p className="text-xs text-gray-500">{reason(pair)}</p>
        <Badge tone={status.tone} dot>
          {status.label}
          {pair.resolved_by ? ` · by ${pair.resolved_by}` : pair.status === 'resolved_distinct' ? ' · automatic' : ''}
        </Badge>
      </header>

      <div className="flex flex-col divide-y divide-gray-100 sm:flex-row sm:divide-x sm:divide-y-0">
        <ProductSide product={first} differing={differing} editable={canEditProduct(user, first)} />
        <ProductSide product={second} differing={differing} editable={canEditProduct(user, second)} />
      </div>

      {user && pair.status === 'unresolved' ? (
        <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 px-4 py-2.5">
          <p className="text-xs text-gray-500">
            {differing.length
              ? 'These differ now. Mark them as distinct.'
              : canEditEither
                ? 'To mark as distinct, first fill in a pack size or variant that differs.'
                : 'Marking as distinct needs a differing pack size or variant, which only the creator or staff can add.'}
          </p>
          <div className="flex items-center gap-2">
            <Button size="sm" onClick={() => onResolve(pair.id, 'duplicate')} disabled={resolving}>
              <Copy className="size-3.5 text-gray-500" />
              Mark as duplicate
            </Button>
            <Button
              size="sm"
              variant="primary"
              onClick={() => onResolve(pair.id, 'resolved_distinct')}
              disabled={resolving || differing.length === 0}
            >
              <Check className="size-3.5" />
              Mark as distinct
            </Button>
          </div>
        </footer>
      ) : null}
    </article>
  )
}
