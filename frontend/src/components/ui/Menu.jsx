import { Check } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { cn } from '../../lib/cn'

/**
 * Dropdown menu. `trigger` is a function (open) => button; `items` is a list of
 * {label, icon, onSelect, selected, danger}. Closes on outside click, Escape and selection.
 */
export function Menu({ trigger, items, align = 'right', className }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)

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

  return (
    <div ref={rootRef} className={cn('relative inline-block', className)}>
      <div onClick={() => setOpen((value) => !value)}>{trigger(open)}</div>
      {open ? (
        <div
          role="menu"
          className={cn(
            'absolute z-30 mt-1 min-w-44 rounded-lg border border-gray-200 bg-white p-1 shadow-popover animate-scale-in',
            align === 'right' ? 'right-0' : 'left-0',
          )}
        >
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              role="menuitem"
              onClick={() => {
                setOpen(false)
                item.onSelect()
              }}
              className={cn(
                'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-[13px] transition-colors',
                item.danger ? 'text-red-600 hover:bg-red-50' : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900',
              )}
            >
              {item.icon ? <item.icon className="size-4 text-gray-400" aria-hidden="true" /> : null}
              <span className="flex-1">{item.label}</span>
              {item.selected ? <Check className="size-4 text-accent" aria-hidden="true" /> : null}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}
