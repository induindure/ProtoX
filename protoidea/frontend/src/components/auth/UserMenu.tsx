import toast from 'react-hot-toast'

import { useAuth } from './AuthContext'

export default function UserMenu() {
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
    toast.success('Logged out')
  }

  return (
    <div className="flex items-center gap-3">
      {user && <span className="text-sm text-gray-600 hidden sm:inline">{user.email}</span>}
      <button
        onClick={handleLogout}
        className="text-sm px-3 py-1.5 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 transition"
      >
        Log out
      </button>
    </div>
  )
}