import { Link } from 'react-router-dom'

import { useLookalikes } from '../../hooks/useLookalikes'
import { ProductImage } from '../catalog/ProductImage'
import { Badge } from '../ui/Badge'
import { STATUS_LABELS } from './statusLabels'

/** The "Possible look-alikes" box on a product page. Shows nothing when there are none. */
export function PossibleLookalikes({ productId }) {
  const { data } = useLookalikes({ product: productId, page_size: 6 })
  if (!data?.results.length) return null

  return (
    <section>
      <h2 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Possible look-alikes</h2>
      <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
        {data.results.map((pair) => {
          const other = pair.product_a.id === Number(productId) ? pair.product_b : pair.product_a
          const status = STATUS_LABELS[pair.status]
          return (
            <li key={pair.id} className="flex items-center gap-3 px-3 py-2">
              <ProductImage src={other.image_url} alt="" className="size-9" iconClassName="size-4" />
              <div className="min-w-0 flex-1">
                <Link to={`/products/${other.id}`} className="block truncate text-[13px] font-medium text-gray-900 hover:text-accent">
                  {other.name}
                </Link>
                <p className="truncate text-xs text-gray-500">
                  {[other.pack_size, other.variant].filter(Boolean).join(' · ') || 'No pack size or variant'}
                </p>
              </div>
              <Badge tone={status.tone} dot>
                {status.label}
              </Badge>
            </li>
          )
        })}
      </ul>
      <Link to="/lookalikes" className="mt-2 inline-block text-xs font-medium text-accent hover:text-accent-hover">
        Review all look-alikes
      </Link>
    </section>
  )
}
