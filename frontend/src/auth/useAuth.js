import { useContext } from 'react'

import { AuthContext } from './authContext'

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}

/** Can this user edit or delete this product? Mirrors IsOwnerOrStaff on the backend. */
export function canEditProduct(user, product) {
  if (!user || !product) return false
  return user.is_staff || product.created_by === user.username
}
