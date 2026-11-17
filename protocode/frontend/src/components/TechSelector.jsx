const STACKS = [
  { value: 'React + FastAPI', title: 'Fast & modern', tagline: 'Great for apps that need quick responses' },
  { value: 'React + Django', title: 'Users & data', tagline: 'Best for apps with logins & databases' },
  { value: 'Vue + FastAPI', title: 'Simple & friendly', tagline: 'Beginner-friendly frontend, speedy backend' },
]

export default function TechSelector({ techStack, setTechStack }) {
  return (
    <fieldset style={{ border: 0, margin: 0, padding: 0 }}>
      <legend className="px-label" style={{ marginBottom: 8 }}>Choose your app type</legend>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 10 }}>
        {STACKS.map(stack => {
          const selected = techStack === stack.value
          return (
            <button
              key={stack.value}
              type="button"
              onClick={() => setTechStack(stack.value)}
              aria-pressed={selected}
              className={`px-option ${selected ? 'is-selected' : ''}`}
            >
              <span style={{ fontWeight: 700 }}>{stack.title}</span>
              <span className="px-small px-muted">{stack.tagline}</span>
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
