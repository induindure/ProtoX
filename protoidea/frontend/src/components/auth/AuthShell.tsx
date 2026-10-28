import type { ReactNode } from 'react'

export default function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center gap-3">
          <span className="text-2xl font-black text-gray-900 tracking-tight">ProtoX</span>
          <span className="text-sm font-semibold bg-brand-teal text-white px-2 py-0.5 rounded-full">ProtoIdea</span>
        </div>
        <div className="h-1 bg-brand-red w-full" />
      </header>

      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md bg-white rounded-2xl shadow-md p-8">{children}</div>
      </main>
    </div>
  )
}