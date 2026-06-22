const STACKS = [
  {
    value: 'React + FastAPI',
    label: 'React + FastAPI',
    tagline: 'Fast & modern - great for apps that need quick responses',
  },
  {
    value: 'React + Node/Express',
    label: 'React + Node/Express',
    tagline: 'Most popular combo - huge community, easy to find help',
  },
  {
    value: 'React + Django',
    label: 'React + Django',
    tagline: 'Best for apps that handle users, logins & databases',
  },
  {
    value: 'Vue + FastAPI',
    label: 'Vue + FastAPI',
    tagline: 'Simple & beginner-friendly frontend with a speedy backend',
  },
  {
    value: 'Vue + Node/Express',
    label: 'Vue + Node/Express',
    tagline: 'Easy to learn, good for straightforward web apps',
  },
  {
    value: 'Next.js + FastAPI',
    label: 'Next.js + FastAPI',
    tagline: 'Great for public websites that need to load fast on Google',
  },
  {
    value: 'Next.js + Node/Express',
    label: 'Next.js + Node/Express',
    tagline: 'Best choice if you want your app to go live & scale big',
  },
]

export default function TechSelector({ techStack, setTechStack }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <label style={{
        fontSize: '0.75rem',
        color: 'var(--text-light)',
        fontWeight: 700,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
      }}>
        Choose Your App Type
      </label>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxWidth: '420px' }}>
        {STACKS.map(stack => (
          <div
            key={stack.value}
            onClick={() => setTechStack(stack.value)}
            style={{
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              border: `1px solid ${techStack === stack.value ? 'var(--accent)' : 'var(--border)'}`,
              background: techStack === stack.value ? 'var(--surface-active, rgba(99,102,241,0.08))' : 'var(--surface)',
              cursor: 'pointer',
              transition: 'all 0.18s',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.15rem',
            }}
          >
            <span style={{
              fontSize: '0.85rem',
              fontWeight: 600,
              color: techStack === stack.value ? 'var(--accent)' : 'var(--text)',
              fontFamily: 'var(--font)',
            }}>
              {stack.tagline}
            </span>
            <span style={{
              fontSize: '0.7rem',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font)',
            }}>
              {stack.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}