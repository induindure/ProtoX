import { useEffect, useRef, useState } from 'react'
import './PreviewWindow.css'

const API_BASE = 'http://localhost:8003/api'

export default function PreviewWindow({ projectId }) {
  const [status, setStatus] = useState(null)   // full /preview-status response
  const [error, setError] = useState('')
  const [showLogs, setShowLogs] = useState(false)
  const pollRef = useRef(null)

  const FAILED_STATUSES = ['install_failed', 'install_timeout', 'crashed']
  const bothRunning = status?.frontend?.status === 'running' && status?.backend?.status === 'running'
  const anyFailed = FAILED_STATUSES.includes(status?.frontend?.status) || FAILED_STATUSES.includes(status?.backend?.status)

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
      console.log("PROJECT ID:", projectId)
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

  useEffect(() => {
    startPreview()
    return () => clearInterval(pollRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  useEffect(() => {
    if (bothRunning || anyFailed) clearInterval(pollRef.current)
  }, [bothRunning, anyFailed])

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
        <button className="preview-btn preview-btn--danger" onClick={stopPreview}>
          Stop preview
        </button>
        <button className="preview-btn" onClick={startPreview}>
          Restart
        </button>
      </div>

      {error && <div className="preview-error">{error}</div>}

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
