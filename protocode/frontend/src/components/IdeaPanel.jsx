import { MODULE_URLS, withTheme } from '../protox/theme'
import { LogoMark } from '../protox/Header'

export default function IdeaPanel({ idea }) {
  if (!idea) {
    return (
      <div className="px-empty" style={{ padding: '40px 24px' }}>
        <div style={{ marginBottom: 16 }}><LogoMark size={56} /></div>
        <h2>No idea loaded yet</h2>
        <p>Pick an idea in ProtoIdea and click “Finalize &amp; open ProtoCode”. It will appear here.</p>
        <a href={withTheme(MODULE_URLS.idea)} className="px-btn px-btn-outline" style={{ marginTop: 16 }}>Go to ProtoIdea</a>
      </div>
    )
  }

  return (
    <section className="px-card px-stack">
      <div className="px-between">
        <p className="px-section-label">Your idea</p>
        <span className="px-badge px-badge-accent">From ProtoIdea</span>
      </div>
      <div>
        <h2 className="px-title" style={{ fontSize: 22 }}>{idea.title}</h2>
        <p className="px-subtitle">{idea.description}</p>
      </div>
      <div>
        <p className="px-section-label" style={{ marginBottom: 4 }}>Target users</p>
        <p style={{ margin: 0 }}>{idea.target_users}</p>
      </div>
      <div>
        <p className="px-section-label" style={{ marginBottom: 6 }}>Core features</p>
        <div className="px-chips">
          {idea.features.map((f, i) => <span key={i} className="px-chip">{f}</span>)}
        </div>
      </div>
    </section>
  )
}
