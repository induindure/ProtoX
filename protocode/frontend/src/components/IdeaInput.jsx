export default function IdeaInput({ idea, setIdea }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>
        YOUR IDEA
      </label>
      <textarea
        rows={3}
        placeholder="e.g. A carpooling app for college students with real-time location tracking..."
        value={idea}
        onChange={e => setIdea(e.target.value)}
        style={{
          background: 'var(--surface2)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '0.85rem 1rem',
          color: 'var(--text)',
          fontSize: '0.95rem',
          resize: 'vertical',
          outline: 'none',
          fontFamily: 'inherit',
          lineHeight: 1.6,
          transition: 'border 0.2s',
        }}
        onFocus={e => e.target.style.borderColor = 'var(--accent)'}
        onBlur={e => e.target.style.borderColor = 'var(--border)'}
      />
    </div>
  )
}