import { useState } from 'react'

async function downloadZip(files, projectName) {
  // Dynamically import JSZip from CDN
  const JSZip = (await import('https://cdn.jsdelivr.net/npm/jszip@3.10.1/+esm')).default
  const zip = new JSZip()
  const folder = zip.folder(projectName || 'protocode-project')

  files.forEach(file => {
    folder.file(file.path, file.content)
  })

  const blob = await zip.generateAsync({ type: 'blob' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${projectName || 'protocode-project'}.zip`
  a.click()
  URL.revokeObjectURL(url)
}

export default function CodeOutput({ file, allFiles, projectName }) {
  const [copied, setCopied] = useState(false)
  const [downloading, setDownloading] = useState(false)

  const handleCopy = () => {
    if (!file) return
    navigator.clipboard.writeText(file.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = async () => {
    setDownloading(true)
    try {
      await downloadZip(allFiles, projectName)
    } catch (e) {
      alert('Download failed: ' + e.message)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

      {/* Toolbar */}
      <div style={{
        padding: '0.65rem 1.25rem',
        borderBottom: '1px solid var(--border)',
        background: '#fff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.82rem',
          color: 'var(--accent)',
          fontWeight: 600,
        }}>
          {file ? file.path : 'Select a file'}
        </span>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={handleCopy}
            disabled={!file}
            style={{
              padding: '0.35rem 0.9rem',
              background: copied ? '#2d6a4f' : 'var(--surface2)',
              color: copied ? '#fff' : 'var(--text)',
              border: '1px solid var(--border)',
              borderRadius: '5px',
              fontSize: '0.8rem',
              cursor: file ? 'pointer' : 'not-allowed',
              fontWeight: 600,
              transition: 'all 0.2s',
            }}
          >
            {copied ? 'Copied' : 'Copy File'}
          </button>

          <button
            onClick={handleDownload}
            disabled={downloading}
            style={{
              padding: '0.35rem 0.9rem',
              background: 'var(--accent)',
              color: '#fff',
              border: 'none',
              borderRadius: '5px',
              fontSize: '0.8rem',
              cursor: downloading ? 'not-allowed' : 'pointer',
              fontWeight: 700,
              letterSpacing: '0.03em',
              transition: 'background 0.2s',
            }}
          >
            {downloading ? 'Downloading...' : 'Download ZIP'}
          </button>
        </div>
      </div>

      {/* Code view */}
      {file ? (
        <div style={{
          flex: 1,
          overflowY: 'auto',
          background: '#fafafa',
          padding: '1.5rem',
        }}>
          <pre style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.83rem',
            lineHeight: 1.9,
            color: '#1a1a1a',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            margin: 0,
          }}>
            {file.content}
          </pre>
        </div>
      ) : (
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)',
          fontSize: '0.88rem',
        }}>
          Select a file from the tree to view its code.
        </div>
      )}
    </div>
  )
}