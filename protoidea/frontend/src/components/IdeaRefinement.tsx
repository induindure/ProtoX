import { useEffect, useRef, useState } from 'react'
import type { IdeaModel } from '../types'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

interface Props {
  idea: IdeaModel
  onRefine: (feedback: string) => Promise<IdeaModel>
  onFinalize: () => void
  loading?: boolean
}

export default function IdeaRefinement({ idea, onRefine, onFinalize, loading }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Let’s shape “${idea.title}”. What would you like to change? Mention features, target users, tech stack or anything else.`,
    },
  ])
  const [input, setInput] = useState('')
  const [refining, setRefining] = useState(false)
  const [currentIdea, setCurrentIdea] = useState(idea)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [messages, refining])

  const handleSend = async () => {
    const text = input.trim()
    if (!text || refining) return

    setMessages((prev) => [...prev, { id: Date.now().toString(), role: 'user', content: text }])
    setInput('')
    setRefining(true)

    try {
      const refined = await onRefine(text)
      setCurrentIdea(refined)
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Updated “${refined.title}” with your feedback. Want more changes, or ready to send it to ProtoCode?`,
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), role: 'assistant', content: 'Sorry, I couldn’t refine that. Try rephrasing your feedback.' },
      ])
    } finally {
      setRefining(false)
    }
  }

  return (
    <div className="px-card px-card-flush" style={{ border: '2px solid var(--accent)' }}>
      <div style={{ padding: '18px 20px', background: 'var(--hero)', borderBottom: '1px solid var(--border)' }}>
        <p className="px-eyebrow">Refining</p>
        <h3 className="px-h2" style={{ marginTop: 4 }}>{currentIdea.title}</h3>
        <p className="px-subtitle">{currentIdea.description}</p>
        {currentIdea.features.length > 0 && (
          <div className="px-chips" style={{ marginTop: 10 }}>
            {currentIdea.features.map((f, i) => <span key={i} className="px-chip">{f}</span>)}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: 20, minHeight: 260, maxHeight: 420, overflowY: 'auto' }} aria-live="polite">
        {messages.map((msg) => (
          <div key={msg.id} className={`px-msg ${msg.role === 'user' ? 'px-msg-user' : 'px-msg-bot'}`}>{msg.content}</div>
        ))}
        {refining && (
          <div className="px-msg px-msg-bot" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="px-spinner" /> Refining…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="px-stack" style={{ padding: 16, borderTop: '1px solid var(--border)', gap: 10 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <label htmlFor="refine-input" className="px-sr-only">Describe what you’d like to change</label>
          <input
            id="refine-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Describe what you’d like to change…"
            disabled={loading || refining}
            className="px-input"
          />
          <button type="button" onClick={handleSend} disabled={!input.trim() || loading || refining} className="px-btn px-btn-primary">
            Send
          </button>
        </div>
        <button type="button" onClick={onFinalize} disabled={loading || refining} className="px-btn px-btn-cta px-btn-lg px-btn-block">
          Finalize &amp; open ProtoCode →
        </button>
      </div>
    </div>
  )
}
