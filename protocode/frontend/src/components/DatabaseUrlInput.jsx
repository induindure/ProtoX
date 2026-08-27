export default function DatabaseUrlInput({ databaseUrl, setDatabaseUrl }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <label style={{
        fontSize: '0.75rem',
        color: 'var(--text-light)',
        fontWeight: 700,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
      }}>
        Database URL{' '}
        <span style={{ textTransform: 'none', fontWeight: 400, color: 'var(--text-muted)' }}>
        </span>
      </label>
      <input
        type="text"
        value={databaseUrl}
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
    </div>
  )
}
