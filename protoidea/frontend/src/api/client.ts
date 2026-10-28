import axios, { type AxiosError } from 'axios'

export const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true, // send the httpOnly login cookie with every request
  headers: { 'Content-Type': 'application/json' },
})

// Called when the backend says the session is gone (expired or logged out elsewhere)
let unauthorizedHandler: (() => void) | null = null

export function setUnauthorizedHandler(handler: (() => void) | null) {
  unauthorizedHandler = handler
}

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const url = error.config?.url ?? ''
    if (error.response?.status === 401 && !url.startsWith('/auth/')) {
      unauthorizedHandler?.()
    }
    return Promise.reject(error)
  },
)

/** Turn any backend error into a sentence we can show the user. */
export function getErrorMessage(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) return 'Cannot reach the server. Is the protoidea backend running on port 8000?'
    const detail = (error.response.data as { detail?: unknown } | undefined)?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string; loc?: unknown[] }
      if (first.loc?.includes('password')) return 'Password must be at least 8 characters.'
      if (first.loc?.includes('email')) return 'Please enter a valid email address.'
      if (first.msg) return first.msg
    }
  }
  return fallback
}