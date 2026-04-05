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
      toast.success('Record deleted')
    },
    onError: () => toast.error('Failed to delete'),
  })

  if (isLoading) return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <p className="text-sm text-gray-400 animate-pulse">Loading history...</p>
    </div>
  )

  const records = data?.records ?? []

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h2 className="text-lg font-bold text-gray-800 mb-4">Past Generations</h2>

      {records.length === 0 ? (
        <p className="text-sm text-gray-400">No history yet. Generate your first ideas above!</p>
      ) : (
        <ul className="space-y-3 max-h-96 overflow-y-auto pr-1">
          {records.map(record => (
            <li
              key={record.record_id}
              className="border border-gray-200 rounded-xl p-3 hover:border-teal-300 transition-all"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-gray-800 truncate">
                    {record.domain} — {record.app_type}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">{record.ideas.length} ideas · ID: {record.record_id.slice(0, 8)}…</p>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button
                    onClick={() => onLoad(record)}
                    className="text-xs px-3 py-1 rounded-lg border border-brand-teal text-brand-teal hover:bg-teal-50 transition"
                  >
                    Load
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(record.record_id)}
                    className="text-xs px-3 py-1 rounded-lg border border-red-300 text-red-500 hover:bg-red-50 transition"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
