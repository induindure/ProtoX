import { MODULE_URLS, withTheme } from '../protox/theme'

export default function IdeaPanel({ idea }) {
  if (!idea) {
    return (
      <div className="px-alert px-alert-warn" style={{ flexDirection: 'column', gap: 8 }}>
        <b>No idea loaded yet</b>
        <span className="px-small">Choose an idea in ProtoIdea and click “Finalize”. It will appear here.</span>
        <a href={withTheme(MODULE_URLS.idea)} className="px-btn px-btn-sm px-btn-outline">Go to ProtoIdea</a>
      </div>
    )
  }

  return (
    <section style={{ padding: 14, borderRadius: 12, background: 'var(--accent-soft)', color: 'var(--accent-text)' }}>
      <p className="px-section-label" style={{ color: 'inherit' }}>Your idea</p>
      <h2 style={{ margin: '4px 0 0', fontSize: 17, fontWeight: 700, color: 'var(--text)' }}>{idea.title}</h2>
      <p className="px-small" style={{ margin: '4px 0 0', color: 'var(--muted)' }}>{idea.description}</p>
      <details style={{ marginTop: 8 }}>
        <summary className="px-small" style={{ cursor: 'pointer', fontWeight: 600 }}>Users &amp; features</summary>
        <p className="px-small" style={{ margin: '8px 0', color: 'var(--text)' }}>{idea.target_users}</p>
        <div className="px-chips">
          {idea.features.map((f, i) => <span key={i} className="px-chip" style={{ background: 'var(--surface)', color: 'var(--text)' }}>{f}</span>)}
        </div>
      </details>
    </section>
  )
}
