function Tile({ label, value, sub, color }) {
  return (
    <div className="px-card px-stat-tile">
      <p className="px-section-label">{label}</p>
      <p className="px-stat-big" style={{ color: color || 'var(--text)' }}>
        {value} {sub && <small style={{ fontSize: 14, fontWeight: 500, color: 'var(--muted)' }}>{sub}</small>}
      </p>
    </div>
  )
}

export default function SummaryBar({ summary, fixAttempts = 0 }) {
  const testsPassed = summary.tests_passed
  const okFiles = summary.total - summary.syntax_failed

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
      <Tile label="Result" value={testsPassed ? 'Passing' : 'Failing'} color={testsPassed ? 'var(--ok)' : 'var(--err)'} />
      <Tile label="Files OK" value={okFiles} sub={`of ${summary.total}`} color="var(--ok)" />
      <Tile label="Syntax errors" value={summary.syntax_failed} color={summary.syntax_failed ? 'var(--err)' : undefined} />
      <Tile label="Auto-fix attempts" value={fixAttempts} />
    </div>
  )
}
