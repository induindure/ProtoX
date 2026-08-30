# Patch: add "Preview App" button to ProtoCode's App.jsx

## 1. Add this handler next to `handleSendToProtoTest`

```javascript
const handleSendToPreview = async () => {
  try {
    const response = await fetch('http://localhost:8003/api/store-project', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        files: result.files,
        project_name: result.project_name,
        tech_stack: techStack,
      }),
    })
    const data = await response.json()
    window.open(`http://localhost:5176/?id=${data.project_id}`, '_blank')
  } catch {
    setError('Could not send project to Preview.')
  }
}
```

This is a byte-for-byte copy of `handleSendToProtoTest`, just pointed at port
8003 (ProtoPreview backend) and 5176 (ProtoPreview frontend) instead of 8002/5175.

## 2. Add the button next to "Send to ProtoTest →" in the banner

```jsx
<button
  onClick={handleSendToPreview}
  style={{
    padding: '0.5rem 1.4rem',
    background: '#2563eb',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    fontWeight: 700,
    fontSize: '0.85rem',
    cursor: 'pointer',
    letterSpacing: '0.03em',
    marginLeft: '0.75rem',
    transition: 'background 0.2s',
  }}
  onMouseOver={e => e.target.style.background = '#1d4ed8'}
  onMouseOut={e => e.target.style.background = '#2563eb'}
>
  Preview App →
</button>
```

Place it right after the existing "Send to ProtoTest →" button, inside the
same flex container, so the banner shows both actions side by side.

## Nothing else in ProtoCode needs to change

`result.files`, `result.project_name`, and `techStack` are already in scope
in that component — Preview consumes the exact same shape ProtoTest does.
