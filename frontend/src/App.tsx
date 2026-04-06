import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import IdeaForm from './components/IdeaForm'
import IdeaCard from './components/IdeaCard'
import HistoryPanel from './components/HistoryPanel'

import { generateIdeas } from './api/ideas'
import type { IdeaModel, IdeaRequest, IdeaResponse } from './types'

export default function App() {
  const queryClient = useQueryClient()
  const [currentResult, setCurrentResult] = useState<IdeaResponse | null>(null)
  const [selectedIdea, setSelectedIdea] = useState<IdeaModel | null>(null)

  const mutation = useMutation({
    mutationFn: (req: IdeaRequest) => generateIdeas(req),
    onSuccess: (data) => {
      setCurrentResult(data)
      setSelectedIdea(null)
      queryClient.invalidateQueries({ queryKey: ['idea-history'] })
      toast.success(`Generated ${data.ideas.length} ideas!`)
    },
    onError: () => {
      toast.error('Failed to generate ideas. Check your API key and backend.')
    },
  })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl font-black text-gray-900 tracking-tight">ProtoX</span>
            <span className="text-sm font-semibold bg-brand-teal text-white px-2 py-0.5 rounded-full">ProtoIdea</span>
          </div>
          <p className="text-xs text-gray-400 hidden sm:block">
            K. J. Somaiya School of Engineering · B.Tech FYP 2025–27
          </p>
        </div>
        {/* Red accent bar */}
        <div className="h-1 bg-brand-red w-full" />
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Left column — Form + History */}
        <div className="lg:col-span-1 space-y-6">
          <IdeaForm
            onSubmit={mutation.mutate}
            loading={mutation.isPending}
          />
          <HistoryPanel
            onLoad={(record) => {
              setCurrentResult(record)
              setSelectedIdea(null)
              toast('Loaded from history', { icon: '📂' })
            }}
          />
        </div>

        {/* Right column — Results */}
        <div className="lg:col-span-2">
          {!currentResult && !mutation.isPending && (
            <div className="h-full flex flex-col items-center justify-center text-center py-24 text-gray-400">
              <div className="text-5xl mb-4">💡</div>
              <p className="text-lg font-semibold text-gray-500">Your ideas will appear here</p>
              <p className="text-sm mt-1">Fill in the form and click Generate Ideas</p>
            </div>
          )}

          {mutation.isPending && (
            <div className="h-full flex flex-col items-center justify-center text-center py-24">
              <svg className="animate-spin h-10 w-10 text-brand-teal mb-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <p className="text-gray-500 font-medium">Generating ideas for you...</p>
              <p className="text-xs text-gray-400 mt-1">This usually takes 5–10 seconds</p>
            </div>
          )}

          {currentResult && !mutation.isPending && (
            <div className="space-y-4">
              {/* Result header */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-800">
                    {currentResult.ideas.length} Ideas for <span className="text-brand-teal">{currentResult.domain}</span>
                  </h2>
                  <p className="text-sm text-gray-400">App type: {currentResult.app_type}</p>
                </div>
                {selectedIdea && (
                  <div className="bg-teal-50 border border-brand-teal rounded-xl px-4 py-2 text-sm text-brand-teal font-semibold">
                    ✓ "{selectedIdea.title}" selected
                  </div>
                )}
              </div>

              {/* Idea cards */}
              <div className="space-y-4">
                {currentResult.ideas.map((idea, i) => (
                  <IdeaCard
                    key={i}
                    idea={idea}
                    index={i}
                    selected={selectedIdea?.title === idea.title}
                    onSelect={setSelectedIdea}
                  />
                ))}
              </div>

              {/* Next step banner */}
              {selectedIdea && (
                <div className="mt-6 bg-brand-teal text-white rounded-xl p-5 flex items-center justify-between">
                  <div>
                    <p className="font-bold text-base">Ready for ProtoCode →</p>
                    <p className="text-sm text-teal-100 mt-0.5">
                      "{selectedIdea.title}" will be passed to the code generation agent.
                    </p>
                  </div>
                  <button
                    disabled
                    className="bg-white text-brand-teal font-semibold px-4 py-2 rounded-lg text-sm opacity-60 cursor-not-allowed"
                    title="ProtoCode coming soon"
                  >
                    Generate Code (soon)
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
