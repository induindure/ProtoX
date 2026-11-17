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
