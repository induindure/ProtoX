import { getDatabaseUrlError } from '../utils/databaseUrl'

export default function DatabaseUrlInput({ databaseUrl, setDatabaseUrl }) {
  const validationError = databaseUrl ? getDatabaseUrlError(databaseUrl) : ''
  const valid = databaseUrl && !validationError

  return (
    <div className="px-field">
      <label htmlFor="database-url" className="px-label">
        Database URL <span className="px-required">required</span>
      </label>
      <input
        id="database-url"
        type="text"
        value={databaseUrl}
        required
        aria-required="true"
        aria-invalid={Boolean(validationError)}
        aria-describedby="database-url-status"
        onChange={(e) => setDatabaseUrl(e.target.value)}
        placeholder="postgresql://user:password@host:5432/dbname"
        spellCheck={false}
        autoComplete="off"
        className="px-input px-input-mono"
      />
      <span
        id="database-url-status"
        role={validationError ? 'alert' : 'status'}
        className={`px-help ${validationError ? 'is-err' : valid ? 'is-ok' : ''}`}
      >
        {validationError || (valid ? 'URL format looks valid.' : 'Enter a database connection URL.')}
      </span>
    </div>
  )
}
