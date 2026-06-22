import { useState } from 'react'
import { configManager, type ModelConfig } from '../config/models'
import { api } from '../utils/api'

interface Props {
  open: boolean
  onClose: () => void
}

export default function CredentialManager({ open, onClose }: Props) {
  const [models] = useState<ModelConfig[]>(() => configManager.getAllModels())
  const [edits, setEdits] = useState<Record<string, ModelConfig>>(() => {
    const map: Record<string, ModelConfig> = {}
    for (const m of configManager.getAllModels()) {
      map[m.id] = { ...m }
    }
    return map
  })
  const [activeTab, setActiveTab] = useState(models[0]?.id || 'nicto_omega')
  const [saved, setSaved] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<Record<string, { connected: boolean; version?: string; error?: string }>>({})

  if (!open) return null

  const current = edits[activeTab]
  if (!current) return null

  const updateField = (field: keyof ModelConfig, value: string) => {
    setEdits(prev => ({
      ...prev,
      [activeTab]: { ...prev[activeTab], [field]: value },
    }))
  }

  const handleSave = () => {
    for (const m of Object.values(edits)) {
      configManager.updateModel(m.id, m)
    }
    api.refreshModel()
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const testConnectionFor = async (modelId: string) => {
    const originalEndpoint = configManager.getModel(modelId)?.endpoint
    const originalKey = configManager.getModel(modelId)?.apiKey
    const edit = edits[modelId]

    configManager.updateModel(modelId, { endpoint: edit.endpoint, apiKey: edit.apiKey })
    api.refreshModel()

    try {
      const status = await api.getStatus()
      setConnectionStatus(prev => ({
        ...prev,
        [modelId]: { connected: true, version: status.version },
      }))
    } catch (e) {
      setConnectionStatus(prev => ({
        ...prev,
        [modelId]: { connected: false, error: (e as Error).message },
      }))
    } finally {
      if (originalEndpoint && originalKey !== undefined) {
        configManager.updateModel(modelId, { endpoint: originalEndpoint, apiKey: originalKey || '' })
      }
      api.refreshModel()
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center animate-fade-in" onClick={onClose}>
      <div className="bg-nikto-bg border border-nikto-border rounded-2xl w-full max-w-2xl mx-4 shadow-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-nikto-border/50">
          <h2 className="text-lg font-semibold">Credential Manager</h2>
          <button onClick={onClose} className="btn-ghost p-1">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="flex border-b border-nikto-border/30">
          {models.map((m) => (
            <button
              key={m.id}
              onClick={() => setActiveTab(m.id)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === m.id
                  ? 'text-nikto-green border-b-2 border-nikto-green bg-nikto-green/5'
                  : 'text-nikto-muted hover:text-nikto-text'
              }`}
            >
              {m.name}
            </button>
          ))}
        </div>

        <div className="p-6 space-y-5 max-h-[60vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-nikto-muted mb-1.5">API Endpoint</label>
              <input
                type="text"
                value={current.endpoint}
                onChange={e => updateField('endpoint', e.target.value)}
                className="input-area text-sm font-mono"
                placeholder="http://127.0.0.1:5000"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-nikto-muted mb-1.5">Version</label>
              <input
                type="text"
                value={current.version}
                onChange={e => updateField('version', e.target.value)}
                className="input-area text-sm"
                placeholder="v1.0"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-nikto-muted mb-1.5">API Key</label>
            <div className="flex gap-2">
              <input
                type="password"
                value={current.apiKey}
                onChange={e => updateField('apiKey', e.target.value)}
                className="input-area text-sm font-mono flex-1"
                placeholder="Enter your NICTO API key..."
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-nikto-muted mb-1.5">Description</label>
            <textarea
              value={current.description}
              onChange={e => updateField('description', e.target.value)}
              className="input-area text-sm resize-none"
              rows={2}
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-nikto-muted mb-1.5">Capabilities</label>
            <div className="flex flex-wrap gap-1.5">
              {current.capabilities.map((cap, i) => (
                <span key={i} className="px-2 py-0.5 bg-nikto-green/10 border border-nikto-green/20 rounded-md text-[11px] text-nikto-green">
                  {cap}
                </span>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4 pt-2">
            <button onClick={handleSave} className="btn-primary text-sm px-6">
              {saved ? 'Saved!' : 'Save Credentials'}
            </button>
            <button
              onClick={() => testConnectionFor(activeTab)}
              className="px-4 py-2 text-xs border border-nikto-border rounded-lg text-nikto-muted hover:text-nikto-text hover:border-nikto-green/50 transition-colors"
            >
              Test Connection
            </button>
            {connectionStatus[activeTab] && (
              <div className={`text-xs ${connectionStatus[activeTab].connected ? 'text-nikto-green' : 'text-red-400'}`}>
                {connectionStatus[activeTab].connected
                  ? `Connected (${connectionStatus[activeTab].version || 'unknown version'})`
                  : `Failed: ${connectionStatus[activeTab].error || 'unknown error'}`}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
