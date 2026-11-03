import { SlidersHorizontal } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { cn } from '../../lib/cn'
import { Button } from '../ui/Button'
import { FormField } from '../ui/FormField'
import { Input } from '../ui/Input'
import { Select } from '../ui/Select'

const EMPTY = { brand: '', category: '', min_price: '', max_price: '' }

/**
 * "Filter" button that opens a small panel with brand, category and price range.
 * Edits are kept in a draft until "Apply", so the list doesn't reload on every keystroke.
 */
export function FilterPanel({ filters, activeCount, onApply, brands, categories }) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState(EMPTY)
  const rootRef = useRef(null)

  // Every open starts from what's in the URL right now.
  const toggle = () => {
    if (!open) {
      setDraft({
        brand: filters.brand,
        category: filters.category,
        min_price: filters.min_price,
        max_price: filters.max_price,
      })
    }
    setOpen(!open)
  }

  useEffect(() => {
    if (!open) return undefined
    const onPointer = (event) => !rootRef.current?.contains(event.target) && setOpen(false)
    const onKey = (event) => event.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const set = (key) => (event) => setDraft((current) => ({ ...current, [key]: event.target.value }))

  const priceError =
    draft.min_price && draft.max_price && Number(draft.min_price) > Number(draft.max_price)
      ? 'Min price must be less than or equal to max price.'
      : null

  const apply = (event) => {
    event.preventDefault()
    if (priceError) return
    onApply(draft)
    setOpen(false)
  }

  const reset = () => {
    onApply(EMPTY)
    setOpen(false)
  }

  return (
    <div ref={rootRef} className="relative">
      <Button onClick={toggle} aria-expanded={open} className={cn(activeCount && 'border-gray-300')}>
        <SlidersHorizontal className="size-4 text-gray-500" />
        Filter
        {activeCount ? (
          <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-accent px-1.5 text-[11px] font-semibold text-white">
            {activeCount}
          </span>
        ) : null}
      </Button>

      {open ? (
        <form
          onSubmit={apply}
          className="absolute left-0 z-30 mt-1 w-[calc(100vw-2rem)] max-w-xs rounded-lg border border-gray-200 bg-white p-4 shadow-popover animate-scale-in sm:left-auto sm:right-0 sm:w-80 sm:max-w-none"
        >
          <div className="space-y-4">
            <FormField label="Brand" htmlFor="filter-brand">
              <Select
                id="filter-brand"
                value={draft.brand}
                onChange={set('brand')}
                placeholder="Any brand"
                options={brands.map((brand) => ({ value: brand, label: brand }))}
              />
            </FormField>
            <FormField label="Category" htmlFor="filter-category" hint="Includes its sub-categories.">
              <Select
                id="filter-category"
                value={draft.category}
                onChange={set('category')}
                placeholder="Any category"
                options={categories.map((category) => ({ value: category.slug, label: category.full_path }))}
              />
            </FormField>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Min price" htmlFor="filter-min">
                <Input
                  id="filter-min"
                  type="number"
                  min="0"
                  step="0.01"
                  inputMode="decimal"
                  value={draft.min_price}
                  onChange={set('min_price')}
                  placeholder="0"
                  leading="₹"
                  invalid={Boolean(priceError)}
                />
              </FormField>
              <FormField label="Max price" htmlFor="filter-max">
                <Input
                  id="filter-max"
                  type="number"
                  min="0"
                  step="0.01"
                  inputMode="decimal"
                  value={draft.max_price}
                  onChange={set('max_price')}
                  placeholder="Any"
                  leading="₹"
                  invalid={Boolean(priceError)}
                />
              </FormField>
            </div>
            {priceError ? <p className="-mt-2 text-xs text-red-600">{priceError}</p> : null}
          </div>
          <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-3">
            <Button variant="ghost" size="sm" onClick={reset}>
              Reset
            </Button>
            <Button variant="primary" size="sm" type="submit">
              Apply filters
            </Button>
          </div>
        </form>
      ) : null}
    </div>
  )
}
