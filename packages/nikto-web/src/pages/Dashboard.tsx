import { useEffect, useState } from 'react'
import { Cpu, Activity, Zap, Brain, TrendingUp, Eye, Briefcase } from 'lucide-react'

const API = '/api'

export default function Dashboard() {
  const [sysInfo, setSysInfo] = useState<any>(null)
  const [brainSt, setBrainSt] = useState<any>(null)
  const [health, setHealth] = useState<string>('checking...')
  const [introspect, setIntrospect] = useState<any>(null)

  const fetchAll = () => {
    fetch(`${API}/health`).then(r => r.json()).then(d => setHealth(d.status)).catch(() => setHealth('offline'))
    fetch(`${API}/system/info`).then(r => r.json()).then(setSysInfo).catch(() => {})
    fetch(`${API}/brain/status`).then(r => r.json()).then(setBrainSt).catch(() => {})
    fetch(`${API}/brain/introspect`).then(r => r.json()).then(setIntrospect).catch(() => {})
  }

  useEffect(() => { fetchAll(); const id = setInterval(fetchAll, 5000); return () => clearInterval(id) }, [])

  const cards = [
    { icon: Cpu, label: 'CPU', value: sysInfo ? `${sysInfo.cpu_percent ?? 0}%` : '---', color: 'text-cyan-400' },
    { icon: Activity, label: 'Memory', value: sysInfo ? `${sysInfo.memory_percent ?? 0}%` : '---', color: 'text-green-400' },
    { icon: Brain, label: 'Brain Cycles', value: brainSt ? `${brainSt.cycle ?? 0}` : '---', color: 'text-purple-400' },
    { icon: Zap, label: 'Thoughts', value: brainSt ? `${brainSt.thoughts ?? 0}` : '---', color: 'text-yellow-400' },
    { icon: Brain, label: 'Memories', value: brainSt ? `${brainSt.memories ?? 0}` : '---', color: 'text-blue-400' },
    { icon: TrendingUp, label: 'Predictions', value: brainSt ? `${brainSt.predictions ?? 0}` : '---', color: 'text-pink-400' },
    { icon: Eye, label: 'Eagle Watching', value: brainSt?.eagle_watching ? 'Active' : 'Idle', color: brainSt?.eagle_watching ? 'text-green-400' : 'text-gray-400' },
    { icon: Briefcase, label: 'Business Models', value: brainSt ? `${brainSt.business_models ?? 0}` : '---', color: 'text-orange-400' },
  ]

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">NIKTO Dashboard</h1>
        <span className={`text-sm px-3 py-1 rounded-full ${health === 'ok' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
          API: {health}
        </span>
      </div>
      <div className="grid grid-cols-4 gap-4 mb-6">
        {cards.map((c, i) => (
          <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center gap-3 mb-2">
              <c.icon size={20} className={c.color} />
              <span className="text-gray-400 text-sm">{c.label}</span>
            </div>
            <div className="text-2xl font-bold text-white">{c.value}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <Brain size={18} className="text-cyan-400" /> Brain Status
          </h2>
          <div className="text-gray-400 text-sm space-y-2">
            <div className="flex justify-between"><span>Name</span><span className="text-white">{brainSt?.name ?? 'NIKTO'}</span></div>
            <div className="flex justify-between"><span>Awake</span><span className={`${brainSt?.awake ? 'text-green-400' : 'text-red-400'}`}>{brainSt?.awake ? 'Yes' : 'No'}</span></div>
            <div className="flex justify-between"><span>Mood</span><span className="text-white">{brainSt?.mood ?? 'neutral'}</span></div>
            <div className="flex justify-between"><span>Facts Known</span><span className="text-white">{brainSt?.facts ?? 0}</span></div>
            <div className="flex justify-between"><span>Goals</span><span className="text-white">{brainSt?.goals ?? 0}</span></div>
            <div className="flex justify-between"><span>Autopilot Pro</span><span className={brainSt?.autopilot_pro_running ? 'text-green-400' : 'text-gray-500'}>{brainSt?.autopilot_pro_running ? 'Running' : 'Stopped'}</span></div>
          </div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <Activity size={18} className="text-purple-400" /> System Info
          </h2>
          <div className="text-gray-400 text-sm space-y-2">
            <div className="flex justify-between"><span>Platform</span><span className="text-white">{sysInfo?.platform ?? '---'}</span></div>
            <div className="flex justify-between"><span>Release</span><span className="text-white">{sysInfo?.platform_release ?? '---'}</span></div>
            <div className="flex justify-between"><span>Hostname</span><span className="text-white">{sysInfo?.hostname ?? '---'}</span></div>
            <div className="flex justify-between"><span>Swarm Agents</span><span className="text-white">{brainSt?.swarm_agents ?? 0}</span></div>
            <div className="flex justify-between"><span>Metrics Tracked</span><span className="text-white">{brainSt?.metrics ?? 0}</span></div>
          </div>
        </div>
      </div>
    </div>
  )
}
