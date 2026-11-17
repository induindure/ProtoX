// ProtoX theme helpers: identical copy in every module.
const KEY = 'protox-theme'

export const MODULE_URLS = {
  idea: 'http://localhost:5173',
  code: 'http://localhost:5174',
  test: 'http://localhost:5175',
  preview: 'http://localhost:5176',
  deploy: 'http://localhost:5180',
}

export function currentTheme(): Theme {
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light'
}

export type Theme = 'light' | 'dark'

export function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
  writeCookieTheme(theme)
  try {
    localStorage.setItem(KEY, theme)
  } catch {
    /* storage blocked: the theme still applies for this visit */
  }
}

/** Adds ?theme=… so the next ProtoX module opens in the same theme. */
export function withTheme(url: string): string {
  const u = new URL(url, window.location.href)
  u.searchParams.set('theme', currentTheme())
  return u.toString()
}

/* ---------- Shared theme across all ProtoX pages ----------
 * Each module runs on its own port, so localStorage is NOT shared between them.
 * Cookies on localhost ARE shared across ports, so the cookie is the single
 * source of truth: toggling on any page updates it, and every open page
 * watches it and follows along. */
function readCookieTheme(): Theme | null {
  const m = document.cookie.match(/(?:^|;\s*)protox-theme=(light|dark)/)
  return m ? (m[1] as Theme) : null
}

function writeCookieTheme(theme: Theme) {
  document.cookie = `${KEY}=${theme}; path=/; max-age=31536000; SameSite=Lax`
}

/** Calls onChange whenever another ProtoX page switches the theme. Returns a cleanup function. */
export function watchTheme(onChange: (theme: Theme) => void): () => void {
  const check = () => {
    const shared = readCookieTheme()
    if (shared && shared !== currentTheme()) {
      document.documentElement.classList.toggle('dark', shared === 'dark')
      try { localStorage.setItem(KEY, shared) } catch { /* ignore */ }
      onChange(shared)
    }
  }
  const onVisible = () => { if (document.visibilityState === 'visible') check() }
  window.addEventListener('focus', check)
  document.addEventListener('visibilitychange', onVisible)
  const timer = window.setInterval(check, 1000)
  check()
  return () => {
    window.removeEventListener('focus', check)
    document.removeEventListener('visibilitychange', onVisible)
    window.clearInterval(timer)
  }
}
