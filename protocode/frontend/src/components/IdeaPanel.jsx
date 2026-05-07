export default function IdeaPanel({ idea }) {
  if (!idea) return (
    <div style={{
      padding: '1rem 1.25rem',
      border: '1px dashed var(--border)',
      borderRadius: '8px',
      color: 'var(--text-muted)',
      fontSize: '0.9rem',
      background: 'var(--surface)',
    }}>
      No idea loaded. Go to ProtoIdea, select an idea, and click "Send to ProtoCode".
    </div>
  )

  return (
    <div style={{
      padding: '1.25rem',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      background: 'var(--surface)',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <span style={{
          fontWeight: 700,
          fontSize: '1rem',
          color: 'var(--text)',
        }}>
          {idea.title}
        </span>
        <span style={{
          fontSize: '0.75rem',
          background: '#f0f0f0',
          color: 'var(--text-muted)',
          padding: '0.15rem 0.6rem',
          borderRadius: '999px',
          fontWeight: 600,
        }}>
          From ProtoIdea
        </span>
      </div>

      <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
        {idea.description}
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-light)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          Target Users
        </span>
        <span style={{ fontSize: '0.85rem', color: 'var(--text)' }}>{idea.target_users}</span>
      </div>

      <div>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-light)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          Core Features
        </span>
        <ul style={{ marginTop: '0.4rem', paddingLeft: '1.1rem', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
          {idea.features.map((f, i) => (
            <li key={i} style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{f}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}