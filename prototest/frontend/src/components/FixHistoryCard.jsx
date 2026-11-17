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

function iterationPassed(it) {
  return it.fix_type === 'test' && it.test_execution && it.test_execution.ran && it.test_execution.passed
}

export default function FixHistoryCard({ data }) {
  const attempts = `${data.attempts_used} attempt${data.attempts_used === 1 ? '' : 's'}`

  return (
    <section className="px-card px-stack">
      <div className="px-between">
        <h2 className="px-h3">Auto-fix history</h2>
        <span className={`px-badge ${data.success ? 'px-badge-ok' : 'px-badge-err'}`}>
          {data.success ? `Passed after ${attempts}` : `Still failing after ${attempts}`}
        </span>
      </div>

      {!data.success && (
        <div className="px-alert px-alert-warn">
          Use “Get fix prompt for ProtoCode” and paste it into ProtoCode’s chat.
        </div>
      )}

      <ol className="px-timeline">
        {data.iterations.map((it) => {
          const ok = iterationPassed(it)
          return (
            <li key={it.attempt}>
              <div className="px-timeline-rail">
                <span
                  className="px-timeline-dot"
                  style={{ background: ok ? 'var(--ok-soft)' : 'var(--warn-soft)', color: ok ? 'var(--ok)' : 'var(--warn)' }}
                >
                  {it.attempt}
                </span>
              </div>
              <div className="px-timeline-body">
                <p style={{ margin: '3px 0 0', fontWeight: 600 }}>{describeIteration(it)}</p>
              </div>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
