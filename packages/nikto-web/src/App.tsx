import { Routes, Route, NavLink } from 'react-router-dom'
import { Terminal, Cpu, Shield, Wallet, Activity, Settings } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Agents from './pages/Agents'
import Security from './pages/Security'
import Crypto from './pages/Crypto'
import TerminalPage from './pages/Terminal'

const nav = [
  { to: '/', icon: Activity, label: 'Dashboard' },
  { to: '/agents', icon: Cpu, label: 'Agents' },
  { to: '/security', icon: Shield, label: 'Security' },
  { to: '/crypto', icon: Wallet, label: 'Crypto' },
  { to: '/terminal', icon: Terminal, label: 'Terminal' },
]

export default function App() {
  return (
    <div className="flex h-screen bg-gray-950">
      <nav className="w-16 bg-gray-900 border-r border-gray-800 flex flex-col items-center py-4 gap-2">
        <div className="text-cyan-400 font-bold text-lg mb-4">N</div>
        {nav.map(n => (
          <NavLink
            key={n.to}
            to={n.to}
            className={({ isActive }) =>
              `p-2 rounded-lg transition-colors ${isActive ? 'bg-cyan-600/20 text-cyan-400' : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800'}`
            }
            title={n.label}
          >
            <n.icon size={20} />
          </NavLink>
        ))}
        <div className="mt-auto">
          <Settings size={20} className="text-gray-500 cursor-pointer hover:text-gray-300" />
        </div>
      </nav>
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/security" element={<Security />} />
          <Route path="/crypto" element={<Crypto />} />
          <Route path="/terminal" element={<TerminalPage />} />
        </Routes>
      </main>
    </div>
  )
}
