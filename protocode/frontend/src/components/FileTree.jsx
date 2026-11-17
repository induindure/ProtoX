function FileIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.7, flexShrink: 0 }} aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" />
    </svg>
  )
}

function FolderIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }} aria-hidden="true">
      <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    </svg>
  )
}

function TreeNode({ name, node, path, onFileClick, selectedPath }) {
  const isFolder = node !== null && typeof node === 'object'
  const fullPath = path ? `${path}/${name}` : name
  const isSelected = fullPath === selectedPath

  if (isFolder) {
    return (
      <li>
        <div className="px-tree-folder"><FolderIcon /> {name}</div>
        <ul className="px-tree">
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
        </ul>
      </li>
    )
  }

  return (
    <li>
      <button
        type="button"
        onClick={() => onFileClick(fullPath)}
        className={`px-tree-file ${isSelected ? 'is-selected' : ''}`}
        aria-current={isSelected ? 'true' : undefined}
      >
        <FileIcon /> {name}
      </button>
    </li>
  )
}

export default function FileTree({ tree, onFileClick, selectedPath }) {
  return (
    <nav className="px-pane" aria-label="Project files">
      <div className="px-pane-head">
        <span className="px-section-label">Project files</span>
      </div>
      <div className="px-pane-body" style={{ padding: 8 }}>
        <ul className="px-tree">
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
        </ul>
      </div>
    </nav>
  )
}
