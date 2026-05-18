export default function Agents() {
  const agents = [
    { name: 'coder-agent', role: 'Lead Developer', status: 'idle', skills: ['python', 'typescript', 'react'], completed: 42 },
    { name: 'security-agent', role: 'Pentester', status: 'scanning', skills: ['nmap', 'sqlmap', 'metasploit'], completed: 18 },
    { name: 'crypto-agent', role: 'Wallet Ops', status: 'syncing', skills: ['bitcoin', 'defi', 'trading'], completed: 7 },
    { name: 'miner-agent', role: 'Miner', status: 'stopped', skills: ['randomx', 'ethash'], completed: 0 },
  ]

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">Agent Team</h1>
      <div className="space-y-3">
        {agents.map((a, i) => (
          <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full ${a.status === 'idle' ? 'bg-green-500' : a.status === 'scanning' || a.status === 'syncing' ? 'bg-yellow-500' : 'bg-red-500'}`} />
              <div>
                <div className="text-white font-medium">{a.name}</div>
                <div className="text-gray-400 text-xs">{a.role}</div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-gray-400 text-xs">{a.skills.slice(0, 3).join(', ')}</div>
              <div className="text-gray-400 text-xs">✓ {a.completed}</div>
              <button className="bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1 rounded text-xs">Logs</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
