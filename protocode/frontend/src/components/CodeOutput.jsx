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
    <div className="px-pane" style={{ background: 'var(--code-bg)' }}>
      <div className="px-pane-head">
        <span className="px-mono" style={{ fontSize: 13, color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', minWidth: 0 }}>
          {file ? file.path : 'Select a file'}
        </span>
        <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
          <button onClick={handleCopy} disabled={!file} className="px-btn px-btn-sm">
            {copied ? 'Copied' : 'Copy'}
          </button>
          <button onClick={handleDownload} disabled={downloading} className="px-btn px-btn-sm px-btn-outline">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" /></svg>
            {downloading ? 'Preparing…' : 'Download ZIP'}
          </button>
        </div>
      </div>

      {file ? (
        <pre className="px-code px-code-wrap px-pane-body">{file.content}</pre>
      ) : (
        <div className="px-pane-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)' }}>
          Select a file from the tree to view its code.
        </div>
      )}
    </div>
  )
}
