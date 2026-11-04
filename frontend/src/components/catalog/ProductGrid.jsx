import { Link } from 'react-router-dom'

import { formatPrice } from '../../lib/format'
import { ProductImage } from './ProductImage'

/** Card view with the pack shot front and centre. */
export function ProductGrid({ products }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {products.map((product) => (
        <Link
          key={product.id}
          to={`/products/${product.id}`}
          className="group flex flex-col rounded-lg border border-gray-200 bg-white p-3 transition-[border-color,box-shadow] duration-150 hover:border-gray-300 hover:shadow-[0_2px_8px_rgb(0_0_0/0.06)]"
        >
          <ProductImage src={product.image_url} alt={product.name} className="aspect-square w-full" iconClassName="size-7" />
          <div className="mt-3 flex flex-1 flex-col">
            <p className="text-[11px] font-medium uppercase tracking-wide text-gray-500">{product.brand}</p>
            <h3 className="mt-0.5 line-clamp-2 text-[13px] font-medium leading-snug text-gray-900 group-hover:text-accent">
              {product.name}
            </h3>
            {product.pack_size ? <p className="mt-0.5 text-xs text-gray-500">{product.pack_size}</p> : null}
            <p className="mt-auto pt-3 text-[13px] font-semibold tabular text-gray-900">{formatPrice(product.price)}</p>
          </div>
        </Link>
      ))}
    </div>
  )
}
