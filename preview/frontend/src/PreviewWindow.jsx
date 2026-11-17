import { useEffect, useRef, useState } from 'react'

const API_BASE = 'http://localhost:8003/api'
const TEST_API = 'http://localhost:8002/api'

export default function PreviewWindow({ projectId }) {
  const [status, setStatus] = useState(null)   // full /preview-status response
  const [error, setError] = useState('')
  const [showLogs, setShowLogs] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
  const [device, setDevice] = useState('both')   // both | desktop | phone
  const [browserError, setBrowserError] = useState('')
  const [fixPrompt, setFixPrompt] = useState('')
  const [promptLoading, setPromptLoading] = useState(false)
  const [promptError, setPromptError] = useState('')
  const [copied, setCopied] = useState(false)
  const pollRef = useRef(null)

  const [userNote, setUserNote] = useState('')
  const [showChoices, setShowChoices] = useState(false)
  const [noIssue, setNoIssue] = useState(false)
  const [hint, setHint] = useState('')

  const FAILED_STATUSES = ['install_failed', 'install_timeout', 'crashed']
  const bothRunning = status?.frontend?.status === 'running' && status?.backend?.status === 'running'
  const anyFailed = FAILED_STATUSES.includes(status?.frontend?.status) || FAILED_STATUSES.includes(status?.backend?.status)

  const hasSignal = anyFailed || browserError.trim() || userNote.trim()

  const statusLabel = (s) => ({
    pending: 'Queued…',
    installing: 'Installing dependencies…',
    running: 'Running',
    install_failed: 'Install failed',
    install_timeout: 'Timed out (hung install)',
    crashed: 'Crashed',
    stopped: 'Stopped',
  }[s] || 'Not started yet')

  const pollStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/preview-status/${projectId}`)
      const data = await res.json()
      setStatus(data)
    } catch {
      setError('Lost connection to ProtoPreview backend.')
    }
  }

  const startPreview = async () => {
    setError('')
    try {
      const res = await fetch(`${API_BASE}/start-preview/${projectId}`, { method: 'POST' })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to start preview')
      }
      pollRef.current = setInterval(pollStatus, 2000)
      pollStatus()
    } catch (e) {
      setError(e.message)
    }
  }

  const stopPreview = async () => {
    clearInterval(pollRef.current)
    await fetch(`${API_BASE}/stop-preview/${projectId}`, { method: 'POST' })
    setStatus(null)
  }

  const handleFixPrompt = async () => {
    setHint('')
    setNoIssue(false)
    if (!hasSignal) {            // nothing to go on: ask instead of generating
      setShowChoices(true)
      return
    }
    setShowChoices(false)
    setPromptLoading(true)
    setPromptError('')
    setFixPrompt('')
    try {
      const fr = await fetch(`${API_BASE}/project-files/${projectId}`)
      if (!fr.ok) throw new Error('files')
      const { files } = await fr.json()

      const tail = (arr) => (arr || []).join('\n').slice(-1100)
      const output = [
        'FRONTEND LOG:\n' + tail(status?.frontend?.log),
        'BACKEND LOG:\n' + tail(status?.backend?.log),
        browserError.trim() ? 'BROWSER ERROR:\n' + browserError.trim().slice(0, 900) : '',
      ].filter(Boolean).join('\n\n')

      const res = await fetch(`${TEST_API}/fix-prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ files, output, source: 'preview', user_note: userNote.trim() }),
      })
      if (!res.ok) throw new Error('prompt')
      const data = await res.json()
      if (data.no_issue) setNoIssue(true)
      else setFixPrompt(data.prompt)
    } catch {
      setPromptError(
        'Could not create the fix prompt. Make sure the ProtoTest backend is running, then try again.'
      )
    } finally {
      setPromptLoading(false)
    }
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(fixPrompt)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  useEffect(() => {
    startPreview()
    return () => clearInterval(pollRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  useEffect(() => {
    if (bothRunning || anyFailed) clearInterval(pollRef.current)
  }, [bothRunning, anyFailed])

  // open the help panel by itself when something fails
  useEffect(() => {
    if (anyFailed) setShowHelp(true)
  }, [anyFailed])

  const badge = bothRunning
    ? { cls: 'px-badge-ok', text: 'Running' }
    : anyFailed
      ? { cls: 'px-badge-err', text: `${statusLabel(status?.frontend?.status)} / ${statusLabel(status?.backend?.status)}` }
      : { cls: 'px-badge-accent', text: `Backend: ${statusLabel(status?.backend?.status)} · Frontend: ${statusLabel(status?.frontend?.status)}` }

  const url = bothRunning ? status.frontend.url : ''
  const browserBar = (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '9px 14px', borderBottom: '1px solid var(--border)', background: 'var(--surface2)' }}>
      <span style={{ display: 'flex', gap: 6 }} aria-hidden="true">
        <span style={{ width: 10, height: 10, borderRadius: 999, background: '#F87171' }} />
        <span style={{ width: 10, height: 10, borderRadius: 999, background: '#FBBF24' }} />
        <span style={{ width: 10, height: 10, borderRadius: 999, background: '#34D399' }} />
      </span>
      <span className="px-mono px-small" style={{ flex: 1, minWidth: 0, padding: '4px 12px', borderRadius: 8, background: 'var(--surface)', color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {url || 'Starting…'}
      </span>
      {url && <a href={url} target="_blank" rel="noreferrer" className="px-small" style={{ fontWeight: 600, color: 'var(--accent-text)' }}>Open in new tab ↗</a>}
    </div>
  )

  return (
    <div className="px-stack">
      <div className="px-between">
        <div className="px-row" style={{ gap: 10 }}>
          <span className={`px-badge ${badge.cls}`} role="status">
            {bothRunning || anyFailed ? <span className="px-dot" /> : <span className="px-spinner" style={{ width: 12, height: 12 }} />}
            {badge.text}
          </span>
          <div className="px-segmented" role="group" aria-label="Device">
            {[['both', 'Both'], ['desktop', 'Desktop'], ['phone', 'Phone']].map(([v, label]) => (
              <button key={v} type="button" aria-pressed={device === v} onClick={() => setDevice(v)}>{label}</button>
            ))}
          </div>
        </div>
        <div className="px-row" style={{ gap: 8 }}>
          <button className="px-btn px-btn-sm" onClick={() => setShowLogs(s => !s)} aria-expanded={showLogs}>
            {showLogs ? 'Hide logs' : 'Show logs'}
          </button>
          {(bothRunning || anyFailed) && (
            <button className={`px-btn px-btn-sm ${showHelp ? '' : 'px-btn-outline'}`} onClick={() => setShowHelp(s => !s)} aria-expanded={showHelp}>
              Something wrong?
            </button>
          )}
          <button className="px-btn px-btn-sm" onClick={startPreview}>Restart</button>
          <button className="px-btn px-btn-sm px-btn-danger" onClick={stopPreview}>Stop</button>
        </div>
      </div>

      {error && <div className="px-alert px-alert-err" role="alert">{error}</div>}

      {showLogs && (
        <section className="px-card px-card-flush">
          {status?.frontend && status?.backend ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
              <div style={{ minWidth: 0 }}>
                <div className="px-card-head"><span className="px-h3">Frontend</span><span className="px-badge px-badge-neutral">{status.frontend.status}</span></div>
                <pre className="px-code px-code-wrap" style={{ maxHeight: 280, fontSize: 12 }}>{status.frontend.log.join('\n')}</pre>
              </div>
              <div style={{ minWidth: 0, borderLeft: '1px solid var(--border)' }}>
                <div className="px-card-head"><span className="px-h3">Backend</span><span className="px-badge px-badge-neutral">{status.backend.status}</span></div>
                <pre className="px-code px-code-wrap" style={{ maxHeight: 280, fontSize: 12 }}>{status.backend.log.join('\n')}</pre>
              </div>
            </div>
          ) : (
            <pre className="px-code" style={{ fontSize: 12 }}>Waiting for processes to start… (status: {status?.status || 'unknown'})</pre>
          )}
        </section>
      )}

      {bothRunning ? (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 28, alignItems: 'flex-start', justifyContent: 'center' }}>
          {device !== 'phone' && (
            <section className="px-card px-card-flush" style={{ flex: '1 1 640px', maxWidth: device === 'desktop' ? 'none' : 900, minWidth: 0 }} aria-label="Desktop preview">
              {browserBar}
              <iframe
                key={url}
                title="App preview, desktop"
                src={url}
                style={{ display: 'block', width: '100%', height: device === 'desktop' ? 'min(720px, calc(100vh - 230px))' : 596, minHeight: 420, border: 0, background: '#FFFFFF' }}
              />
            </section>
          )}
          {device !== 'desktop' && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
              <div className="px-phone">
                <iframe key={url + '-phone'} title="App preview, phone" src={url} />
              </div>
              <span className="px-small px-muted">Phone view</span>
            </div>
          )}
        </div>
      ) : (
        <section className="px-card px-card-flush">
          {browserBar}
          <div style={{ height: 420, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, color: 'var(--muted)', padding: 24, textAlign: 'center' }}>
            {anyFailed ? (
              <>
                <span className="px-badge px-badge-err">Couldn’t start</span>
                <p style={{ margin: 0 }}>The demo app failed to start. Check the logs, or use “Something wrong?”.</p>
              </>
            ) : (
              <>
                <span className="px-spinner" style={{ width: 28, height: 28, color: 'var(--accent)' }} />
                <p style={{ margin: 0 }}>Spinning up your app… installing can take a minute or two.</p>
              </>
            )}
          </div>
        </section>
      )}

      {showHelp && (
          <aside className="px-card px-stack" style={{ width: '100%', maxWidth: 760, margin: '0 auto', boxSizing: 'border-box' }} aria-label="Get help fixing the app">
            <div className="px-row" style={{ gap: 10, flexWrap: 'nowrap' }}>
              <span style={{ width: 32, height: 32, borderRadius: 9, background: 'var(--brand)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }} aria-hidden="true">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4z" /></svg>
              </span>
              <div>
                <h2 className="px-h3">Something wrong?</h2>
                <p className="px-small px-muted" style={{ margin: 0 }}>
                  {anyFailed ? 'The app couldn’t start. ' : ''}We’ll write a fix request for ProtoCode.
                </p>
              </div>
            </div>

            <div className="px-field">
              <label htmlFor="user-note" className="px-label">What isn’t working?</label>
              <input
                id="user-note"
                value={userNote}
                onChange={(e) => setUserNote(e.target.value)}
                placeholder="e.g. login button does nothing"
                className="px-input"
              />
            </div>
            <div className="px-field">
              <label htmlFor="browser-error" className="px-label">Browser error <span className="px-label-hint">(optional)</span></label>
              <textarea
                id="browser-error"
                value={browserError}
                onChange={(e) => setBrowserError(e.target.value)}
                rows={3}
                placeholder="Blank page or “crashed”? Paste the logs, or a red error from the Console tab (Ctrl+Shift+I)."
                className="px-textarea px-input-mono"
                style={{ fontSize: 12 }}
              />
            </div>

            <button className="px-btn px-btn-cta px-btn-block" onClick={handleFixPrompt} disabled={promptLoading || !status}>
              {promptLoading ? <><span className="px-spinner" /> Writing the fix request…</> : 'Get fix prompt for ProtoCode'}
            </button>

            {promptError && <div className="px-alert px-alert-err">{promptError}</div>}
            {showChoices && (
              <div className="px-alert px-alert-warn">Nothing to go on yet. Describe what’s wrong or paste the error above, then try again.</div>
            )}
            {noIssue && (
              <div className="px-alert px-alert-ok">No problem found. If something still looks off, describe it above.</div>
            )}

            {fixPrompt && (
              <div className="px-stack" style={{ gap: 8 }}>
                <label htmlFor="fix-prompt" className="px-sr-only">Fix prompt</label>
                <textarea id="fix-prompt" readOnly value={fixPrompt} rows={6} className="px-textarea px-input-mono" style={{ fontSize: 12 }} />
                <div className="px-row" style={{ gap: 10 }}>
                  <button className="px-btn px-btn-primary px-btn-sm" onClick={handleCopy}>{copied ? 'Copied' : 'Copy prompt'}</button>
                  <span className="px-small px-muted">Paste it into the ProtoCode chat, then send the project to ProtoTest again.</span>
                </div>
              </div>
            )}
          </aside>
      )}
    </div>
  )
}
