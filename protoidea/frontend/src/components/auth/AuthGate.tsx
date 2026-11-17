import type { ReactNode } from 'react'

import { useAuth } from './AuthContext'
import AuthPage from './AuthPage'

export default function AuthGate({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="px-page" style={{ alignItems: 'center', justifyContent: 'center', gap: 10, flexDirection: 'row', color: 'var(--muted)' }}>
        <span className="px-spinner" /> Loading…
      </div>
    )
  }

  if (!user) return <AuthPage />

  return <>{children}</>
}
