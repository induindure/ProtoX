import { useState, useEffect, useRef } from 'react'
import IdeaPanel from './components/IdeaPanel'
import TechSelector from './components/TechSelector'
import FileTree from './components/FileTree'
import CodeOutput from './components/CodeOutput'
import { generateCode } from './api/protocode'

export default function App() {
  const [idea, setIdea] = useState(null)
  const [techStack, setTechStack] = useState('')
  const [result, setResult] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const outputRef = useRef(null)  // 👈 ref for auto-scroll

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

  // Auto-scroll when result arrives 👇
  useEffect(() => {
    if (result && outputRef.current) {
      setTimeout(() => {
        outputRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
    }
  }, [result])

  const handleGenerate = async () => {
    if (!idea) return setError('No idea received from ProtoIdea yet.')
    if (!techStack) return setError('Please select a tech stack.')
    setError('')
    setLoading(true)
    setResult(null)
    setSelectedFile(null)
    try {
      const ideaSummary = `
        App: ${idea.title}
        Description: ${idea.description}
        Target Users: ${idea.target_users}
        Core Features: ${idea.features.join(', ')}
      `.trim()
      const data = await generateCode(ideaSummary, techStack)
      setResult(data)
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

  const handleSendToProtoTest = () => {
    const payload = encodeURIComponent(JSON.stringify({
      files: result.files,
      project_name: result.project_name,
      tech_stack: techStack,
    }))
    window.open(`http://localhost:5175/?project=${payload}`, '_blank')
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>

      {/* Header */}
      <header style={{
        padding: '0.9rem 2rem',
        borderBottom: '3px solid var(--accent)',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        background: '#fff',
      }}>
        <span style={{ fontWeight: 800, fontSize: '1.2rem', color: '#1a1a1a', letterSpacing: '-0.5px' }}>
          ProtoX
        </span>
        <span style={{
          background: 'var(--accent)',
          color: '#fff',
          fontSize: '0.75rem',
          fontWeight: 700,
          padding: '0.2rem 0.6rem',
          borderRadius: '999px',
          letterSpacing: '0.03em',
        }}>
          ProtoCode
        </span>
        <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          K. J. Somaiya School of Engineering · B.Tech FYP 2025–27
        </span>
      </header>

      {/* Input Section */}
      <div style={{
        padding: '2rem',
        borderBottom: '1px solid var(--border)',
        background: '#fff',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.5rem',
        maxWidth: '860px',
        width: '100%',
        alignSelf: 'center',
      }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.3rem' }}>
            Generate Project Code
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            ProtoCode turns your refined idea into a working starter project.
          </p>
        </div>

        <IdeaPanel idea={idea} />
        <TechSelector techStack={techStack} setTechStack={setTechStack} />

        {error && (
          <p style={{ color: 'var(--accent)', fontSize: '0.85rem', fontWeight: 500 }}>{error}</p>
        )}

        <button
          onClick={handleGenerate}
          disabled={loading || !idea}
          style={{
            alignSelf: 'flex-start',
            padding: '0.65rem 2rem',
            background: loading || !idea ? '#ccc' : 'var(--accent)',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 700,
            fontSize: '0.95rem',
            cursor: loading || !idea ? 'not-allowed' : 'pointer',
            letterSpacing: '0.03em',
            transition: 'background 0.2s',
          }}
        >
          {loading ? 'Generating...' : 'Generate Code'}
        </button>
      </div>

      {/* Output Section */}
      {result && (
        <div ref={outputRef}>  {/* 👈 scroll target */}

          {/* Send to ProtoTest banner */}
          <div style={{
            padding: '1rem 2rem',
            background: '#f0fdf4',
            borderBottom: '1px solid #bbf7d0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <div>
              <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#166534' }}>
                Code generated successfully!
              </span>
              <span style={{ color: '#166534', fontSize: '0.85rem', marginLeft: '0.75rem' }}>
                Ready to test your project?
              </span>
            </div>
            <button
              onClick={handleSendToProtoTest}
              style={{
                padding: '0.5rem 1.4rem',
                background: '#16a34a',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
                letterSpacing: '0.03em',
                transition: 'background 0.2s',
              }}
              onMouseOver={e => e.target.style.background = '#15803d'}
              onMouseOut={e => e.target.style.background = '#16a34a'}
            >
              Send to ProtoTest →
            </button>
          </div>

          {/* File viewer */}
          <div style={{
            display: 'flex',
            flex: 1,
            overflow: 'hidden',
            height: 'calc(100vh - 280px)',
          }}>
            <FileTree
              tree={result.file_tree}
              onFileClick={handleFileClick}
              selectedPath={selectedFile?.path}
            />
            <CodeOutput
              file={selectedFile}
              allFiles={result.files}
              projectName={result.project_name}
            />
          </div>
        </div>
      )}
    </div>
  )
}