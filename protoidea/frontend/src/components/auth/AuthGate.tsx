import type { ReactNode } from 'react'

import { useAuth } from './AuthContext'
import AuthPage from './AuthPage'

export default function AuthGate({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-gray-400">Loading…</div>
  }

  if (!user) return <AuthPage />

  return <>{children}</>
}