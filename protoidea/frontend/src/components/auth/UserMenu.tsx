import toast from 'react-hot-toast'

import { useAuth } from './AuthContext'

export default function UserMenu() {
  const { user, logout } = useAuth()
  const initials = (user?.email ?? '?').slice(0, 2).toUpperCase()

  const handleLogout = async () => {
    await logout()
    toast.success('Logged out')
  }

  return (
    <>
      {user && (
        <span
          title={user.email}
          style={{ display: 'flex', alignItems: 'center', gap: 8, minHeight: 44, padding: '0 12px 0 6px', border: '1px solid var(--border)', borderRadius: 10, background: 'var(--surface)' }}
        >
          <span style={{ width: 30, height: 30, borderRadius: 999, background: 'var(--accent-soft)', color: 'var(--accent-text)', fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {initials}
          </span>
          <span className="px-small" style={{ fontWeight: 500, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {user.email}
          </span>
        </span>
      )}
      <button type="button" onClick={handleLogout} className="px-icon-btn" aria-label="Log out" title="Log out">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
        </svg>
      </button>
    </>
  )
}
