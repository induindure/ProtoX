import { useState, useEffect } from 'react'
import { runTests } from './api/prototest'
import SummaryBar from './components/SummaryBar'
import FileResultCard from './components/FileResultCard'

export default function App() {
  const [project, setProject] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const raw = params.get('project')
    if (raw) {
      try {
        setProject(JSON.parse(decodeURIComponent(raw)))
      } catch {
        setError('Could not load project from ProtoCode.')
      }
    }
  }, [])

  const handleTest = async () => {
    if (!project) return
    setLoading(true)
    setError('')
    setReport(null)
    try {
      const data = await runTests(project.files, project.project_name, project.tech_stack)
      setReport(data)
    } catch {
      setError('Testing failed. Make sure the ProtoTest backend is running on port 8002.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg)' }}>

      {/* Header */}
      <header style={{
        padding: '0.9rem 2rem',
        borderBottom: '3px solid var(--accent)',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        background: '#fff',
      }}>
        <span style={{ fontWeight: 800, fontSize: '1.2rem', color: 'var(--text)', letterSpacing: '-0.5px' }}>
          ProtoX
        </span>
        <span style={{
          background: 'var(--accent)',
          color: '#fff',
          fontSize: '0.75rem',
          fontWeight: 700,
          padding: '0.2rem 0.6rem',
          borderRadius: '999px',
        }}>
          ProtoTest
        </span>
        <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          K. J. Somaiya School of Engineering · B.Tech FYP 2025–27
        </span>
      </header>

      {/* Input section */}
      <div style={{
        padding: '2rem',
        background: '#fff',
        borderBottom: '1px solid var(--border)',
        maxWidth: '860px',
        width: '100%',
        alignSelf: 'center',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.3rem' }}>
            Test Generated Code
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            ProtoTest checks your generated project for syntax errors and reviews code quality using AI.
          </p>
        </div>

        {project ? (
          <div style={{
            padding: '0.85rem 1.25rem',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            fontSize: '0.88rem',
            color: 'var(--text)',
          }}>
            <strong>{project.project_name}</strong>
            <span style={{ color: 'var(--text-muted)', marginLeft: '0.75rem' }}>{project.tech_stack}</span>
            <span style={{ color: 'var(--text-muted)', marginLeft: '0.75rem' }}>· {project.files.length} files</span>
          </div>
        ) : (
          <div style={{
            padding: '0.85rem 1.25rem',
            background: '#fef9c3',
            borderRadius: '8px',
            fontSize: '0.88rem',
            color: '#854d0e',
          }}>
            ⚠️ No project received. Please go back to ProtoCode and click "Send to ProtoTest".
          </div>
        )}

        {error && <p style={{ color: 'var(--accent)', fontSize: '0.85rem', fontWeight: 500 }}>{error}</p>}

        <button
          onClick={handleTest}
          disabled={loading || !project}
          style={{
            alignSelf: 'flex-start',
            padding: '0.65rem 2rem',
            background: loading || !project ? '#ccc' : 'var(--accent)',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 700,
            fontSize: '0.95rem',
            cursor: loading || !project ? 'not-allowed' : 'pointer',
            transition: 'background 0.2s',
          }}
        >
          {loading ? 'Running Tests...' : 'Run Tests'}
        </button>
      </div>

      {/* Results */}
      {report && (
        <div style={{ maxWidth: '860px', width: '100%', alignSelf: 'center', padding: '0 0 3rem' }}>
          <SummaryBar
            summary={report.summary}
            projectName={report.project_name}
            techStack={report.tech_stack}
          />
          <div style={{ padding: '1.5rem 2rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {report.results.map((r) => (
              <FileResultCard key={r.path} result={r} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}