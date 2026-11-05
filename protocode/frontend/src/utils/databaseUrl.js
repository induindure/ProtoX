const DATABASE_SCHEMES = new Set([
  'postgres',
  'postgresql',
  'mysql',
  'mariadb',
  'mongodb',
  'sqlite',
  'mssql',
  'sqlserver',
  'oracle',
  'redis',
])

export function getDatabaseUrlError(value) {
  const input = value.trim()
  if (!input) return 'Enter a database URL to generate code.'
  if (/\s/.test(input)) return 'Remove spaces from the URL or percent-encode them.'

  let url
  try {
    url = new URL(input)
  } catch {
    return 'Enter a valid database URL, including its scheme (for example, postgresql://).'
  }

  const scheme = url.protocol.slice(0, -1).toLowerCase()
  const baseScheme = scheme.split('+', 1)[0]
  if (!DATABASE_SCHEMES.has(baseScheme)) {
    return 'Use a supported database URL scheme, such as postgresql://, mysql://, mongodb://, or sqlite:///.'
  }

  if (baseScheme === 'sqlite') {
    if (url.hostname || !url.pathname || url.pathname === '/') {
      return 'Enter a SQLite database path, for example sqlite:///./app.db.'
    }
    return ''
  }

  if (!url.hostname) return 'The database URL must include a hostname.'
  return ''
}
