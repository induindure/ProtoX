import { useState } from 'react'

export default function TestExecutionCard({ execution }) {
  const [showCode, setShowCode] = useState(false)

  if (!execution.ran) {
    return (
      <div style={{
        border: '1px solid #fbbf2433',
        borderRadius: '10px',
        padding: '1rem 1.25rem',
        background: '#fef9c3',
        color: '#854d0e',
      }}>
        ⚠️ Tests did not run: {execution.reason}
      </div>
    )
  }

  const passed = execution.passed
  const cfg = passed
    ? { color: '#16a34a', bg: '#dcfce7', icon: '✅', label: 'Tests Passed' }
    : { color: '#dc2626', bg: '#fee2e2', icon: '❌', label: 'Tests Failed' }

  return (
    <div style={{
      border: `1px solid ${cfg.color}33`,
      borderRadius: '10px',
      overflow: 'hidden',
      background: '#fff',
    }}>
      <div style={{
        padding: '0.85rem 1.25rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        background: cfg.bg,
      }}>
        <span>{cfg.icon}</span>
        <span style={{ fontWeight: 700, color: cfg.color, flex: 1 }}>{cfg.label}</span>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{execution.runner}</span>
      </div>

      {execution.install_note && (
        <div style={{ padding: '0.6rem 1.25rem', fontSize: '0.8rem', color: '#854d0e', background: '#fef9c3' }}>
          ℹ️ {execution.install_note}
        </div>
      )}

      <div style={{ padding: '1rem 1.25rem', borderTop: '1px solid var(--border)' }}>
        <p style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
          Test Output
        </p>
        <pre style={{
          fontSize: '0.8rem',
          background: '#fafafa',
          padding: '0.75rem',
          borderRadius: '6px',
          overflowX: 'auto',
          whiteSpace: 'pre-wrap',
        }}>
          {execution.stdout || execution.stderr || 'No output'}
        </pre>

        <button
          onClick={() => setShowCode(s => !s)}
          style={{ marginTop: '0.75rem', background: 'none', border: 'none', color: 'var(--accent)', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', padding: 0 }}
        >
          {showCode ? 'Hide' : 'Show'} generated test code
        </button>

        {showCode && (
          <pre style={{
            fontSize: '0.78rem',
            background: '#1a1a1a',
            color: '#e5e5e5',
            padding: '0.75rem',
            borderRadius: '6px',
            overflowX: 'auto',
            marginTop: '0.5rem',
            whiteSpace: 'pre-wrap',
          }}>
            {execution.generated_test_code}
          </pre>
        )}
      </div>
    </div>
  )
}