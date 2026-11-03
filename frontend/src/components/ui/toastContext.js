import { createContext, useContext } from 'react'

export const ToastContext = createContext(null)

/** const toast = useToast(); toast.success("Saved"); toast.error("Nope") */
export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used inside <ToastProvider>')
  return context
}
