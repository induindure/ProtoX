import { useState } from 'react'

const STATUS_CONFIG = {
  pass: { color: '#16a34a', bg: '#dcfce7', icon: '✅' },
  warn: { color: '#ca8a04', bg: '#fef9c3', icon: '⚠️' },
  fail: { color: '#dc2626', bg: '#fee2e2', icon: '❌' },
  skip: { color: '#475569', bg: '#f1f5f9', icon: '⏭️' },
}

export default function FileResultCard({ result }) {
  const [open, setOpen] = useState(false)
  const cfg = STATUS_CONFIG[result.syntax.status]

  return (
    <div style={{
      border: `1px solid ${cfg.color}33`,
      borderRadius: '10px',
      overflow: 'hidden',
      background: '#fff',
    }}>
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          padding: '0.85rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          cursor: 'pointer',
          background: cfg.bg,
        }}
      >
        <span>{cfg.icon}</span>
        <span style={{
          fontFamily: 'monospace',
          fontSize: '0.85rem',
          fontWeight: 600,
          color: '#1a1a1a',
          flex: 1,
        }}>
          {result.path}
        </span>
        <span style={{ fontSize: '0.78rem', color: cfg.color, fontWeight: 600 }}>
          {result.syntax.message}
        </span>
        <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{open ? '▲' : '▼'}</span>
      </div>

      {open && (
        <div style={{
          padding: '1rem 1.25rem',
          borderTop: `1px solid ${cfg.color}33`,
          background: '#fafafa',
        }}>
          <p style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            marginBottom: '0.5rem',
          }}>
            AI Review
          </p>
          <pre style={{
            fontFamily: 'inherit',
            fontSize: '0.85rem',
            lineHeight: 1.7,
            color: '#1a1a1a',
            whiteSpace: 'pre-wrap',
            margin: 0,
          }}>
            {result.ai_feedback}
          </pre>
        </div>
      )}
    </div>
  )
}