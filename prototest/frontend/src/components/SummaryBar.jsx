export default function SummaryBar({ summary, projectName, techStack }) {
  const total = summary.total
  const testsPassed = summary.tests_passed

  const pill = (label, count, bg, color) => (
    <div style={{
      padding: '0.4rem 1rem',
      borderRadius: '999px',
      background: bg,
      color,
      fontWeight: 700,
      fontSize: '0.85rem',
      display: 'flex',
      gap: '0.4rem',
      alignItems: 'center',
    }}>
      <span>{label}</span>
      <span style={{
        background: 'rgba(0,0,0,0.12)',
        borderRadius: '999px',
        padding: '0 0.45rem',
        fontSize: '0.8rem',
      }}>{count}</span>
    </div>
  )

  return (
    <div style={{
      background: '#fff',
      borderBottom: '1px solid var(--border)',
      padding: '1.5rem 2rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>{projectName}</h2>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{techStack}</span>
        </div>

        <div style={{
          width: '72px',
          height: '72px',
          borderRadius: '50%',
          background: testsPassed ? '#dcfce7' : '#fee2e2',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          border: `3px solid ${testsPassed ? '#16a34a' : '#dc2626'}`,
        }}>
          <span style={{ fontSize: '1.3rem' }}>{testsPassed ? '✅' : '❌'}</span>
          <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            {testsPassed ? 'PASS' : 'FAIL'}
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
        {pill('📄 Files', total, '#f1f5f9', '#475569')}
        {pill('❌ Syntax errors', summary.syntax_failed, summary.syntax_failed > 0 ? '#fee2e2' : '#dcfce7', summary.syntax_failed > 0 ? '#991b1b' : '#166534')}
        {pill(testsPassed ? '✅ Tests passed' : '❌ Tests failed', '', testsPassed ? '#dcfce7' : '#fee2e2', testsPassed ? '#166534' : '#991b1b')}
      </div>
    </div>
  )
}