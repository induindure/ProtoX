function describeIteration(it) {
  if (it.fix_type === 'syntax') {
    return `Fixed syntax error${it.fixed_files.length === 1 ? '' : 's'} in ${it.fixed_files.join(', ')}`
  }
  if (it.fix_type === 'test') {
    const passed = it.test_execution && it.test_execution.ran && it.test_execution.passed
    if (passed) return 'Tests passed'
    if (it.fixed_files.length) return `Tests failed — patched ${it.fixed_files.join(', ')}`
    return 'Tests failed — could not determine a fix'
  }
  return (it.test_execution && it.test_execution.reason) || 'Stopped'
}

export default function FixHistoryCard({ data }) {
  const cfg = data.success
    ? {
        color: '#16a34a',
        bg: '#dcfce7',
        icon: '✅',
        label: `All checks passed after ${data.attempts_used} attempt${data.attempts_used === 1 ? '' : 's'}`,
      }
    : {
        color: '#dc2626',
        bg: '#fee2e2',
        icon: '⚠️',
        label: `Still failing after ${data.attempts_used} attempt${data.attempts_used === 1 ? '' : 's'} — manual review needed`,
      }

  return (
    <div style={{
      border: `1px solid ${cfg.color}33`,
      borderRadius: '10px',
      overflow: 'hidden',
      background: '#fff',
      marginBottom: '0.75rem',
    }}>
      <div style={{
        padding: '0.85rem 1.25rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        background: cfg.bg,
      }}>
        <span>{cfg.icon}</span>
        <span style={{ fontWeight: 700, color: cfg.color }}>{cfg.label}</span>
      </div>

      <div style={{ padding: '1rem 1.25rem', borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        {data.iterations.map((it) => (
          <div key={it.attempt} style={{ fontSize: '0.85rem', color: 'var(--text)' }}>
            <strong>Attempt {it.attempt}:</strong> {describeIteration(it)}
          </div>
        ))}
      </div>
    </div>
  )
}
