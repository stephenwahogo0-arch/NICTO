import { useEffect, useState } from 'react'
import { Eye, AlertTriangle, Target, RefreshCw, Search, Play, Square } from 'lucide-react'

const API = '/api'

export default function EagleEye() {
  const [status, setStatus] = useState<any>(null)
  const [analysis, setAnalysis] = useState<any>(null)
  const [target, setTarget] = useState('')
  const [loading, setLoading] = useState(true)

  const fetchStatus = () => {
    fetch(`${API}/eagle/status`).then(r => r.json()).then(setStatus).catch(() => {})
    setLoading(false)
  }

  useEffect(() => { fetchStatus(); const id = setInterval(fetchStatus, 3000); return () => clearInterval(id) }, [])

  const startWatch = () => fetch(`${API}/eagle/open`, { method: 'POST' }).then(fetchStatus)
  const stopWatch = () => fetch(`${API}/eagle/close`, { method: 'POST' }).then(fetchStatus)

  const analyze = () => {
    if (!target) return
    fetch(`${API}/eagle/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target }),
    }).then(r => r.json()).then(setAnalysis)
  }

  if (loading) return <div className="p-6 text-gray-400">Loading...</div>

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Eye className="text-cyan-400" /> Eagle Eye Perception
        </h1>
        <div className="flex gap-2">
          <button onClick={startWatch} className="flex items-center gap-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm">
            <Play size={14} /> Watch
          </button>
          <button onClick={stopWatch} className="flex items-center gap-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm">
            <Square size={14} /> Stop
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Status</div>
          <div className={`text-lg font-bold ${status?.watching ? 'text-green-400' : 'text-gray-500'}`}>
            {status?.watching ? 'Watching' : 'Idle'}
          </div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Observations</div>
          <div className="text-lg font-bold text-white">{status?.observations ?? 0}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Alerts</div>
          <div className="text-lg font-bold text-yellow-400">{status?.alerts ?? 0}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Patterns</div>
          <div className="text-lg font-bold text-purple-400">{status?.patterns ?? 0}</div>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6">
        <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <Search size={18} className="text-cyan-400" /> Target Analysis
        </h2>
        <div className="flex gap-2">
          <input
            type="text"
            value={target}
            onChange={e => setTarget(e.target.value)}
            placeholder="IP, domain, URL, file path, or code..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500"
            onKeyDown={e => e.key === 'Enter' && analyze()}
          />
          <button onClick={analyze} className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm flex items-center gap-1">
            <Target size={14} /> Analyze
          </button>
        </div>
      </div>

      {analysis && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h3 className="text-white font-medium mb-3 flex items-center gap-2">
              <Target size={16} className="text-cyan-400" /> Analysis: {analysis.target}
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between text-gray-400"><span>Target Type</span><span className="text-white">{analysis.surface_findings?.target_type ?? 'N/A'}</span></div>
              <div className="flex justify-between text-gray-400"><span>Alert Level</span>
                <span className={`font-medium ${analysis.alert_level === 'LOW' ? 'text-green-400' : analysis.alert_level === 'HIGH' ? 'text-red-400' : 'text-yellow-400'}`}>
                  {analysis.alert_level}
                </span>
              </div>
              <div className="flex justify-between text-gray-400"><span>Confidence</span><span className="text-white">{(analysis.confidence * 100).toFixed(0)}%</span></div>
              <div className="flex justify-between text-gray-400"><span>Patterns</span><span className="text-white">{analysis.patterns_found?.length ?? 0}</span></div>
              <div className="flex justify-between text-gray-400"><span>Anomalies</span><span className="text-white">{analysis.anomalies_detected?.length ?? 0}</span></div>
            </div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h3 className="text-white font-medium mb-3 flex items-center gap-2">
              <AlertTriangle size={16} className="text-yellow-400" /> Findings
            </h3>
            <div className="text-sm space-y-2">
              <div className="text-gray-400">
                <span className="text-cyan-400">Threats:</span> {analysis.threat_assessment?.threat_level ?? 'low'}
              </div>
              {analysis.opportunities_identified?.length > 0 && (
                <div>
                  <div className="text-green-400 mb-1">Opportunities:</div>
                  {analysis.opportunities_identified.map((o: string, i: number) => (
                    <div key={i} className="text-gray-500 text-xs">• {o}</div>
                  ))}
                </div>
              )}
              {analysis.predictions?.length > 0 && (
                <div>
                  <div className="text-purple-400 mb-1">Predictions:</div>
                  {analysis.predictions.map((p: string, i: number) => (
                    <div key={i} className="text-gray-500 text-xs">• {p}</div>
                  ))}
                </div>
              )}
              {analysis.deep_context && (
                <div className="mt-3">
                  <div className="text-gray-400 text-xs">{analysis.deep_context}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
