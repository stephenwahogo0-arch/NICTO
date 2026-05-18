import { useEffect, useState } from 'react'
import { Cpu, Shield, Wallet, Activity, Zap, Users } from 'lucide-react'

const API = 'http://127.0.0.1:4890'

export default function Dashboard() {
  const [sysInfo, setSysInfo] = useState<any>(null)
  const [health, setHealth] = useState<string>('checking...')

  useEffect(() => {
    fetch(`${API}/health`).then(r => r.json()).then(d => setHealth(d.status)).catch(() => setHealth('offline'))
    fetch(`${API}/system/info`).then(r => r.json()).then(setSysInfo).catch(() => {})
  }, [])

  const cards = [
    { icon: Cpu, label: 'CPU', value: sysInfo ? `${sysInfo.cpu_percent}%` : '---', color: 'text-cyan-400' },
    { icon: Activity, label: 'Memory', value: sysInfo ? `${sysInfo.memory_percent}%` : '---', color: 'text-green-400' },
    { icon: Cpu, label: 'Agents', value: '4 running', color: 'text-purple-400' },
    { icon: Wallet, label: 'Crypto', value: '0.000 BTC', color: 'text-yellow-400' },
  ]

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Nikto Dashboard</h1>
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
            <Zap size={18} className="text-cyan-400" /> Recent Activity
          </h2>
          <div className="text-gray-400 text-sm space-y-2">
            <p>Security scan completed (22 ports)</p>
            <p>Wallet synced — 0.000 BTC</p>
            <p>Orchestrator started</p>
          </div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <Users size={18} className="text-purple-400" /> Agent Team
          </h2>
          <div className="text-gray-400 text-sm space-y-2">
            <p>🟢 coder-agent — idle</p>
            <p>🟢 security-agent — scanning target</p>
            <p>🟡 crypto-agent — wallet sync</p>
            <p>🔴 miner-agent — stopped</p>
          </div>
        </div>
      </div>
    </div>
  )
}
