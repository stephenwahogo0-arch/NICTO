import { useEffect, useState } from 'react'
import { Briefcase, TrendingUp, Users, Clock, RefreshCw } from 'lucide-react'

const API = '/api'

export default function Business() {
  const [models, setModels] = useState<any[]>([])
  const [plan, setPlan] = useState<any>(null)
  const [selectedModel, setSelectedModel] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/business/models`).then(r => r.json()).then(d => { setModels(d.models); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const generatePlan = () => {
    const modelName = selectedModel || models[0]?.name
    fetch(`${API}/business/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_name: modelName, skills: ['python', 'security'] }),
    }).then(r => r.json()).then(setPlan)
  }

  if (loading) return <div className="p-6 text-gray-400">Loading...</div>

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Briefcase className="text-cyan-400" /> Zero-Capital Business Engine
        </h1>
        <button onClick={() => fetch(`${API}/business/models`).then(r => r.json()).then(d => setModels(d.models))}
          className="p-1.5 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg">
          <RefreshCw size={16} />
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Models Available</div>
          <div className="text-lg font-bold text-white">{models.length}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Capital Required</div>
          <div className="text-lg font-bold text-green-400">KES 0</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Min Time to Revenue</div>
          <div className="text-lg font-bold text-yellow-400">7 days</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Max Monthly Potential</div>
          <div className="text-lg font-bold text-purple-400">KES 2M+</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <Users size={18} className="text-cyan-400" /> Available Business Models
          </h2>
          <div className="space-y-2">
            {models.map((m: any) => (
              <div key={m.name}
                className={`p-3 rounded-lg cursor-pointer border ${selectedModel === m.name ? 'border-cyan-500 bg-cyan-900/20' : 'border-gray-800 hover:border-gray-700'}`}
                onClick={() => setSelectedModel(m.name)}>
                <div className="text-white text-sm font-medium">{m.name}</div>
                <div className="text-gray-500 text-xs mt-1">
                  Capital: KES {m.capital} | Time: {m.time_to_revenue} | Potential: {m.monthly_potential}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <TrendingUp size={18} className="text-green-400" /> Generate Business Plan
          </h2>
          {selectedModel && (
            <button onClick={generatePlan}
              className="w-full mb-4 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm">
              Generate Plan for Selected Model
            </button>
          )}
          {plan ? (
            <div className="text-sm space-y-2">
              <div className="text-green-400 font-medium">{plan.model_name}</div>
              <div className="text-gray-400">Capital: KES {plan.capital_required}</div>
              <div className="text-gray-400">Time to Revenue: {plan.time_to_first_revenue}</div>
              <div className="text-gray-400">Monthly Potential: {plan.monthly_potential}</div>
              {plan.first_week_actions?.length > 0 && (
                <div className="mt-3">
                  <div className="text-cyan-400 text-xs mb-1">First Week Actions:</div>
                  {plan.first_week_actions.slice(0, 4).map((a: string, i: number) => (
                    <div key={i} className="text-gray-500 text-xs">• {a}</div>
                  ))}
                </div>
              )}
              {plan.projections && (
                <div className="mt-3">
                  <div className="text-yellow-400 text-xs mb-1">Projections:</div>
                  {Object.entries(plan.projections).slice(0, 4).map(([k, v]: any) => (
                    <div key={k} className="text-gray-500 text-xs">{k}: KES {v.profit_kes} profit</div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="text-gray-500 text-sm">Select a model and click generate to create a customized business plan.</div>
          )}
        </div>
      </div>
    </div>
  )
}
