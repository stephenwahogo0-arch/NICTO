import { useState } from 'react'
import { configManager, type ModelConfig } from '../config/models'
import { api } from '../utils/api'

interface Props {
  onModelChange: () => void
}

const modelTiers: Record<string, { label: string; color: string }> = {
  nicto_kyros: { label: '⚡ Fast', color: 'text-blue-400' },
  nicto_omega: { label: '⚖️ Balanced', color: 'text-yellow-400' },
  nicto_main: { label: '🔧 Full', color: 'text-purple-400' },
  nicto_x: { label: '🚀 Frontier', color: 'text-nikto-green' },
}

export default function ModelSelector({ onModelChange }: Props) {
  const [models] = useState<ModelConfig[]>(() => configManager.getAllModels())
  const [active, setActive] = useState(() => configManager.getActiveModel())

  const handleSwitch = (id: string) => {
    configManager.setActiveModel(id)
    const model = configManager.getActiveModel()
    setActive(model)
    api.refreshModel()
    onModelChange()
  }

  return (
    <div className="px-3 py-2 border-b border-nikto-border/30">
      <label className="block text-[10px] uppercase tracking-widest text-nikto-muted/50 mb-1.5 font-medium">
        Active Model
      </label>
      <div className="flex flex-col gap-1.5">
        {models.map((m) => {
          const isActive = m.id === active.id
          const tier = modelTiers[m.id] || { label: '', color: 'text-nikto-muted' }
          return (
            <button
              key={m.id}
              onClick={() => handleSwitch(m.id)}
              className={`text-left px-3 py-2 rounded-lg text-xs transition-all duration-200 border ${
                isActive
                  ? 'bg-nikto-green/10 border-nikto-green/40 text-nikto-green shadow-[0_0_8px_rgba(34,197,94,0.15)]'
                  : 'bg-nikto-surface/50 border-transparent text-nikto-muted hover:text-nikto-text hover:bg-nikto-surface'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm">{m.name}</span>
                <span className={`text-[10px] font-medium ${tier.color}`}>{tier.label}</span>
              </div>
              <div className="text-[10px] opacity-60 mt-0.5 mb-1">{m.version}</div>
              <div className="flex flex-wrap gap-1">
                {m.capabilities.slice(0, 5).map((cap, i) => (
                  <span key={i} className="px-1.5 py-0.5 bg-nikto-green/10 border border-nikto-green/20 rounded-sm text-[9px] text-nikto-green/80">
                    {cap}
                  </span>
                ))}
                {m.capabilities.length > 5 && (
                  <span className="px-1.5 py-0.5 text-[9px] text-nikto-muted">
                    +{m.capabilities.length - 5}
                  </span>
                )}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
