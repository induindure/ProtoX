import { useEffect, useState } from 'react'
import Header, { Hero } from './protox/Header'
import { MODULE_URLS, withTheme } from './protox/theme'
import PreviewWindow from './PreviewWindow'

export default function App() {
  const [projectId, setProjectId] = useState(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const id = params.get('id')
    if (id) setProjectId(id)
  }, [])

  return (
    <div className="px-page">
      <Header current={4} />

      <Hero step={4} title="Preview your app">
        Your generated app running live. Try it out, and if something looks wrong we’ll write a fix request for ProtoCode.
      </Hero>

      <main className="px-container">
        {projectId ? (
          <PreviewWindow projectId={projectId} />
        ) : (
          <div className="px-empty">
            <span className="px-empty-icon" aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="M10 9l5 3-5 3z" /></svg>
            </span>
            <h2>No app to preview yet</h2>
            <p>Run tests in ProtoTest and click “Preview app”. Your app will start here.</p>
            <a href={withTheme(MODULE_URLS.test)} className="px-btn px-btn-outline" style={{ marginTop: 16 }}>Go to ProtoTest</a>
          </div>
        )}
      </main>
    </div>
  )
}
