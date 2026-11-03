import { MoreHorizontal, Pencil, Trash2 } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

import { canEditProduct, useAuth } from '../../auth/useAuth'
import { formatPrice, leafName, timeAgo } from '../../lib/format'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Menu } from '../ui/Menu'
import { ProductImage } from './ProductImage'
import { ReadinessRing } from './ReadinessRing'
import { isScored } from '../../lib/readiness'

const headClasses = 'px-3 py-2.5 text-left text-[12px] font-medium text-gray-500 whitespace-nowrap'

/** Dense list view, Linear/Attio style. Clicking a row opens the product. */
export function ProductTable({ products, onDelete }) {
  const { user } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full min-w-[640px] border-collapse">
        <thead className="border-b border-gray-200 bg-gray-50/80">
          <tr>
            <th className={headClasses}>Product</th>
            <th className={headClasses}>Brand</th>
            <th className={`${headClasses} hidden md:table-cell`}>Category</th>
            <th className={`${headClasses} text-right`}>Price</th>
            <th className={headClasses}>Readiness</th>
            <th className={`${headClasses} hidden lg:table-cell`}>Added</th>
            <th className={`${headClasses} w-10`}>
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {products.map((product) => {
            const editable = canEditProduct(user, product)
            const details = [product.pack_size, product.variant].filter(Boolean).join(' · ')
            return (
              <tr
                key={product.id}
                onClick={() => navigate(`/products/${product.id}`)}
                className="group cursor-pointer transition-colors hover:bg-gray-50"
              >
                <td className="px-3 py-2">
                  <div className="flex items-center gap-3">
                    <ProductImage src={product.image_url} alt="" className="size-9" iconClassName="size-4" />
                    <div className="min-w-0">
                      <Link
                        to={`/products/${product.id}`}
                        onClick={(event) => event.stopPropagation()}
                        className="block truncate text-[13px] font-medium text-gray-900 group-hover:text-accent"
                      >
                        {product.name}
                      </Link>
                      {details ? <p className="truncate text-xs text-gray-500">{details}</p> : null}
                    </div>
                  </div>
                </td>
                <td className="px-3 py-2">
                  <Badge tone="outline">{product.brand}</Badge>
                </td>
                <td className="hidden px-3 py-2 text-[13px] text-gray-600 md:table-cell">
                  {leafName(product.category_detail?.full_path)}
                </td>
                <td className="px-3 py-2 text-right text-[13px] font-medium tabular text-gray-900">
                  {formatPrice(product.price)}
                </td>
                <td className="px-3 py-2">
                  <ReadinessRing score={product.readiness_score} scored={isScored(product)} />
                </td>
                <td className="hidden px-3 py-2 text-[13px] text-gray-500 lg:table-cell">{timeAgo(product.created_at)}</td>
                <td className="px-2 py-2" onClick={(event) => event.stopPropagation()}>
                  {editable ? (
                    <Menu
                      trigger={(open) => (
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={`Actions for ${product.name}`}
                          className={open ? 'bg-gray-100' : 'opacity-0 group-hover:opacity-100 focus-visible:opacity-100'}
                        >
                          <MoreHorizontal className="size-4" />
                        </Button>
                      )}
                      items={[
                        { label: 'Edit', icon: Pencil, onSelect: () => navigate(`/products/${product.id}/edit`) },
                        { label: 'Delete', icon: Trash2, danger: true, onSelect: () => onDelete(product) },
                      ]}
                    />
                  ) : null}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
