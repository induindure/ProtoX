import type { ReactNode } from 'react'

import Header, { LogoMark } from '../../protox/Header'

const STEPS = ['Idea', 'Code', 'Test', 'Preview', 'Deploy']

export default function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="px-page">
      <Header minimal />

      <main className="px-hero" style={{ flex: 1, borderBottom: 0 }}>
        <div className="px-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 32, paddingTop: 56 }}>
          <div style={{ textAlign: 'center', maxWidth: 560 }}>
            <div style={{ display: 'flex', justifyContent: 'center' }}><LogoMark size={56} /></div>
            <h1 className="px-hero-title" style={{ marginTop: 16 }}>From idea to deployed app</h1>
            <p className="px-hero-text" style={{ marginInline: 'auto' }}>
              Generate, code, test, preview and deploy, all in one pipeline.
            </p>
            <div className="px-chips" style={{ justifyContent: 'center', marginTop: 16 }}>
              {STEPS.map((s, i) => (
                <span key={s} className="px-chip" style={{ fontWeight: 600, color: 'var(--muted)' }}>
                  <span className="px-mono" style={{ color: 'var(--accent-text)' }}>{i + 1}</span>
                  {s}
                </span>
              ))}
            </div>
          </div>

          <div className="px-card" style={{ width: '100%', maxWidth: 420, padding: 32 }}>
            {children}
          </div>
        </div>
      </main>
    </div>
  )
}
