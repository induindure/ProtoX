import { useState } from 'react'
import type { IdeaModel, IdeaScores } from '../types'

interface Props {
  idea: IdeaModel
  scores?: IdeaScores
  index: number
  onSelect?: () => void
  selected?: boolean
}

function Num({ index }: { index: number }) {
  return (
    <span className="px-mono" style={{ fontSize: 13, fontWeight: 600, color: 'var(--faint)', paddingTop: 3, flexShrink: 0 }}>
      {String(index + 1).padStart(2, '0')}
    </span>
  )
}

export default function IdeaCard({ idea, scores, index, onSelect, selected }: Props) {
  const top = index === 0
  // The top idea opens fully; the rest start as slim rows that expand on click.
  const [open, setOpen] = useState(top)
  const [details, setDetails] = useState(false)

  if (!open) {
    return (
      <article className={`px-card ${selected ? 'is-selected' : ''}`} style={{ padding: 0 }}>
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-expanded={false}
          style={{
            display: 'flex', alignItems: 'center', gap: 16, width: '100%', minHeight: 64, padding: '14px 20px',
            border: 0, background: 'transparent', color: 'inherit', font: 'inherit', textAlign: 'left', cursor: 'pointer',
          }}
        >
          <Num index={index} />
          <span style={{ flex: 1, minWidth: 0 }}>
            <span style={{ display: 'block', fontWeight: 700, fontSize: 16 }}>{idea.title}</span>
            <span className="px-muted" style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {idea.description}
            </span>
          </span>
          {scores && (
            <span style={{ padding: '2px 10px', borderRadius: 10, background: 'var(--surface2)', fontWeight: 700, fontSize: 16, flexShrink: 0 }}>
              {scores.total}
            </span>
          )}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--faint)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0 }}>
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>
      </article>
    )
  }

  return (
    <article className={`px-card px-stack ${selected ? "is-selected" : ""}`} style={{ padding: '18px 20px', gap: 14 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
        <Num index={index} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 className="px-h2">{idea.title}</h3>
          <p className="px-subtitle" style={{ maxWidth: 680, marginTop: 2 }}>{idea.description}</p>
        </div>
        {scores && (
          <span
            style={{
              padding: '4px 12px', borderRadius: 10, flexShrink: 0, fontWeight: 700, fontSize: 20,
              background: top ? 'var(--accent-soft)' : 'var(--surface2)',
              color: top ? 'var(--accent-text)' : 'var(--text)',
            }}
            aria-label={`Score ${scores.total}`}
          >
            {scores.total}
          </span>
        )}
      </div>

      {scores && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 16, paddingLeft: 36 }}>
          {[
            { label: 'Feasibility', value: scores.feasibility },
            { label: 'Novelty', value: scores.novelty },
            { label: 'Market fit', value: scores.market_fit },
          ].map(({ label, value }) => (
            <div key={label}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--muted)', fontSize: 12 }}>
                <span>{label}</span>
                <span style={{ fontWeight: 600, color: 'var(--text)' }}>{value}</span>
              </div>
              <div className={`px-meter ${top ? '' : 'is-muted'}`} style={{ marginTop: 5, height: 5 }}>
                <span style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {details && (
        <div className="px-stack" style={{ gap: 12, paddingLeft: 36 }}>
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
        <div className="px-row" style={{ gap: 16 }}>
          <button type="button" className="px-link-btn" onClick={() => setDetails((v) => !v)} aria-expanded={details}>
            {details ? 'Hide details' : 'Features & details'}
          </button>
          {!top && (
            <button type="button" className="px-link-btn" style={{ color: 'var(--muted)' }} onClick={() => { setOpen(false); setDetails(false) }}>
              Collapse
            </button>
          )}
        </div>
        {onSelect && (
          <button type="button" onClick={onSelect} className={`px-btn ${top || selected ? 'px-btn-cta' : 'px-btn-outline'}`}>
            {selected ? 'Refine this idea →' : 'Choose & refine →'}
          </button>
        )}
      </div>
    </article>
  )
}
