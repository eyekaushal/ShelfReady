import { createContext } from 'react'

/** Shared between AuthProvider (writes it) and useAuth (reads it). */
export const AuthContext = createContext(null)
