import { useState } from 'react'
import type { IdeaModel } from '../types'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
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
      content: `I've selected "${idea.title}" for refinement. What would you like to change or improve about this idea? You can mention specific features, target audience, tech stack, or any other aspect.`,
      timestamp: new Date(),
    }
  ])
  const [input, setInput] = useState('')
  const [refining, setRefining] = useState(false)
  const [currentIdea, setCurrentIdea] = useState(idea)

  const handleSend = async () => {
    if (!input.trim()) return

    // Add user message
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setRefining(true)

    try {
      const refined = await onRefine(input)
      setCurrentIdea(refined)

      // Add assistant response
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I've updated "${refined.title}" based on your feedback. Here's what changed:\n\n✓ Updated features and focus\n✓ Refined target users\n✓ Adjusted tech stack if needed\n\nWould you like more changes, or are you ready to finalize?`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (error) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I had trouble refining that idea. Could you try again with different feedback?',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setRefining(false)
    }
  }

  return (
    <div className="rounded-xl border-2 border-brand-teal bg-white shadow-lg overflow-hidden flex flex-col h-full">
      {/* Header */}
      <div className="bg-gradient-to-r from-brand-teal to-teal-600 text-white px-5 py-4">
        <h3 className="font-bold text-lg">{currentIdea.title}</h3>
        <p className="text-sm text-teal-100 mt-1">Refine this idea with your feedback</p>
      </div>

      {/* Current Idea Summary */}
      <div className="px-5 py-3 bg-teal-50 border-b border-teal-200">
        <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Current Version</p>
        <p className="text-sm text-gray-700">{currentIdea.description}</p>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 bg-gray-50 min-h-96">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs px-4 py-2 rounded-lg text-sm ${
                msg.role === 'user'
                  ? 'bg-brand-teal text-white rounded-br-none'
                  : 'bg-white text-gray-800 border border-gray-200 rounded-bl-none'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {refining && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-800 border border-gray-200 px-4 py-2 rounded-lg rounded-bl-none">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-brand-teal rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-brand-teal rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-brand-teal rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 px-5 py-3 space-y-2 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Describe what you'd like to change..."
            disabled={loading || refining}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal disabled:bg-gray-100"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading || refining}
            className="px-4 py-2 bg-brand-teal text-white rounded-lg text-sm font-semibold hover:bg-teal-600 disabled:bg-gray-300 transition-all"
          >
            Send
          </button>
        </div>
        <button
          onClick={onFinalize}
          disabled={loading || refining}
          className="w-full px-4 py-2 bg-brand-red text-white rounded-lg text-sm font-semibold hover:bg-red-700 disabled:bg-gray-300 transition-all"
        >
          ✓ Finalize & Move to ProtoCode
        </button>
      </div>
    </div>
  )
}
