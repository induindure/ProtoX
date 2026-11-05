import { getDatabaseUrlError } from '../utils/databaseUrl'

export default function DatabaseUrlInput({ databaseUrl, setDatabaseUrl }) {
  const validationError = databaseUrl ? getDatabaseUrlError(databaseUrl) : ''
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <label style={{
        fontSize: '0.75rem',
        color: 'var(--text-light)',
        fontWeight: 700,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
      }}>
        Database URL (Required)
      </label>
      <input
        type="text"
        value={databaseUrl}
        required
        aria-required="true"
        aria-invalid={Boolean(validationError)}
        aria-describedby="database-url-status"
        onChange={(e) => setDatabaseUrl(e.target.value)}
        placeholder="postgresql://user:password@host:5432/dbname"
        style={{
          padding: '0.6rem 0.85rem',
          borderRadius: '8px',
          border: '1px solid var(--border)',
          fontSize: '0.85rem',
          fontFamily: 'var(--font)',
          maxWidth: '420px',
          background: 'var(--surface)',
          color: 'var(--text)',
        }}
      />
      <span
        id="database-url-status"
        role={validationError ? 'alert' : 'status'}
        style={{
          color: validationError ? 'var(--accent)' : 'var(--text-muted)',
          fontSize: '0.8rem',
        }}
      >
        {validationError || (databaseUrl ? 'URL format looks valid.' : 'Enter a database connection URL.')}
      </span>
    </div>
  )
}
