const handleSendToProtoCode = (idea) => {
  localStorage.setItem('protocode_idea', JSON.stringify({
    title: idea.title,
    description: idea.description,
    features: idea.features,
    tech_hints: idea.tech_hints,
    target_users: idea.target_users,
  }))
  window.open('http://localhost:5174', '_blank')
}

// Add this button inside the card JSX
<button
  onClick={() => handleSendToProtoCode(idea)}
  style={{
    marginTop: '1rem',
    padding: '0.5rem 1.2rem',
    background: '#8b0000',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    fontWeight: 600,
    fontSize: '0.85rem',
    cursor: 'pointer',
    letterSpacing: '0.03em',
  }}
>
  Send to ProtoCode →
</button>