import { useState, useEffect, useRef } from 'react'
import Header, { CheckIcon, LogoMark } from './protox/Header'
import { MODULE_URLS, withTheme } from './protox/theme'
import IdeaPanel from './components/IdeaPanel'
import TechSelector from './components/TechSelector'
import DatabaseUrlInput from './components/DatabaseUrlInput'
import FileTree from './components/FileTree'
import CodeOutput from './components/CodeOutput'
import ChatPanel from './components/ChatPanel'
import { generateCode, chatEdit } from './api/protocode'
import { getDatabaseUrlError } from './utils/databaseUrl'
import SupabaseGuide from './components/SupabaseGuide'

export default function App() {
  const [idea, setIdea] = useState(null)
  const [techStack, setTechStack] = useState('')
  const [databaseUrl, setDatabaseUrl] = useState('')
  const [result, setResult] = useState(null)
  const [previousResult, setPreviousResult] = useState(null) // one undo level
  const [generation, setGeneration] = useState(0)            // bumps on each fresh generate
  const [selectedFile, setSelectedFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const outputRef = useRef(null)
  const databaseUrlError = getDatabaseUrlError(databaseUrl)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const ideaParam = params.get('idea')
    if (ideaParam) {
      try {
        setIdea(JSON.parse(decodeURIComponent(ideaParam)))
      } catch {
        setError('Could not load idea from ProtoIdea.')
      }
    }
  }, [])

  // Auto-scroll only when a NEW generation arrives (not on chat edits)
  useEffect(() => {
    if (generation > 0 && outputRef.current) {
      setTimeout(() => {
        outputRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
    }
  }, [generation])

  const handleGenerate = async () => {
    if (!idea) return setError('No idea received from ProtoIdea yet.')
    if (!techStack) return setError('Please choose an app type.')
    if (databaseUrlError) return setError(databaseUrlError)
    setError('')
    setLoading(true)
    setResult(null)
    setPreviousResult(null)
    setSelectedFile(null)
    try {
      const ideaSummary = `
        App: ${idea.title}
        Description: ${idea.description}
        Target Users: ${idea.target_users}
        Core Features: ${idea.features.join(', ')}
      `.trim()
      const data = await generateCode(ideaSummary, techStack, databaseUrl)
      setResult(data)
      setGeneration(g => g + 1)
      if (data.files?.length > 0) setSelectedFile(data.files[0])
    } catch {
      setError('Code generation failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleFileClick = (filePath) => {
    const file = result?.files.find(f => f.path === filePath)
    if (file) setSelectedFile(file)
  }

  // Called by ChatPanel. Returns a summary for the panel, throws on failure.
  const handleChatEdit = async (instruction) => {
    const data = await chatEdit(instruction, result.files, techStack)
    const patches = data.files || []

    if (patches.length === 0) {
      return { explanation: data.explanation, changed: [], created: [] }
    }

    const patchMap = new Map(patches.map(p => [p.path, p.content]))
    const existing = new Set(result.files.map(f => f.path))

    const updatedFiles = result.files.map(f =>
      patchMap.has(f.path) ? { ...f, content: patchMap.get(f.path) } : f
    )
    const createdPatches = patches.filter(p => !existing.has(p.path))
    createdPatches.forEach(p => updatedFiles.push({ path: p.path, content: p.content }))

    setPreviousResult(result) // snapshot before applying
    setResult({ ...result, files: updatedFiles })

    // keep the open file in sync with the edit
    if (selectedFile && patchMap.has(selectedFile.path)) {
      setSelectedFile({ ...selectedFile, content: patchMap.get(selectedFile.path) })
    }

    return {
      explanation: data.explanation,
      changed: patches.filter(p => existing.has(p.path)).map(p => p.path),
      created: createdPatches.map(p => p.path),
    }
  }

  const handleUndo = () => {
    if (!previousResult) return
    setResult(previousResult)
    const stillThere = previousResult.files.find(f => f.path === selectedFile?.path)
    setSelectedFile(stillThere || previousResult.files[0] || null)
    setPreviousResult(null)
  }

  const handleSendToProtoTest = async () => {
    try {
      const response = await fetch('http://localhost:8002/api/store-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          files: result.files,
          project_name: result.project_name,
          tech_stack: techStack,
        }),
      })
      const data = await response.json()
      window.open(withTheme(`${MODULE_URLS.test}/?id=${data.project_id}`), '_blank')
    } catch {
      setError('Could not send project to ProtoTest.')
    }
  }

  const blocked = loading || !idea || Boolean(databaseUrlError)

  return (
    <div className="px-page">
      <Header current={2} />

      <div className="px-sidebar-layout">
        <aside className={`px-sidebar ${result ? '' : 'is-wide'}`} aria-label="Code settings">
          <div>
            <p className="px-eyebrow">Step 2 of 5</p>
            <h1 className="px-hero-title" style={{ fontSize: result ? 22 : 28, marginTop: 6 }}>Generate project code</h1>
          </div>

          <IdeaPanel idea={idea} />
          <TechSelector techStack={techStack} setTechStack={setTechStack} />
          <DatabaseUrlInput databaseUrl={databaseUrl} setDatabaseUrl={setDatabaseUrl} />
          <SupabaseGuide />

          {error && (
            <div className="px-alert px-alert-err" role="alert">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" /></svg>
              {error}
            </div>
          )}

          <button onClick={handleGenerate} disabled={blocked} className="px-btn px-btn-cta px-btn-lg px-btn-block">
            {loading ? (
              <><span className="px-spinner" /> Generating code…</>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M16 18l6-6-6-6M8 6l-6 6 6 6" /></svg>
                {result ? 'Generate again' : 'Generate code'}
              </>
            )}
          </button>
        </aside>

        <main className={`px-sidebar-main ${result ? '' : 'is-narrow'}`}>
          {!result && !loading && (
            <div className="px-empty" style={{ flex: 1, justifyContent: 'center' }}>
              <div style={{ marginBottom: 14 }}><LogoMark size={48} /></div>
              <h2>Your code will appear here</h2>
              <p>Pick an app type, paste your database URL, then click Generate code. You can then browse the files and ask for changes in chat.</p>
            </div>
          )}

          {loading && (
            <div className="px-card px-stack" aria-live="polite" style={{ flex: 1 }}>
              <div className="px-row" style={{ color: 'var(--accent-text)', fontWeight: 600 }}>
                <span className="px-spinner" /> Writing your project… this can take a minute.
              </div>
              {[70, 90, 55, 80, 40].map((w, i) => <div key={i} className="px-skeleton" style={{ height: 12, width: `${w}%` }} />)}
            </div>
          )}

          {result && !loading && (
            <>
              <div ref={outputRef} className="px-between" style={{ scrollMarginTop: 80 }}>
                <div className="px-row" style={{ gap: 10 }}>
                  <span className="px-badge px-badge-ok"><CheckIcon size={14} /> {result.files.length} files ready</span>
                  <span className="px-small px-muted">Browse the files, ask for changes, then run tests.</span>
                </div>
                <button onClick={handleSendToProtoTest} className="px-btn px-btn-cta">Send to ProtoTest →</button>
              </div>

              <section className="px-card px-card-flush px-workspace is-two">
                <FileTree tree={result.file_tree} onFileClick={handleFileClick} selectedPath={selectedFile?.path} />
                <CodeOutput file={selectedFile} allFiles={result.files} projectName={result.project_name} />
                <ChatPanel
                  key={generation}  /* fresh chat for each new generation */
                  onSend={handleChatEdit}
                  onUndo={handleUndo}
                  canUndo={!!previousResult}
                />
              </section>
            </>
          )}
        </main>
      </div>
    </div>
  )
}
