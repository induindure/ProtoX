import { useState, useRef, useEffect } from 'react'

export default function ChatPanel({ onSend, onUndo, canUndo }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, busy])

  const submit = async () => {
    const text = input.trim()
    if (!text || busy) return
    setInput('')
    setMessages(m => [...m, { role: 'user', text }])
    setBusy(true)
    try {
      const r = await onSend(text)
      setMessages(m => [...m, {
        role: 'assistant',
        text: r.explanation || 'Done.',
        changed: r.changed,
        created: r.created,
      }])
    } catch {
      setMessages(m => [...m, {
        role: 'error',
        text: 'Edit failed. Check the ProtoCode backend terminal for the error.',
      }])
    } finally {
      setBusy(false)
    }
  }

  const undo = () => {
    onUndo()
    setMessages(m => [...m, { role: 'note', text: 'Last edit undone.' }])
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const bubbleClass = (role) =>
    role === 'user' ? 'px-msg px-msg-user' :
    role === 'error' ? 'px-msg px-msg-err' :
    role === 'note' ? 'px-msg px-msg-note' : 'px-msg px-msg-bot'

  const pathList = (label, paths, color) =>
    paths?.length > 0 && (
      <div style={{ marginTop: 8 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
        {paths.map(p => (
          <div key={p} className="px-mono" style={{ fontSize: 12 }}>{p}</div>
        ))}
      </div>
    )

  const [showLog, setShowLog] = useState(true)

  return (
    <div className="px-chat-float" aria-label="Edit with chat">
      {showLog && (messages.length > 0 || busy) && (
        <div className="px-chat-log" aria-live="polite">
          {messages.map((m, i) => (
            <div key={i} className={bubbleClass(m.role)}>
              {m.text}
              {m.role === 'assistant' && (
                <>
                  {pathList('Changed', m.changed, 'var(--ok)')}
                  {pathList('New files', m.created, 'var(--accent-text)')}
                  {!m.changed?.length && !m.created?.length && (
                    <div className="px-small" style={{ marginTop: 8, color: 'var(--muted)' }}>No files changed.</div>
                  )}
                </>
              )}
            </div>
          ))}
          {busy && (
            <div className="px-msg px-msg-bot" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="px-spinner" /> Editing…
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      )}

      <div className="px-composer" style={{ alignItems: 'center' }}>
        <span style={{ width: 30, height: 30, borderRadius: 9, background: 'var(--brand)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginLeft: 4 }} aria-hidden="true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4z" /></svg>
        </span>
        <label htmlFor="chat-input" className="px-sr-only">Describe a change</label>
        <textarea
          id="chat-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={busy}
          rows={1}
          placeholder="Ask ProtoX to change the code… e.g. add a login page (Enter to send)"
          className="px-textarea"
          style={{ resize: 'none', borderColor: 'transparent', minHeight: 44 }}
        />
        {messages.length > 0 && (
          <button onClick={() => setShowLog(v => !v)} className="px-btn px-btn-sm px-btn-ghost" aria-expanded={showLog}>
            {showLog ? 'Hide chat' : `Chat (${messages.length})`}
          </button>
        )}
        <button onClick={undo} disabled={!canUndo || busy} className="px-btn px-btn-sm">Undo</button>
        <button onClick={submit} disabled={busy || !input.trim()} className="px-btn px-btn-primary">
          {busy ? <><span className="px-spinner" /> Editing…</> : 'Send'}
        </button>
      </div>
    </div>
  )
}
