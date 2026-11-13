import { useEffect, useRef, useState } from 'react'
import './PreviewWindow.css'

const API_BASE = 'http://localhost:8003/api'
const TEST_API = 'http://localhost:8002/api'

export default function PreviewWindow({ projectId }) {
  const [status, setStatus] = useState(null)   // full /preview-status response
  const [error, setError] = useState('')
  const [showLogs, setShowLogs] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
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

  return (
    <div className="preview-container">
      <div className="preview-toolbar">
        <span className="preview-title">Live Demo</span>

        {!bothRunning && !anyFailed && (
          <span className="preview-badge preview-badge--pending">
            Backend: {statusLabel(status?.backend?.status)} · Frontend: {statusLabel(status?.frontend?.status)}
          </span>
        )}
        {bothRunning && <span className="preview-badge preview-badge--ok">Running</span>}
        {anyFailed && <span className="preview-badge preview-badge--error">{statusLabel(status?.frontend?.status)} / {statusLabel(status?.backend?.status)} — see logs</span>}

        <button className="preview-btn" onClick={() => setShowLogs(s => !s)}>
          {showLogs ? 'Hide logs' : 'Show logs'}
        </button>
        {(bothRunning || anyFailed) && (
          <button className="preview-btn" onClick={() => setShowHelp(s => !s)}>
            Something wrong?
          </button>
        )}
        <button className="preview-btn preview-btn--danger" onClick={stopPreview}>
          Stop preview
        </button>
        <button className="preview-btn" onClick={startPreview}>
          Restart
        </button>
      </div>

      {error && <div className="preview-error">{error}</div>}

      {showHelp && (
        <div style={{
          border: '1px solid #ddd',
          borderRadius: '8px',
          padding: '1rem',
          margin: '0.75rem 0',
          background: '#fafafa',
        }}>
          <p style={{ margin: '0 0 0.5rem', fontWeight: 600 }}>
            {anyFailed
              ? "The app couldn't start. We can write a fix request for you."
              : 'Page blank, or something not working? We can write a fix request for you.'}
          </p>
          <p style={{ margin: '0 0 0.5rem', fontSize: '0.85rem', color: '#555' }}>
            If the page is blank, or you see the word "crashed", click "show logs" and copy paste the logs here. Or open the Console tab (Ctr+Shift+I) in the browser, and
            paste any red error below (optional).
          </p>
          <textarea
            value={browserError}
            onChange={(e) => setBrowserError(e.target.value)}
            rows={3}
            placeholder="Paste the red error here (optional)"
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #ccc', fontSize: '0.85rem' }}
          />
          <button
            className="preview-btn"
            onClick={handleFixPrompt}
            disabled={promptLoading || !status}
            style={{ marginTop: '0.5rem' }}
          >
            {promptLoading ? 'Writing the fix request...' : 'Get fix prompt for ProtoCode'}
          </button>

          {promptError && <div className="preview-error" style={{ marginTop: '0.5rem' }}>{promptError}</div>}

          {showChoices && (
            <div className="preview-error" style={{ marginTop: '0.5rem' }}>
              Nothing to go on yet. Paste the browser error or describe what's wrong below, then try again.
            </div>
          )}
          {noIssue && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#555' }}>
              No problem found. If something still looks off, describe it below.
            </div>
          )}

          <input
            value={userNote}
            onChange={(e) => setUserNote(e.target.value)}
            placeholder="Or describe what's not working (e.g. 'login button does nothing')"
            style={{ width: '100%', marginTop: '0.5rem', padding: '0.5rem', borderRadius: '6px', border: '1px solid #ccc', fontSize: '0.85rem' }}
          />

          {fixPrompt && (
            <div style={{ marginTop: '0.75rem' }}>
              <textarea
                readOnly
                value={fixPrompt}
                rows={6}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #ccc', fontSize: '0.85rem' }}
              />
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.5rem' }}>
                <button className="preview-btn" onClick={handleCopy}>
                  {copied ? 'Copied' : 'Copy prompt'}
                </button>
                <span style={{ fontSize: '0.8rem', color: '#555' }}>
                  Paste it into the ProtoCode chat, then send the project to ProtoTest again.
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {showLogs && status?.frontend && status?.backend && (
        <div className="preview-logs">
          <div>
            <h4>Frontend ({status.frontend.status})</h4>
            <pre>{status.frontend.log.join('\n')}</pre>
          </div>
          <div>
            <h4>Backend ({status.backend.status})</h4>
            <pre>{status.backend.log.join('\n')}</pre>
          </div>
        </div>
      )}
      {showLogs && !(status?.frontend && status?.backend) && (
        <div className="preview-logs">
          <pre>Waiting for processes to start... (status: {status?.status || 'unknown'})</pre>
        </div>
      )}

      <div className="preview-frame-wrap">
        {bothRunning ? (
          <iframe
            key={status.frontend.url}
            title="App preview"
            src={status.frontend.url}
            className="preview-frame"
          />
        ) : (
          <div className="preview-placeholder">
            {anyFailed
              ? 'The demo app failed to start. Check the logs above.'
              : 'Spinning up your app...'}
          </div>
        )}
      </div>
    </div>
  )
}