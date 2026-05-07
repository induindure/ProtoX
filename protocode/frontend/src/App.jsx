import { useState, useEffect } from 'react'
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

  // Read idea from localStorage (sent by protoidea)
  useEffect(() => {
    const stored = localStorage.getItem('protocode_idea')
    if (stored) {
      try {
        setIdea(JSON.parse(stored))
      } catch {
        setError('Could not load idea from ProtoIdea.')
      }
    }
  }, [])

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

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>

      {/* Header — matches protoidea */}
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
      )}
    </div>
  )
}