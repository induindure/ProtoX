const STACKS = [
  { value: 'React + FastAPI', title: 'Fast & modern', tagline: 'Quick responses' },
  { value: 'React + Django', title: 'Users & data', tagline: 'Logins & databases' },
  { value: 'Vue + FastAPI', title: 'Simple & friendly', tagline: 'Beginner-friendly' },
]

export default function TechSelector({ techStack, setTechStack }) {
  return (
    <fieldset style={{ border: 0, margin: 0, padding: 0 }}>
      <legend className="px-label" style={{ marginBottom: 8 }}>App type</legend>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 8 }}>
        {STACKS.map(stack => {
          const selected = techStack === stack.value
          return (
            <button
              key={stack.value}
              type="button"
              onClick={() => setTechStack(stack.value)}
              aria-pressed={selected}
              className={`px-option ${selected ? 'is-selected' : ''}`}
              style={{ padding: selected ? '9px 11px' : '10px 12px', gap: 2 }}
            >
              <span style={{ display: 'flex', justifyContent: 'space-between', gap: 8, width: '100%' }}>
                <span style={{ fontWeight: 700 }}>{stack.title}</span>
                <span className="px-small px-muted">{stack.tagline}</span>
              </span>
              <span className="px-mono" style={{ fontSize: 11, fontWeight: 500, color: selected ? 'var(--accent-text)' : 'var(--faint)' }}>
                {stack.value}
              </span>
            </button>
          )
        })}
      </div>
    </fieldset>
  )
}
