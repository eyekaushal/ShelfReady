import { AlertCircle, CheckCircle2, X } from 'lucide-react'
import { useCallback, useMemo, useRef, useState } from 'react'

import { cn } from '../../lib/cn'
import { ToastContext } from './toastContext'

/**
 * Bottom-right toast stack. Each toast disappears after 4 s or when its X is clicked.
 * Read it with useToast() from ./toastContext.js.
 */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const nextId = useRef(1)

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const push = useCallback(
    (tone, message) => {
      const id = nextId.current++
      setToasts((current) => [...current, { id, tone, message }])
      setTimeout(() => dismiss(id), 4000)
    },
    [dismiss],
  )

  const api = useMemo(
    () => ({ success: (message) => push('success', message), error: (message) => push('error', message) }),
    [push],
  )

  return (
    <ToastContext.Provider value={api}>
      {children}
      {/* Bottom centre, so a toast never covers a page's primary action (those sit bottom-right). */}
      <div className="pointer-events-none fixed inset-x-4 bottom-4 z-[60] flex flex-col items-center gap-2 sm:inset-x-0 sm:bottom-6">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="status"
            className={cn(
              'pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-lg border bg-white px-3.5 py-3 text-sm shadow-popover animate-slide-up',
              toast.tone === 'success' ? 'border-gray-200' : 'border-red-200',
            )}
          >
            {toast.tone === 'success' ? (
              <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-green-600" aria-hidden="true" />
            ) : (
              <AlertCircle className="mt-0.5 size-4 shrink-0 text-red-600" aria-hidden="true" />
            )}
            <p className="flex-1 text-gray-800">{toast.message}</p>
            <button
              type="button"
              onClick={() => dismiss(toast.id)}
              className="-mr-1 -mt-0.5 rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
              aria-label="Dismiss"
            >
              <X className="size-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
