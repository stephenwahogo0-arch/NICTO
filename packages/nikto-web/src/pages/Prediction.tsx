import { useEffect, useState } from 'react'
import { TrendingUp, BarChart3, Target, CheckCircle, RefreshCw } from 'lucide-react'

const API = '/api'

export default function Prediction() {
  const [status, setStatus] = useState<any>(null)
  const [prediction, setPrediction] = useState<any>(null)
  const [accuracy, setAccuracy] = useState<any>(null)
  const [question, setQuestion] = useState('')
  const [timeframe, setTimeframe] = useState('30_day')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/predict/status`).then(r => r.json()).then(setStatus).catch(() => setLoading(false))
    fetch(`${API}/predict/accuracy`).then(r => r.json()).then(setAccuracy).catch(() => {})
    setLoading(false)
  }, [])

  const makePrediction = () => {
    if (!question) return
    fetch(`${API}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, timeframe }),
    }).then(r => r.json()).then(setPrediction)
  }

  if (loading) return <div className="p-6 text-gray-400">Loading...</div>

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <TrendingUp className="text-cyan-400" /> Future Prediction Engine
        </h1>
        <button onClick={() => { fetch(`${API}/predict/status`).then(r => r.json()).then(setStatus); fetch(`${API}/predict/accuracy`).then(r => r.json()).then(setAccuracy) }}
          className="p-1.5 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg">
          <RefreshCw size={16} />
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Predictions Made</div>
          <div className="text-lg font-bold text-white">{status?.prediction_count ?? 0}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Average Accuracy</div>
          <div className="text-lg font-bold text-green-400">
            {accuracy ? `${(accuracy.average_accuracy * 100).toFixed(1)}%` : 'N/A'}
          </div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Methods</div>
          <div className="text-lg font-bold text-purple-400">8</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Domains</div>
          <div className="text-lg font-bold text-yellow-400">10</div>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6">
        <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <BarChart3 size={18} className="text-cyan-400" /> Make a Prediction
        </h2>
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="What do you want to predict? e.g. Will AI surpass human intelligence by 2030?"
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500"
            onKeyDown={e => e.key === 'Enter' && makePrediction()}
          />
          <select value={timeframe} onChange={e => setTimeframe(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm">
            <option value="7_day">7 days</option>
            <option value="30_day">30 days</option>
            <option value="90_day">90 days</option>
            <option value="1_year">1 year</option>
          </select>
          <button onClick={makePrediction} className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm flex items-center gap-1">
            <Target size={14} /> Predict
          </button>
        </div>
      </div>

      {prediction && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h3 className="text-white font-medium mb-3 flex items-center gap-2">
              <CheckCircle size={16} className="text-green-400" /> Prediction Result
            </h3>
            <div className="space-y-2 text-sm">
              <div className="text-gray-400">Question: <span className="text-white">{prediction.question}</span></div>
              <div className="text-gray-400">Most Likely: <span className="text-green-400 font-medium">{prediction.most_likely_outcome}</span></div>
              <div className="flex gap-4">
                <div className="text-gray-400">Probability: <span className="text-yellow-400">{(prediction.probability * 100).toFixed(1)}%</span></div>
                <div className="text-gray-400">Confidence: <span className="text-cyan-400">{(prediction.confidence * 100).toFixed(1)}%</span></div>
              </div>
              <div className="text-gray-400">Timeframe: <span className="text-white">{prediction.timeframe}</span></div>
              <div className="text-gray-400">Domain: <span className="text-white">{prediction.domain}</span></div>
              <div className="text-gray-400">Methodology: <span className="text-purple-400">{prediction.methodology?.join(', ')}</span></div>
            </div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h3 className="text-white font-medium mb-3">Alternative Scenarios</h3>
            {prediction.alternative_scenarios?.length > 0 ? (
              <div className="space-y-2">
                {prediction.alternative_scenarios.map((s: any, i: number) => (
                  <div key={i} className="bg-gray-800 rounded-lg p-3">
                    <div className="text-cyan-400 text-sm font-medium">{s.name}</div>
                    <div className="text-gray-400 text-xs mt-1">{s.outcome}</div>
                    <div className="text-yellow-400 text-xs mt-1">Probability: {(s.probability * 100).toFixed(0)}%</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-gray-500 text-sm">No alternative scenarios generated.</div>
            )}
            {prediction.signals_to_watch?.length > 0 && (
              <div className="mt-3">
                <div className="text-purple-400 text-xs mb-1">Signals to Watch:</div>
                {prediction.signals_to_watch.map((sig: string, i: number) => (
                  <div key={i} className="text-gray-500 text-xs">• {sig}</div>
                ))}
              </div>
            )}
            <div className="mt-4 text-gray-600 text-xs">ID: {prediction.id} — save this for later verification</div>
          </div>
        </div>
      )}

      {accuracy && accuracy.total_predictions_verified > 0 && (
        <div className="mt-6 bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h3 className="text-white font-medium mb-2 flex items-center gap-2">
            <BarChart3 size={16} className="text-cyan-400" /> Accuracy History
          </h3>
          <div className="text-sm text-gray-400">
            Total verified: {accuracy.total_predictions_verified} | Average: {(accuracy.average_accuracy * 100).toFixed(1)}%
          </div>
        </div>
      )}
    </div>
  )
}
