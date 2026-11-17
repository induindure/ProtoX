import { useState } from 'react'

export default function TestExecutionCard({ execution }) {
  const [showCode, setShowCode] = useState(false)

  if (!execution.ran) {
    return (
      <div className="px-alert px-alert-warn">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 9v4M12 17h.01M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /></svg>
        <span><strong>Tests did not run.</strong> {execution.reason}</span>
      </div>
    )
  }

  const passed = execution.passed

  return (
    <section className="px-card px-card-flush">
      <div className="px-card-head">
        <h2 className="px-h3" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className={`px-badge ${passed ? 'px-badge-ok' : 'px-badge-err'}`}>{passed ? 'Passed' : 'Failed'}</span>
          Test output
        </h2>
        <span className="px-mono px-small px-muted">{execution.runner}</span>
      </div>

      {execution.install_note && (
        <div className="px-alert px-alert-warn" style={{ borderRadius: 0 }}>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div>{execution.install_note}</div>
            {execution.install_error && (
              <pre className="px-code px-code-wrap" style={{ marginTop: 8, padding: 10, borderRadius: 8, fontSize: 12, maxHeight: 220 }}>
                {execution.install_error}
              </pre>
            )}
          </div>
        </div>
      )}

      <pre className="px-code px-code-wrap" style={{ maxHeight: 420, fontSize: 12.5 }}>
        {execution.stdout || execution.stderr || 'No output'}
      </pre>

      <div style={{ padding: '6px 20px', borderTop: '1px solid var(--border)' }}>
        <button type="button" onClick={() => setShowCode(s => !s)} className="px-link-btn" aria-expanded={showCode}>
          {showCode ? 'Hide' : 'Show'} generated test code
        </button>
      </div>

      {showCode && (
        <pre className="px-code px-code-wrap" style={{ borderTop: '1px solid var(--border)', maxHeight: 480, fontSize: 12.5 }}>
          {execution.generated_test_code}
        </pre>
      )}
    </section>
  )
}
