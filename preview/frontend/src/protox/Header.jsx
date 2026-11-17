import { useEffect, useState } from 'react'
import { MODULE_URLS, applyTheme, currentTheme, watchTheme, withTheme } from './theme'

const STEPS = [
  { n: 1, label: 'Idea', href: MODULE_URLS.idea },
  { n: 2, label: 'Code', href: MODULE_URLS.code },
  { n: 3, label: 'Test', href: MODULE_URLS.test },
  { n: 4, label: 'Preview', href: MODULE_URLS.preview },
  { n: 5, label: 'Deploy', href: MODULE_URLS.deploy },
]

export function LogoMark({ size = 30 }) {
  return (
    <svg className="px-logo-mark" width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <rect className="px-logo-bg" width="64" height="64" rx="16" />
      <path className="px-logo-brackets" d="M18 22l-8 10 8 10M46 22l8 10-8 10" strokeWidth="4.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path className="px-logo-x" d="M26 24l12 16M38 24L26 40" strokeWidth="5" strokeLinecap="round" />
    </svg>
  )
}

export function Wordmark() {
  return <span className="px-wordmark"><b>&lt;</b>protox<b>/&gt;</b></span>
}

export function CheckIcon({ size = 12 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 12l5 5L20 7" />
    </svg>
  )
}

export default function Header({ current = 0, minimal = false, children }) {
  const [theme, setTheme] = useState(currentTheme)
  const dark = theme === 'dark'

  // follow theme changes made on any other ProtoX page
  useEffect(() => watchTheme(setTheme), [])

  const toggle = () => {
    const next = dark ? 'light' : 'dark'
    applyTheme(next)
    setTheme(next)
  }

  return (
    <header className="px-header">
      <div className="px-header-inner">
        <a className="px-logo" href={withTheme(MODULE_URLS.idea)} aria-label="ProtoX home">
          <LogoMark />
          <Wordmark />
        </a>

        {/* Progress only, not links: moving between modules happens through the
            "Send to …" buttons, which carry your work along. */}
        {!minimal && (
        <ol className="px-steps" aria-label="ProtoX progress">
          {STEPS.map((step, i) => {
            const state = step.n < current ? 'done' : step.n === current ? 'current' : 'todo'
            return (
              <li key={step.n}>
                {i > 0 && <span className="px-step-sep" aria-hidden="true">›</span>}
                <span className={`px-step is-${state}`} aria-current={state === 'current' ? 'step' : undefined}>
                  <span className="px-step-dot">{state === 'done' ? <CheckIcon /> : step.n}</span>
                  {step.label}
                  {state === 'done' && <span className="px-sr-only"> (done)</span>}
                </span>
              </li>
            )
          })}
        </ol>
        )}

        <div className="px-header-actions">
          {children}
          <button
            type="button"
            className="px-icon-btn"
            onClick={toggle}
            aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
            title={dark ? 'Light theme' : 'Dark theme'}
          >
            {dark ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </header>
  )
}

/** The soft aurora band with the page title, used under the header on every screen. */
export function Hero({ step, title, children, compact = false, aside = null }) {
  return (
    <div className={`px-hero ${compact ? 'is-compact' : ''}`}>
      <div className="px-hero-inner">
        <div className={compact ? 'px-hero-head' : undefined}>
          <p className="px-eyebrow">Step {step} of 5</p>
          <h1 className="px-hero-title">{title}</h1>
          {children && <p className="px-hero-text">{children}</p>}
        </div>
        {aside && <div className="px-hero-aside">{aside}</div>}
      </div>
    </div>
  )
}
