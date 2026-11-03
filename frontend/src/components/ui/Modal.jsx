import { X } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'

import { cn } from '../../lib/cn'
import { Button } from './Button'

/**
 * Centered dialog. Closes on Escape, on the overlay click and on the X button.
 * Rendered in a portal so it's never clipped by a scrolling parent.
 */
export function Modal({ open, onClose, title, description, children, footer, size = 'md' }) {
  const panelRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const onKey = (event) => event.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden' // no background scroll while open
    panelRef.current?.focus()
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-gray-900/40 p-4 backdrop-blur-[2px] animate-fade-in sm:items-center"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className={cn(
          'w-full rounded-xl bg-white shadow-modal outline-none animate-scale-in',
          size === 'md' ? 'max-w-md' : 'max-w-2xl',
        )}
      >
        <div className="flex items-start justify-between gap-4 px-5 pt-5">
          <div>
            <h2 id="modal-title" className="text-base font-semibold text-gray-900">
              {title}
            </h2>
            {description ? <p className="mt-1 text-sm text-gray-500">{description}</p> : null}
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close" className="-mr-2 -mt-1">
            <X className="size-4" />
          </Button>
        </div>
        {children ? <div className="px-5 py-4">{children}</div> : null}
        {footer ? <div className="flex justify-end gap-2 border-t border-gray-100 px-5 py-3.5">{footer}</div> : null}
      </div>
    </div>,
    document.body,
  )
}
