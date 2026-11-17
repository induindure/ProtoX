export default function SummaryBar({ summary }) {
  const testsPassed = summary.tests_passed
  const syntaxOk = summary.syntax_failed === 0

  return (
    <div className="px-stats">
      <div className="px-card" style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <span
          style={{
            width: 48, height: 48, borderRadius: 999, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: testsPassed ? 'var(--ok-soft)' : 'var(--err-soft)', color: testsPassed ? 'var(--ok)' : 'var(--err)',
          }}
          aria-hidden="true"
        >
          {testsPassed ? (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12l5 5L20 7" /></svg>
          ) : (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
          )}
        </span>
        <div>
          <p className="px-stat-label">Result</p>
          <p className="px-stat-value" style={{ color: testsPassed ? 'var(--ok)' : 'var(--err)' }}>
            {testsPassed ? 'All passing' : 'Tests failing'}
          </p>
        </div>
      </div>

      <div className="px-card">
        <p className="px-stat-label">Syntax errors</p>
        <p className="px-stat-value" style={{ color: syntaxOk ? 'var(--text)' : 'var(--err)' }}>
          {summary.syntax_failed} <small>in {summary.total} files</small>
        </p>
      </div>

      <div className="px-card">
        <p className="px-stat-label">Files</p>
        <p className="px-stat-value">{summary.total} <small>checked</small></p>
      </div>
    </div>
  )
}
