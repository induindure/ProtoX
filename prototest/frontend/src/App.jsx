import { useState, useEffect } from 'react'
import Header, { Hero, CheckIcon } from './protox/Header'
import { MODULE_URLS, withTheme } from './protox/theme'
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
  const [fixPrompt, setFixPrompt] = useState('')
  const [promptLoading, setPromptLoading] = useState(false)
  const [copied, setCopied] = useState(false)

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
      window.open(withTheme(`${MODULE_URLS.preview}/?id=${data.project_id}`), '_blank')
    } catch {
      setError('Could not send project to Preview.')
    }
  }

  const handleSendToDeploy = async () => {
    try {
      const response = await fetch('http://localhost:8010/api/protodeploy/store-project', {
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
      const name = encodeURIComponent(project.project_name)
      window.open(withTheme(`${MODULE_URLS.deploy}/?id=${data.project_id}&name=${name}`), '_blank')
    } catch {
      setError('Could not send project to ProtoDeploy. Is its backend running on port 8010?')
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

  const handleFixPrompt = async () => {
    if (!project || !report) return
    setPromptLoading(true)
    setFixPrompt('')
    try {
      const ex = report.test_execution || {}
      const syntaxErrors = (report.syntax_results || [])
        .filter(r => r.syntax.status === 'fail')
        .map(r => `${r.path}: ${r.syntax.message}`)
        .join('\n')
      const output = [ex.stdout, ex.stderr, syntaxErrors].filter(Boolean).join('\n')

      const res = await fetch('http://localhost:8002/api/fix-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          files: project.files,
          output,
          test_code: ex.generated_test_code || '',
        }),
      })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setFixPrompt(data.prompt)
    } catch {
      setError('Could not create the fix prompt.')
    } finally {
      setPromptLoading(false)
    }
  }

  const handleCopyPrompt = async () => {
    await navigator.clipboard.writeText(fixPrompt)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const hasFailures = report && (
    report.summary.syntax_failed > 0 ||
    (report.test_execution.ran && !report.test_execution.passed)
  )

  const testsPassed =
    report &&
    report.summary.syntax_failed === 0 &&
    report.test_execution?.passed === true

  const busy = loading || autoFixing

  return (
    <div className="px-page">
      <Header current={3} />

      <Hero step={3} title="Test generated code">
        Checks every file for syntax errors, then runs real automated tests against your project.
      </Hero>

      <main className="px-container px-container-narrow px-stack-lg">
        {project ? (
          <div className="px-card px-between" style={{ padding: '14px 18px' }}>
            <div className="px-row" style={{ gap: 10 }}>
              <span style={{ fontWeight: 700, fontSize: 16 }}>{project.project_name}</span>
              <span className="px-badge px-badge-neutral">{project.tech_stack}</span>
              <span className="px-small px-muted">{project.files.length} files</span>
            </div>

            <div className="px-row" style={{ gap: 8 }}>
              <button onClick={handleTest} disabled={busy || !project} className={`px-btn ${report ? '' : 'px-btn-cta'}`}>
                {loading ? <><span className="px-spinner" /> Running tests…</> : report ? 'Run tests again' : 'Run tests'}
              </button>

              {hasFailures && (
                <button onClick={handleAutoFix} disabled={busy || !project} className="px-btn px-btn-cta">
                  {autoFixing ? <><span className="px-spinner" /> Fixing &amp; retesting…</> : 'Auto-fix & retest'}
                </button>
              )}
              {hasFailures && (
                <button onClick={handleFixPrompt} disabled={promptLoading || !project} className="px-btn px-btn-outline">
                  {promptLoading ? <><span className="px-spinner" /> Writing prompt…</> : 'Get fix prompt for ProtoCode'}
                </button>
              )}

              {testsPassed && (
                <>
                  <button onClick={handleSendToPreview} disabled={!project} className="px-btn px-btn-outline">Preview app →</button>
                  <button onClick={handleSendToDeploy} disabled={!project} className="px-btn px-btn-cta">Deploy →</button>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="px-empty" style={{ padding: '40px 24px' }}>
            <span className="px-empty-icon" aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" /></svg>
            </span>
            <h2>No project received yet</h2>
            <p>Generate code in ProtoCode and click “Send to ProtoTest”. Your project will open here.</p>
            <a href={withTheme(MODULE_URLS.code)} className="px-btn px-btn-outline" style={{ marginTop: 16 }}>Go to ProtoCode</a>
          </div>
        )}

        {error && (
          <div className="px-alert px-alert-err" role="alert">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" /></svg>
            {error}
          </div>
        )}

        {testsPassed && (
          <div className="px-alert px-alert-ok">
            <CheckIcon size={18} />
            <span><strong>Your app is ready to try.</strong> See it running live, or put it online.</span>
          </div>
        )}

        {fixPrompt && (
          <section className="px-card px-stack">
            <div>
              <h2 className="px-h3">Fix prompt for ProtoCode</h2>
              <p className="px-subtitle px-small">Paste it into the ProtoCode chat, then click Send to ProtoTest again.</p>
            </div>
            <label htmlFor="fix-prompt" className="px-sr-only">Fix prompt</label>
            <textarea id="fix-prompt" readOnly value={fixPrompt} rows={6} className="px-textarea px-input-mono" />
            <div>
              <button onClick={handleCopyPrompt} className="px-btn px-btn-primary">
                {copied ? <><CheckIcon /> Copied</> : 'Copy prompt'}
              </button>
            </div>
          </section>
        )}

        {report && (
          <div className="px-stack">
            <SummaryBar summary={report.summary} projectName={report.project_name} techStack={report.tech_stack} />
            {fixHistory && <FixHistoryCard data={fixHistory} />}
            <TestExecutionCard execution={report.test_execution} />
            <section className="px-card px-card-flush">
              <div className="px-card-head">
                <h2 className="px-h3">Files checked</h2>
                <span className="px-small px-muted">
                  {report.syntax_results.length - report.summary.syntax_failed} of {report.syntax_results.length} OK
                </span>
              </div>
              <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                {report.syntax_results.map((r) => (
                  <FileResultCard key={r.path} result={r} />
                ))}
              </ul>
            </section>
          </div>
        )}
      </main>
    </div>
  )
}
