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

  const bubble = (role) => ({
    alignSelf: role === 'user' ? 'flex-end' : 'flex-start',
    maxWidth: '92%',
    padding: '0.55rem 0.8rem',
    borderRadius: '8px',
    fontSize: '0.83rem',
    lineHeight: 1.5,
    background:
      role === 'user' ? 'var(--accent)' :
      role === 'error' ? '#fef2f2' :
      role === 'note' ? 'transparent' : 'var(--surface2)',
    color:
      role === 'user' ? '#fff' :
      role === 'error' ? '#b91c1c' :
      role === 'note' ? 'var(--text-muted)' : 'var(--text)',
    border: role === 'assistant' ? '1px solid var(--border)' : 'none',
    fontStyle: role === 'note' ? 'italic' : 'normal',
  })

  const pathList = (label, paths, color) =>
    paths?.length > 0 && (
      <div style={{ marginTop: '0.5rem' }}>
        <div style={{ fontSize: '0.72rem', fontWeight: 700, color, textTransform: 'uppercase' }}>
          {label}
        </div>
        {paths.map(p => (
          <div key={p} style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{p}</div>
        ))}
      </div>
    )

  return (
    <div style={{
      width: '340px',
      flexShrink: 0,
      display: 'flex',
      flexDirection: 'column',
      borderLeft: '1px solid var(--border)',
      background: '#fff',
      minHeight: 0,
    }}>
      <div style={{
        padding: '0.65rem 1rem',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <span style={{ fontWeight: 700, fontSize: '0.88rem' }}>Chat edit</span>
        <button
          onClick={undo}
          disabled={!canUndo || busy}
          style={{
            padding: '0.25rem 0.7rem',
            background: 'var(--surface2)',
            border: '1px solid var(--border)',
            borderRadius: '5px',
            fontSize: '0.78rem',
            fontWeight: 600,
            cursor: canUndo && !busy ? 'pointer' : 'not-allowed',
            opacity: canUndo && !busy ? 1 : 0.5,
          }}
        >
          Undo
        </button>
      </div>

      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.6rem',
        minHeight: 0,
      }}>
        {messages.length === 0 && (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
            Ask for a change, e.g. "make the Follow button call the API" or
            "remove the hardcoded followers card".
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} style={bubble(m.role)}>
            {m.text}
            {m.role === 'assistant' && (
              <>
                {pathList('Changed', m.changed, '#166534')}
                {pathList('New files', m.created, '#1d4ed8')}
                {!m.changed?.length && !m.created?.length && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    No files changed.
                  </div>
                )}
              </>
            )}
          </div>
        ))}
        {busy && (
          <div style={bubble('note')}>Editing...</div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{ padding: '0.75rem', borderTop: '1px solid var(--border)' }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={busy}
          rows={3}
          placeholder="Describe a change... (Enter to send)"
          style={{
            width: '100%',
            boxSizing: 'border-box',
            resize: 'none',
            padding: '0.5rem 0.65rem',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            fontSize: '0.83rem',
            fontFamily: 'inherit',
          }}
        />
        <button
          onClick={submit}
          disabled={busy || !input.trim()}
          style={{
            marginTop: '0.5rem',
            width: '100%',
            padding: '0.5rem',
            background: busy || !input.trim() ? '#ccc' : 'var(--accent)',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 700,
            fontSize: '0.83rem',
            cursor: busy || !input.trim() ? 'not-allowed' : 'pointer',
          }}
        >
          {busy ? 'Editing...' : 'Apply edit'}
        </button>
      </div>
    </div>
  )
}