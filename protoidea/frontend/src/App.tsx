import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import Header, { Hero, CheckIcon, LogoMark } from './protox/Header'
import { MODULE_URLS, withTheme } from './protox/theme'
import IdeaForm from './components/IdeaForm'
import IdeaCard from './components/IdeaCard'
import HistoryPanel from './components/HistoryPanel'
import IdeaRefinement from './components/IdeaRefinement'
import UserMenu from './components/auth/UserMenu'

import { generateIdeas, refineIdea } from './api/ideas'
import type { RankedIdea, IdeaRequest, IdeaResponse, IdeaModel } from './types'

function EmptyState() {
  return (
    <div className="px-empty">
      <div style={{ marginBottom: 16 }}><LogoMark size={56} /></div>
      <h2>Your ideas will appear here</h2>
      <p>Pick a domain and an app type, then generate. You’ll get 3–5 ranked ideas you can refine and send to ProtoCode.</p>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="px-stack" aria-live="polite">
      <div className="px-row" style={{ color: 'var(--accent-text)', fontWeight: 600 }}>
        <span className="px-spinner" /> Generating ideas… this usually takes 5–10 seconds.
      </div>
      {[0, 1, 2].map((i) => (
        <div key={i} className="px-card px-stack">
          <div className="px-skeleton" style={{ height: 18, width: '35%' }} />
          <div className="px-skeleton" style={{ height: 12, width: '85%' }} />
          <div className="px-skeleton" style={{ height: 12, width: '65%' }} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 16 }}>
            <div className="px-skeleton" style={{ height: 6 }} />
            <div className="px-skeleton" style={{ height: 6 }} />
            <div className="px-skeleton" style={{ height: 6 }} />
          </div>
        </div>
      ))}
    </div>
  )
}

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
      toast.success(`Generated ${data.ideas.length} ideas`)
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
      toast.success('Idea refined')
      return refined.idea || refined
    } catch (error) {
      toast.error('Failed to refine idea. Try again.')
      throw error
    } finally {
      setRefinementLoading(false)
    }
  }

  const handleFinalizeIdea = () => {
    if (!refiningIdea) return
    const finalIdea = refiningIdea

    setSelectedIdea({
      idea: finalIdea,
      scores: selectedIdea?.scores || { total: 0, feasibility: 0, novelty: 0, market_fit: 0 },
    })
    setRefiningIdea(null)
    toast.success('Idea finalized. Opening ProtoCode…')

    // Encode idea as URL param and open protocode (in the same theme)
    const encoded = encodeURIComponent(JSON.stringify({
      title: finalIdea.title,
      description: finalIdea.description,
      features: finalIdea.features,
      tech_hints: finalIdea.tech_hints,
      target_users: finalIdea.target_users,
    }))
    window.open(withTheme(`${MODULE_URLS.code}?idea=${encoded}`), '_blank')
  }

  return (
    <div className="px-page">
      <Header current={1}>
        <UserMenu />
      </Header>

      <Hero step={1} title="What should we build today?">
        Describe the space and ProtoX suggests ranked, buildable app ideas you can refine and turn into code.
      </Hero>

      <main className="px-container grid items-start gap-6 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)]">
        <aside className="px-stack-lg">
          <IdeaForm onSubmit={mutation.mutate} loading={mutation.isPending} />
          <HistoryPanel
            onLoad={(record) => {
              setCurrentResult(record)
              setSelectedIdea(null)
              setRefiningIdea(null)
              toast.success('Loaded from history')
            }}
          />
        </aside>

        <section className="min-w-0">
          {!currentResult && !mutation.isPending && <EmptyState />}

          {mutation.isPending && <LoadingState />}

          {currentResult && !mutation.isPending && (
            <div className="px-stack">
              <div className="px-between" style={{ alignItems: 'flex-end' }}>
                <div>
                  <h2 className="px-title" style={{ fontSize: 24 }}>
                    {currentResult.ideas.length} ideas for <span className="px-gradient-text">{currentResult.domain}</span>
                  </h2>
                  <p className="px-subtitle">{currentResult.app_type} · ranked by overall score · pick one to refine</p>
                </div>

                {refiningIdea ? (
                  <button type="button" onClick={() => setRefiningIdea(null)} className="px-btn">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M15 18l-6-6 6-6" />
                    </svg>
                    Back to ideas
                  </button>
                ) : (
                  selectedIdea && (
                    <span className="px-badge px-badge-ok">
                      <CheckIcon /> {selectedIdea.idea.title} selected
                    </span>
                  )
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
                <div className="px-stack">
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
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
