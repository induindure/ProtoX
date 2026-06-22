function getFileIcon(name) {
  if (name.endsWith('.jsx') || name.endsWith('.tsx')) return '◈'
  if (name.endsWith('.js') || name.endsWith('.ts')) return '◇'
  if (name.endsWith('.py')) return '◆'
  if (name.endsWith('.css')) return '◎'
  if (name.endsWith('.json')) return '❖'
  if (name.endsWith('.md')) return '◉'
  if (name.includes('.env')) return '◐'
  if (name.endsWith('.html')) return '◑'
  return '◇'
}

function TreeNode({ name, node, path, onFileClick, selectedPath }) {
  const isFolder = node !== null && typeof node === 'object'
  const fullPath = path ? `${path}/${name}` : name
  const isSelected = fullPath === selectedPath

  if (isFolder) {
    return (
      <div style={{ marginBottom: '0.1rem' }}>
        <div style={{
          padding: '0.3rem 0.75rem',
          fontSize: '0.75rem',
          fontWeight: 700,
          color: 'var(--text-muted)',
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          marginTop: '0.6rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
        }}>
          <span style={{ fontSize: '0.7rem' }}>▸</span> {name}
        </div>
        <div style={{ paddingLeft: '0.75rem', borderLeft: '1px solid var(--border)', marginLeft: '1rem' }}>
          {Object.entries(node).map(([childName, childNode]) => (
            <TreeNode
              key={childName}
              name={childName}
              node={childNode}
              path={fullPath}
              onFileClick={onFileClick}
              selectedPath={selectedPath}
            />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div
      onClick={() => onFileClick(fullPath)}
      style={{
        padding: '0.3rem 0.75rem',
        borderRadius: '4px',
        cursor: 'pointer',
        fontSize: '0.83rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        background: isSelected ? 'var(--accent)' : 'transparent',
        color: isSelected ? '#fff' : 'var(--text)',
        marginBottom: '1px',
        transition: 'background 0.15s',
        userSelect: 'none',
      }}
      onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = 'var(--surface2)' }}
      onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent' }}
    >
      <span style={{ fontSize: '0.7rem', opacity: 0.7 }}>{getFileIcon(name)}</span>
      {name}
    </div>
  )
}

export default function FileTree({ tree, onFileClick, selectedPath }) {
  return (
    <div style={{
      width: '220px',
      minWidth: '220px',
      background: 'var(--surface)',
      borderRight: '1px solid var(--border)',
      padding: '1rem 0.5rem',
      overflowY: 'auto',
    }}>
      <p style={{
        fontSize: '0.7rem',
        color: 'var(--text-light)',
        fontWeight: 700,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        padding: '0 0.75rem',
        marginBottom: '0.75rem',
      }}>
        Project Files
      </p>
      {Object.entries(tree).map(([name, node]) => (
        <TreeNode
          key={name}
          name={name}
          node={node}
          path=""
          onFileClick={onFileClick}
          selectedPath={selectedPath}
        />
      ))}
    </div>
  )
}