import { useEffect, useState } from 'react'
import PreviewWindow from './PreviewWindow'

export default function App() {
  const [projectId, setProjectId] = useState(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const id = params.get('id')
    if (id) setProjectId(id)
  }, [])

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{
        padding: '0.9rem 2rem',
        borderBottom: '3px solid var(--accent, #e11d48)',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        background: '#fff',
      }}>
        <span style={{ fontWeight: 800, fontSize: '1.2rem', color: '#1a1a1a', letterSpacing: '-0.5px' }}>
          ProtoX
        </span>
        <span style={{
          background: '#2563eb',
          color: '#fff',
          fontSize: '0.75rem',
          fontWeight: 700,
          padding: '0.2rem 0.6rem',
          borderRadius: '999px',
          letterSpacing: '0.03em',
        }}>
          ProtoPreview
        </span>
      </header>

      {projectId ? (
        <PreviewWindow projectId={projectId} />
      ) : (
        <div style={{ padding: '2rem', color: '#666' }}>
          No project id found. Open this page from ProtoCode's "Preview App" button.
        </div>
      )}
    </div>
  )
}
