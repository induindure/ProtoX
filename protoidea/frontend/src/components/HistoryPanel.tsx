import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getHistory, deleteIdea } from '../api/ideas'
import toast from 'react-hot-toast'
import type { IdeaResponse } from '../types'

interface Props {
  onLoad: (record: IdeaResponse) => void
}

export default function HistoryPanel({ onLoad }: Props) {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['idea-history'],
    queryFn: getHistory,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteIdea,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['idea-history'] })
      toast.success('Removed from history')
    },
    onError: () => toast.error('Failed to delete'),
  })

  const records = data?.records ?? []

  return (
    <section style={{ padding: '14px 14px 10px', borderTop: '1px solid var(--border)', background: 'var(--surface2)' }}>
      <div className="px-between" style={{ marginBottom: 6, padding: '0 6px' }}>
        <h2 className="px-section-label">History</h2>
        <span className="px-small" style={{ color: 'var(--faint)' }}>Private to you</span>
      </div>

      {isLoading ? (
        <div className="px-stack" style={{ gap: 8, paddingBottom: 8 }}>
          <div className="px-skeleton" style={{ height: 44 }} />
          <div className="px-skeleton" style={{ height: 44 }} />
        </div>
      ) : records.length === 0 ? (
        <p className="px-small px-muted" style={{ margin: '4px 6px 10px' }}>No history yet. Your generated ideas will be saved here.</p>
      ) : (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0, maxHeight: 240, overflowY: 'auto' }}>
          {records.map((record) => (
            <li key={record.record_id} style={{ display: 'flex', alignItems: 'center', gap: 4, borderRadius: 10 }}>
              <button
                type="button"
                onClick={() => onLoad(record)}
                className="px-btn px-btn-ghost"
                style={{ flex: 1, minWidth: 0, minHeight: 44, justifyContent: 'flex-start', textAlign: 'left', padding: '8px 10px' }}
              >
                <span style={{ minWidth: 0 }}>
                  <span style={{ display: 'block', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {record.domain} · {record.app_type}
                  </span>
                  <span className="px-small px-muted" style={{ fontWeight: 400 }}>{record.ideas.length} ideas</span>
                </span>
              </button>
              <button
                type="button"
                onClick={() => deleteMutation.mutate(record.record_id)}
                className="px-btn px-btn-ghost px-btn-danger"
                style={{ minWidth: 40, padding: 0 }}
                aria-label={`Delete ${record.domain} ${record.app_type} from history`}
                title="Delete"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />
                </svg>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
