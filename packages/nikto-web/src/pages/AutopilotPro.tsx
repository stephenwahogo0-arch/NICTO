import { useEffect, useState } from 'react'
import { Play, Square, Activity, RefreshCw, TrendingUp } from 'lucide-react'

const API = '/api'

export default function AutopilotPro() {
  const [status, setStatus] = useState<any>(null)
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const fetchStatus = () => {
    fetch(`${API}/autopilot/status`).then(r => r.json()).then(setStatus).catch(() => {})
    fetch(`${API}/autopilot/report`).then(r => r.json()).then(setReport).catch(() => {})
    setLoading(false)
  }

  useEffect(() => { fetchStatus(); const id = setInterval(fetchStatus, 5000); return () => clearInterval(id) }, [])

  const start = () => { fetch(`${API}/autopilot/start`, { method: 'POST' }).then(fetchStatus) }
  const stop = () => { fetch(`${API}/autopilot/stop`, { method: 'POST' }).then(fetchStatus) }

  if (loading) return <div className="p-6 text-gray-400">Loading...</div>

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Activity className="text-cyan-400" /> Autopilot Pro
        </h1>
        <div className="flex gap-2">
          <button onClick={start} className="flex items-center gap-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm">
            <Play size={14} /> Start
          </button>
          <button onClick={stop} className="flex items-center gap-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm">
            <Square size={14} /> Stop
          </button>
          <button onClick={fetchStatus} className="p-1.5 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg">
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Status</div>
          <div className={`text-lg font-bold ${status?.running ? 'text-green-400' : 'text-gray-500'}`}>
            {status?.running ? 'Running' : 'Stopped'}
          </div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Cycles</div>
          <div className="text-lg font-bold text-white">{status?.cycles ?? 0}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Value Generated</div>
          <div className="text-lg font-bold text-yellow-400">{status?.value_generated ?? 0} {status?.currency ?? 'KES'}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Success Rate</div>
          <div className="text-lg font-bold text-white">{report ? (report.success_rate * 100).toFixed(0) : 0}%</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <TrendingUp size={18} className="text-cyan-400" /> Task Summary
          </h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-gray-400"><span>Completed</span><span className="text-green-400">{status?.tasks_completed ?? 0}</span></div>
            <div className="flex justify-between text-gray-400"><span>Failed</span><span className="text-red-400">{status?.tasks_failed ?? 0}</span></div>
            <div className="flex justify-between text-gray-400"><span>Opportunities</span><span className="text-yellow-400">{status?.opportunities ?? 0}</span></div>
            <div className="flex justify-between text-gray-400"><span>Decisions Made</span><span className="text-cyan-400">{status?.decisions ?? 0}</span></div>
          </div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <Activity size={18} className="text-purple-400" /> Active Modules
          </h2>
          {report?.modules_running ? (
            <div className="space-y-1">
              {report.modules_running.map((m: string) => (
                <div key={m} className="flex items-center gap-2 text-gray-400 text-sm">
                  <span className="w-2 h-2 rounded-full bg-green-500" /> {m}
                </div>
              ))}
            </div>
          ) : <div className="text-gray-500 text-sm">No modules running</div>}
        </div>
      </div>
    </div>
  )
}
