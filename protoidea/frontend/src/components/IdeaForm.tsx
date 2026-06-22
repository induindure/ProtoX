import { useState } from 'react'
import type { IdeaRequest } from '../types'

interface Props {
  onSubmit: (req: IdeaRequest) => void
  loading: boolean
}

const APP_TYPES = ['Web App', 'Mobile App', 'CLI Tool', 'API / Backend Service', 'Desktop App', 'Browser Extension']
const DOMAINS = ['Healthcare', 'Education', 'Finance', 'E-Commerce', 'Social Media', 'Productivity', 'Entertainment', 'Travel', 'Food & Nutrition', 'Other']

export default function IdeaForm({ onSubmit, loading }: Props) {
  const [domain, setDomain] = useState('')
  const [customDomain, setCustomDomain] = useState('')
  const [appType, setAppType] = useState('')
  const [constraints, setConstraints] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const finalDomain = domain === 'Other' ? customDomain.trim() : domain
    if (!finalDomain || !appType) return
    onSubmit({ domain: finalDomain, app_type: appType, constraints: constraints.trim() || undefined })
  }

  const isValid = (domain === 'Other' ? customDomain.trim().length > 0 : domain.length > 0) && appType.length > 0

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-md p-8 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-1">Generate App Ideas</h2>
        <p className="text-sm text-gray-500">ProtoIdea generates 3-5 scoped, buildable app ideas.</p>
      </div>

      {/* Domain */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">Domain <span className="text-red-600">*</span></label>
        <select
          value={domain}
          onChange={e => setDomain(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
        >
          <option value="">Select a domain...</option>
          {DOMAINS.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        {domain === 'Other' && (
          <input
            type="text"
            placeholder="Enter your domain (e.g. Agriculture)"
            value={customDomain}
            onChange={e => setCustomDomain(e.target.value)}
            className="mt-2 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
        )}
      </div>

      {/* App Type */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">App Type <span className="text-red-600">*</span></label>
        <div className="flex flex-wrap gap-2">
          {APP_TYPES.map(type => (
            <button
              key={type}
              type="button"
              onClick={() => setAppType(type)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-all ${
                appType === type
                  ? 'bg-brand-teal text-white border-brand-teal'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-teal-400'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Constraints */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">
          Constraints <span className="text-gray-400 font-normal">(optional)</span>
        </label>
        <textarea
          rows={3}
          placeholder="e.g. must be free to use, simple UI, no login required, target college students..."
          value={constraints}
          onChange={e => setConstraints(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none"
        />
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={!isValid || loading}
        className="w-full bg-brand-red text-white font-semibold py-3 rounded-lg hover:bg-red-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            Generating ideas...
          </>
        ) : (
          'Generate Ideas'
        )}
      </button>
    </form>
  )
}
