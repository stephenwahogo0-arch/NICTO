'use client'

import { useEffect, useState } from 'react'

export default function Dashboard() {
  const [status, setStatus] = useState<any>(null)

  useEffect(() => {
    fetch('http://localhost:8000/status')
      .then(r => r.json())
      .then(setStatus)
      .catch(() => setStatus({ error: 'Backend offline' }))
  }, [])

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-nicto-green">NICTO X</h1>
        <p className="text-nicto-muted mt-1">Frontier AI Platform Dashboard</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-nicto-surface rounded-xl p-4 border border-gray-800">
          <p className="text-nicto-muted text-sm">Status</p>
          <p className="text-xl font-semibold mt-1">{status?.running ? 'Running' : status?.error || 'Loading...'}</p>
        </div>
        <div className="bg-nicto-surface rounded-xl p-4 border border-gray-800">
          <p className="text-nicto-muted text-sm">Agents</p>
          <p className="text-xl font-semibold mt-1">{status?.agents?.length || 0} active</p>
        </div>
        <div className="bg-nicto-surface rounded-xl p-4 border border-gray-800">
          <p className="text-nicto-muted text-sm">Version</p>
          <p className="text-xl font-semibold mt-1">{status?.version || '0.1.0'}</p>
        </div>
      </div>

      <div className="bg-nicto-surface rounded-xl border border-gray-800 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Agent Network</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {['Research', 'Coding', 'Planning', 'Evaluation', 'Memory', 'Vision', 'Security'].map(name => (
            <div key={name} className="flex items-center gap-2 bg-gray-900/50 rounded-lg p-3">
              <span className="w-2 h-2 rounded-full bg-nicto-green" />
              <span className="text-sm">{name}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-nicto-surface rounded-xl border border-gray-800 p-6">
        <h2 className="text-lg font-semibold mb-4">System Performance</h2>
        <p className="text-nicto-muted text-sm">Real-time metrics visualization coming soon.</p>
      </div>
    </div>
  )
}
