import { useState } from 'react'
import type { IdeaRequest } from '../types'

interface Props {
  onSubmit: (req: IdeaRequest) => void
  loading: boolean
}

const APP_TYPES = ['Web App', 'Mobile App']
const DOMAINS = ['Healthcare', 'Education', 'Finance', 'E-Commerce', 'Social Media', 'Productivity', 'Entertainment', 'Travel', 'Food & Nutrition', 'Other']

export default function IdeaForm({ onSubmit, loading }: Props) {
  const [domain, setDomain] = useState('')
  const [customDomain, setCustomDomain] = useState('')
  const [appType, setAppType] = useState('')
  const [constraints, setConstraints] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const finalDomain = domain === 'Other' ? customDomain.trim() : domain
    if (!finalDomain || !appType) return
    onSubmit({ domain: finalDomain, app_type: appType, constraints: constraints.trim() || undefined })
  }

  const isValid = (domain === 'Other' ? customDomain.trim().length > 0 : domain.length > 0) && appType.length > 0

  return (
    <form onSubmit={handleSubmit} className="px-stack" style={{ padding: 20, gap: 14 }}>
      <div>
        <h2 className="px-h3">New ideas</h2>
        <p className="px-subtitle px-small">Get 3–5 scoped, buildable app ideas.</p>
      </div>

      <div className="px-field">
        <label htmlFor="domain" className="px-label">Domain</label>
        <select id="domain" value={domain} onChange={(e) => setDomain(e.target.value)} className="px-select">
          <option value="">Select a domain…</option>
          {DOMAINS.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
        {domain === 'Other' && (
          <input
            type="text"
            aria-label="Your domain"
            placeholder="Enter your domain (e.g. Agriculture)"
            value={customDomain}
            onChange={(e) => setCustomDomain(e.target.value)}
            className="px-input"
          />
        )}
      </div>

      <fieldset className="px-field" style={{ border: 0, margin: 0, padding: 0 }}>
        <legend className="px-label" style={{ marginBottom: 6 }}>App type</legend>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 6 }}>
          {APP_TYPES.map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setAppType(type)}
              aria-pressed={appType === type}
              className={`px-pill ${appType === type ? 'is-selected' : ''}`}
              style={{ minHeight: 40 }}
            >
              {type}
            </button>
          ))}
        </div>
      </fieldset>

      <div className="px-field">
        <label htmlFor="constraints" className="px-label">
          Constraints <span className="px-label-hint">(optional)</span>
        </label>
        <textarea
          id="constraints"
          rows={2}
          placeholder="e.g. free, simple UI, for college students"
          value={constraints}
          onChange={(e) => setConstraints(e.target.value)}
          className="px-textarea"
        />
      </div>

      <button type="submit" disabled={!isValid || loading} className="px-btn px-btn-cta px-btn-lg px-btn-block">
        {loading ? (
          <><span className="px-spinner" /> Generating ideas…</>
        ) : (
          <>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2l2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4z" /></svg>
            Generate ideas
          </>
        )}
      </button>
    </form>
  )
}
