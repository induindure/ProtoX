import { useState, useEffect } from 'react'
import { runTests, autoFix } from './api/prototest'
import SummaryBar from './components/SummaryBar'
import FileResultCard from './components/FileResultCard'
import TestExecutionCard from './components/TestExecutionCard'
import FixHistoryCard from './components/FixHistoryCard'

export default function App() {
  const [project, setProject] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [autoFixing, setAutoFixing] = useState(false)
  const [fixHistory, setFixHistory] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const projectId = params.get('id')
    if (projectId) {
      fetch(`http://localhost:8002/api/get-project/${projectId}`)
        .then(res => res.json())
        .then(data => {
          if (data.error) {
            setError(data.error)
          } else {
            setProject(data)
          }
        })
        .catch(() => setError('Could not load project from ProtoCode.'))
    }
  }, [])

  const handleTest = async () => {
    if (!project) return
    setLoading(true)
    setError('')
    setReport(null)
    setFixHistory(null)
    try {
      const data = await runTests(project.files, project.project_name, project.tech_stack)
      setReport(data)
    } catch {
      setError('Testing failed. Make sure the ProtoTest backend is running on port 8002.')
    } finally {
      setLoading(false)
    }
  }

  const handleSendToPreview = async () => {
    try {
      const response = await fetch('http://localhost:8003/api/store-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          files: project.files,
          project_name: project.project_name,
          tech_stack: project.tech_stack,
        }),
      })
      if (!response.ok) throw new Error()
      const data = await response.json()
      window.open(`http://localhost:5176/?id=${data.project_id}`, '_blank')
    } catch {
      setError('Could not send project to Preview.')
    }
  }

  const handleAutoFix = async () => {
    if (!project) return
    setAutoFixing(true)
    setError('')
    try {
      const data = await autoFix(project.files, project.project_name, project.tech_stack)
      setProject({ ...project, files: data.files })
      setFixHistory(data)
      setReport({
        project_name: data.project_name,
        tech_stack: data.tech_stack,
        summary: {
          total: data.final_syntax_results.length,
          syntax_failed: data.final_syntax_results.filter(r => r.syntax.status === 'fail').length,
          tests_passed: data.final_test_execution ? !!data.final_test_execution.passed : false,
        },
        syntax_results: data.final_syntax_results,
        test_execution: data.final_test_execution || {
          ran: false,
          reason: 'Tests were not run because syntax errors remained unresolved.',
        },
      })
    } catch {
      setError('Auto-fix failed. Make sure the ProtoTest backend is running on port 8002.')
    } finally {
      setAutoFixing(false)
    }
  }

  const hasFailures = report && (
    report.summary.syntax_failed > 0 ||
    (report.test_execution.ran && !report.test_execution.passed)
  )

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
            ProtoTest checks your generated project for syntax errors and runs real automated tests against it.
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

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={handleTest}
            disabled={loading || autoFixing || !project}
            style={{
              alignSelf: 'flex-start',
              padding: '0.65rem 2rem',
              background: loading || autoFixing || !project ? '#ccc' : 'var(--accent)',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 700,
              fontSize: '0.95rem',
              cursor: loading || autoFixing || !project ? 'not-allowed' : 'pointer',
              transition: 'background 0.2s',
            }}
          >
            {loading ? 'Running Tests...' : 'Run Tests'}
          </button>

          <button
            onClick={handleSendToPreview}
            disabled={!project}
            style={{
              padding: '0.5rem 1.4rem',
              background: '#2563eb',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: project ? 'pointer' : 'not-allowed',
              opacity: project ? 1 : 0.5,
              letterSpacing: '0.03em',
              transition: 'background 0.2s',
            }}
            onMouseOver={e => { if (project) e.target.style.background = '#1d4ed8' }}
            onMouseOut={e => { e.target.style.background = '#2563eb' }}
          >
            Preview App →
          </button>

          {hasFailures && (
            <button
              onClick={handleAutoFix}
              disabled={loading || autoFixing || !project}
              style={{
                alignSelf: 'flex-start',
                padding: '0.65rem 2rem',
                background: loading || autoFixing || !project ? '#ccc' : 'transparent',
                color: loading || autoFixing || !project ? '#fff' : 'var(--accent)',
                border: '2px solid var(--accent)',
                borderRadius: '6px',
                fontWeight: 700,
                fontSize: '0.95rem',
                cursor: loading || autoFixing || !project ? 'not-allowed' : 'pointer',
                transition: 'background 0.2s',
              }}
            >
              {autoFixing ? 'Fixing & Retesting...' : 'Auto-Fix & Retest'}
            </button>
          )}
        </div>
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
            {fixHistory && <FixHistoryCard data={fixHistory} />}
            <TestExecutionCard execution={report.test_execution} />
            {report.syntax_results.map((r) => (
              <FileResultCard key={r.path} result={r} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}