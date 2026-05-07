const STACKS = [
  'React + FastAPI',
  'React + Node/Express',
  'React + Django',
  'Vue + FastAPI',
  'Vue + Node/Express',
  'Next.js + FastAPI',
  'Next.js + Node/Express',
]

export default function TechSelector({ techStack, setTechStack }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <label style={{
        fontSize: '0.75rem',
        color: 'var(--text-light)',
        fontWeight: 700,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
      }}>
        Tech Stack
      </label>
      <select
        value={techStack}
        onChange={e => setTechStack(e.target.value)}
        style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '6px',
          padding: '0.65rem 1rem',
          color: techStack ? 'var(--text)' : 'var(--text-muted)',
          fontSize: '0.9rem',
          outline: 'none',
          cursor: 'pointer',
          maxWidth: '300px',
          transition: 'border 0.2s',
          fontFamily: 'var(--font)',
        }}
        onFocus={e => e.target.style.borderColor = 'var(--accent)'}
        onBlur={e => e.target.style.borderColor = 'var(--border)'}
      >
        <option value="" disabled>Select a stack...</option>
        {STACKS.map(stack => (
          <option key={stack} value={stack}>{stack}</option>
        ))}
      </select>
    </div>
  )
}