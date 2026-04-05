import { useState } from 'react'
import type { IdeaModel } from '../types'

interface Props {
  idea: IdeaModel
  index: number
  onSelect?: (idea: IdeaModel) => void
  selected?: boolean
}

export default function IdeaCard({ idea, index, onSelect, selected }: Props) {
  const [expanded, setExpanded] = useState(true)

  return (
    <div
      className={`rounded-xl border-2 transition-all shadow-sm ${
        selected ? 'border-brand-teal bg-teal-50' : 'border-gray-200 bg-white hover:border-teal-300'
      }`}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-5 py-4 cursor-pointer"
        onClick={() => setExpanded(v => !v)}
      >
        <div className="flex items-center gap-3">
          <span className="w-7 h-7 rounded-full bg-brand-teal text-white text-xs font-bold flex items-center justify-center flex-shrink-0">
            {index + 1}
          </span>
          <h3 className="font-semibold text-gray-800 text-base">{idea.title}</h3>
        </div>
        <span className="text-gray-400 text-lg">{expanded ? '▲' : '▼'}</span>
      </div>

      {/* Body */}
      {expanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-gray-100 pt-4">
          {/* Description */}
          <p className="text-sm text-gray-600 leading-relaxed">{idea.description}</p>

          {/* Target Users */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Target Users:</span>
            <span className="text-xs text-gray-700 bg-gray-100 px-2 py-0.5 rounded-full">{idea.target_users}</span>
          </div>

          {/* Features */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Core Features</p>
            <ul className="space-y-1">
              {idea.features.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-brand-teal mt-0.5 flex-shrink-0">›</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>

          {/* Tech hints */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Tech Stack Hints</p>
            <div className="flex flex-wrap gap-1.5">
              {idea.tech_hints.map((t, i) => (
                <span key={i} className="text-xs px-2 py-1 bg-brand-teal text-white rounded-full">{t}</span>
              ))}
            </div>
          </div>

          {/* Select button */}
          {onSelect && (
            <button
              onClick={() => onSelect(idea)}
              className={`w-full mt-2 py-2 rounded-lg text-sm font-semibold transition-all ${
                selected
                  ? 'bg-brand-teal text-white'
                  : 'border border-brand-teal text-brand-teal hover:bg-teal-50'
              }`}
            >
              {selected ? '✓ Selected for ProtoCode' : 'Select this idea →'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
