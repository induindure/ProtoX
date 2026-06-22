import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import IdeaForm from './components/IdeaForm'
import IdeaCard from './components/IdeaCard'
import HistoryPanel from './components/HistoryPanel'
import IdeaRefinement from './components/IdeaRefinement'

import { generateIdeas, refineIdea } from './api/ideas'
import type { RankedIdea, IdeaRequest, IdeaResponse, IdeaModel } from './types'

export default function App() {
  const queryClient = useQueryClient()
  const [currentResult, setCurrentResult] = useState<IdeaResponse | null>(null)
  const [selectedIdea, setSelectedIdea] = useState<RankedIdea | null>(null)
  const [refiningIdea, setRefiningIdea] = useState<IdeaModel | null>(null)
  const [refinementLoading, setRefinementLoading] = useState(false)

  const mutation = useMutation({
    mutationFn: (req: IdeaRequest) => generateIdeas(req),
    onSuccess: (data) => {
      setCurrentResult(data)
      setSelectedIdea(null)
      setRefiningIdea(null)
      queryClient.invalidateQueries({ queryKey: ['idea-history'] })
      toast.success(`Generated ${data.ideas.length} ideas!`)
    },
    onError: () => {
      toast.error('Failed to generate ideas. Check your API key and backend.')
    },
  })

  const handleRefineIdea = async (feedback: string): Promise<IdeaModel> => {
    if (!refiningIdea) throw new Error('No idea to refine')
    
    setRefinementLoading(true)
    try {
      const refined = await refineIdea({
        title: refiningIdea.title,
        current_description: refiningIdea.description,
        current_features: refiningIdea.features,
        current_tech_hints: refiningIdea.tech_hints,
        current_target_users: refiningIdea.target_users,
        feedback,
      })
      
      setRefiningIdea(refined.idea || refined)
      toast.success('Idea refined! ✓')
      return refined.idea || refined
    } catch (error) {
      toast.error('Failed to refine idea. Try again!')
      throw error
    } finally {
      setRefinementLoading(false)
    }
  }

  const handleFinalizeIdea = () => {
    if (refiningIdea) {
      const finalIdea = refiningIdea

      setSelectedIdea({
        idea: finalIdea,
        scores: selectedIdea?.scores || { total: 0, feasibility: 0, novelty: 0, market_fit: 0 }
      })
      setRefiningIdea(null)
      toast.success('Idea finalized! Opening ProtoCode...')

      // Encode idea as URL param and open protocode
      const encoded = encodeURIComponent(JSON.stringify({
        title: finalIdea.title,
        description: finalIdea.description,
        features: finalIdea.features,
        tech_hints: finalIdea.tech_hints,
        target_users: finalIdea.target_users,
      }))
      window.open(`http://localhost:5174?idea=${encoded}`, '_blank')
    }
  }

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
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-800">
                    {currentResult.ideas.length} Ideas for{' '}
                    <span className="text-brand-teal">{currentResult.domain}</span>
                  </h2>
                  <p className="text-sm text-gray-400">App type: {currentResult.app_type}</p>
                </div>
                {selectedIdea && !refiningIdea && (
                  <div className="bg-teal-50 border border-brand-teal rounded-xl px-4 py-2 text-sm text-brand-teal font-semibold">
                    ✓ "{selectedIdea.idea.title}" selected
                  </div>
                )}
              </div>

              {refiningIdea ? (
                <IdeaRefinement
                  idea={refiningIdea}
                  onRefine={handleRefineIdea}
                  onFinalize={handleFinalizeIdea}
                  loading={refinementLoading}
                />
              ) : (
                <>
                  <div className="space-y-4">
                    {currentResult.ideas.map((ranked, i) => (
                      <IdeaCard
                        key={i}
                        idea={ranked.idea}
                        scores={ranked.scores}
                        index={i}
                        selected={selectedIdea?.idea.title === ranked.idea.title}
                        onSelect={() => {
                          setSelectedIdea(ranked)
                          setRefiningIdea(ranked.idea)
                        }}
                      />
                    ))}
                  </div>

                  {selectedIdea && (
                    <div className="mt-6 bg-brand-teal text-white rounded-xl p-5 flex items-center justify-between">
                      <div>
                        <p className="font-bold text-base">Ready for ProtoCode</p>
                        <p className="text-sm text-teal-100 mt-0.5">
                          Select this idea and refine it to send it to ProtoCode.
                        </p>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}