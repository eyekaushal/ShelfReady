import { AlertTriangle } from 'lucide-react'

import { useDebounce } from '../../hooks/useDebounce'
import { useSkuCheck } from '../../hooks/useLookalikes'

/**
 * Non-blocking warning in the product form: "this looks like an existing SKU".
 * Links open in a new tab, so nothing typed in the form is lost.
 */
export function SkuWarning({ name, brand, excludeId }) {
  const debouncedName = useDebounce(name.trim(), 500)
  const debouncedBrand = useDebounce(brand.trim(), 500)
  const { data: matches } = useSkuCheck({ name: debouncedName, brand: debouncedBrand, exclude: excludeId })

  if (!matches?.length) return null

  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5 text-[13px] text-amber-800" role="status">
      <p className="flex items-center gap-1.5 font-medium">
        <AlertTriangle className="size-4 shrink-0" aria-hidden="true" />
        This looks like an existing SKU
      </p>
      <ul className="mt-1 space-y-0.5 pl-[22px]">
        {matches.map((match) => (
          <li key={match.id} className="truncate">
            <a href={`/products/${match.id}`} target="_blank" rel="noreferrer" className="underline hover:text-amber-900">
              {match.name}
            </a>
            {match.pack_size ? ` · ${match.pack_size}` : ''}
          </li>
        ))}
      </ul>
      <p className="mt-1 pl-[22px] text-xs text-amber-700">You can still save. Add a pack size or variant so a camera can tell them apart.</p>
    </div>
  )
}
