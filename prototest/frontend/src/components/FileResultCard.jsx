import { useState } from 'react'

const STATUS = {
  pass: { color: 'var(--ok)', label: 'OK' },
  warn: { color: 'var(--warn)', label: 'Warning' },
  fail: { color: 'var(--err)', label: 'Error' },
  skip: { color: 'var(--faint)', label: 'Skipped' },
}

export default function FileResultCard({ result }) {
  const [open, setOpen] = useState(false)
  const cfg = STATUS[result.syntax.status] || STATUS.skip
  const hasReview = Boolean(result.ai_feedback)

  return (
    <li style={{ borderBottom: '1px solid var(--border)' }}>
      <button
        type="button"
        onClick={() => hasReview && setOpen(o => !o)}
        aria-expanded={hasReview ? open : undefined}
        className="px-btn px-btn-ghost"
        style={{ width: '100%', borderRadius: 0, justifyContent: 'flex-start', padding: '10px 20px', minHeight: 44, cursor: hasReview ? 'pointer' : 'default', textAlign: 'left' }}
      >
        <span className="px-dot" style={{ color: cfg.color }} aria-label={cfg.label} role="img" />
        <span className="px-mono" style={{ flex: 1, minWidth: 0, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis' }}>{result.path}</span>
        <span className="px-small" style={{ color: result.syntax.status === 'pass' ? 'var(--muted)' : cfg.color, fontWeight: result.syntax.status === 'pass' ? 400 : 600 }}>
          {result.syntax.message}
        </span>
        {hasReview && <span className="px-small" style={{ color: 'var(--faint)' }} aria-hidden="true">{open ? '−' : '+'}</span>}
      </button>

      {open && hasReview && (
        <div style={{ padding: '0 20px 14px 38px' }}>
          <p className="px-section-label" style={{ marginBottom: 6 }}>AI review</p>
          <p style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 13 }}>{result.ai_feedback}</p>
        </div>
      )}
    </li>
  )
}
