import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { getMe, logout as apiLogout, type AuthUser } from '../../api/auth'
import { setUnauthorizedHandler } from '../../api/client'

interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  signIn: (user: AuthUser) => void
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  // Clear cached data whenever the person changes, so nobody sees someone else's history
  const signIn = useCallback((nextUser: AuthUser) => {
    queryClient.clear()
    setUser(nextUser)
  }, [queryClient])

  const signOutLocally = useCallback(() => {
    queryClient.clear()
    setUser(null)
  }, [queryClient])

  useEffect(() => {
    // Is there already a valid login cookie? (e.g. after a page refresh)
    getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))

    setUnauthorizedHandler(signOutLocally)
    return () => setUnauthorizedHandler(null)
  }, [signOutLocally])

  const logout = useCallback(async () => {
    try {
      await apiLogout()
    } finally {
      signOutLocally()
    }
  }, [signOutLocally])

  return (
    <AuthContext.Provider value={{ user, loading, signIn, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}