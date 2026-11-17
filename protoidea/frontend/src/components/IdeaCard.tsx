import { useState } from 'react'
import type { IdeaModel, IdeaScores } from '../types'

interface Props {
  idea: IdeaModel
  scores?: IdeaScores
  index: number
  onSelect?: () => void
  selected?: boolean
}

export default function IdeaCard({ idea, scores, index, onSelect, selected }: Props) {
  const [expanded, setExpanded] = useState(index === 0)
  const top = index === 0

  return (
    <article className={`px-card px-stack ${selected ? 'is-selected' : ''}`}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
        <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start', minWidth: 0 }}>
          <span className="px-mono" style={{ fontSize: 13, color: 'var(--faint)', paddingTop: 3 }}>
            {String(index + 1).padStart(2, '0')}
          </span>
          <div style={{ minWidth: 0 }}>
            <h3 className="px-h2">{idea.title}</h3>
            <p className="px-subtitle" style={{ maxWidth: 680 }}>{idea.description}</p>
          </div>
        </div>
        {scores && (
          <div
            style={{
              textAlign: 'center', minWidth: 64, padding: '6px 10px', borderRadius: 10, flexShrink: 0,
              background: top ? 'var(--accent-soft)' : 'var(--surface2)',
              color: top ? 'var(--accent-text)' : 'var(--text)',
            }}
          >
            <span style={{ display: 'block', fontSize: 22, fontWeight: 700, lineHeight: 1.1 }}>{scores.total}</span>
            <span style={{ fontSize: 11, fontWeight: 600 }}>score</span>
          </div>
        )}
      </div>

      {scores && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 16 }}>
          {[
            { label: 'Feasibility', value: scores.feasibility },
            { label: 'Novelty', value: scores.novelty },
            { label: 'Market fit', value: scores.market_fit },
          ].map(({ label, value }) => (
            <div key={label}>
              <div className="px-small" style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--muted)', fontSize: 12 }}>
                <span>{label}</span>
                <span style={{ fontWeight: 600, color: 'var(--text)' }}>{value}</span>
              </div>
              <div className={`px-meter ${top ? '' : 'is-muted'}`} style={{ marginTop: 6 }}>
                <span style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {expanded && (
        <div className="px-stack" style={{ gap: 12 }}>
          <div>
            <p className="px-section-label" style={{ marginBottom: 6 }}>Target users</p>
            <p style={{ margin: 0 }}>{idea.target_users}</p>
          </div>
          <div>
            <p className="px-section-label" style={{ marginBottom: 6 }}>Core features</p>
            <div className="px-chips">
              {idea.features.map((f, i) => <span key={i} className="px-chip">{f}</span>)}
            </div>
          </div>
          {idea.tech_hints.length > 0 && (
            <div>
              <p className="px-section-label" style={{ marginBottom: 6 }}>Tech hints</p>
              <div className="px-chips">
                {idea.tech_hints.map((t, i) => (
                  <span key={i} className="px-chip px-mono" style={{ background: 'var(--accent-soft)', color: 'var(--accent-text)' }}>{t}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="px-between" style={{ paddingTop: 12, borderTop: '1px solid var(--border)' }}>
        <button type="button" className="px-link-btn" onClick={() => setExpanded((v) => !v)} aria-expanded={expanded}>
          {expanded ? 'Show less' : 'Show features & details'}
        </button>
        {onSelect && (
          <button type="button" onClick={onSelect} className={`px-btn ${top || selected ? 'px-btn-cta' : 'px-btn-outline'}`}>
            {selected ? 'Refine this idea →' : 'Choose & refine →'}
          </button>
        )}
      </div>
    </article>
  )
}
