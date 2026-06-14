import { useState, useEffect, useCallback } from 'react'
import { configManager } from '../config/models'
import { api } from '../utils/api'

interface TrainingEntry {
  epoch: number
  loss: number
  accuracy: number
}

interface VersionEntry {
  version: string
  date: string
  description: string
}

interface FeedbackEntry {
  id: string
  timestamp: number
  message: string
  correction: string
  applied: boolean
}

const STORAGE_FEEDBACK = 'nikto-feedback-logs'

export default function SelfImprovementDashboard({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [activeTab, setActiveTab] = useState<'overview' | 'training' | 'versions' | 'feedback'>('overview')
  const [trainingData, setTrainingData] = useState<TrainingEntry[]>([])
  const [feedbackLogs, setFeedbackLogs] = useState<FeedbackEntry[]>([])
  const [metrics, setMetrics] = useState<Record<string, number>>({})
  const [versionHistory] = useState<VersionEntry[]>([
    { version: 'v1.0', date: '2026-05-01', description: 'Initial release — core reasoning + memory' },
    { version: 'v1.1', date: '2026-05-15', description: 'Enhanced chain-of-thought + calibration' },
    { version: 'v2.0', date: '2026-06-01', description: 'Hyperbrain — 12 architectural advances, 100B param target' },
  ])

  useEffect(() => {
    setFeedbackLogs(loadFeedbackLogs())
    api.getPerformanceMetrics().then(setMetrics).catch(() => {})
    api.getTrainingHistory().then(r => {
      if (r.entries?.length) setTrainingData(r.entries)
    }).catch(() => {})
  }, [])

  if (!open) return null

  const activeModel = configManager.getActiveModel()
  const modelConfig = configManager.getConfig()

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: '◈' },
    { id: 'training' as const, label: 'Training', icon: '▦' },
    { id: 'versions' as const, label: 'Versions', icon: '⏣' },
    { id: 'feedback' as const, label: 'Feedback', icon: '↻' },
  ]

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center animate-fade-in" onClick={onClose}>
      <div className="bg-nikto-bg border border-nikto-border rounded-2xl w-full max-w-4xl mx-4 max-h-[85vh] shadow-2xl overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-nikto-border/50 shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold">Self-Improvement Dashboard</h2>
            <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 bg-nikto-green/10 border border-nikto-green/20 rounded text-nikto-green">
              {activeModel.name} {activeModel.version}
            </span>
          </div>
          <button onClick={onClose} className="btn-ghost p-1">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="flex border-b border-nikto-border/30 shrink-0">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors ${
                activeTab === t.id
                  ? 'text-nikto-green border-b-2 border-nikto-green bg-nikto-green/5'
                  : 'text-nikto-muted hover:text-nikto-text'
              }`}
            >
              <span className="text-xs">{t.icon}</span>
              {t.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' && <OverviewTab metrics={metrics} modelConfig={modelConfig} feedbackLogs={feedbackLogs} trainingData={trainingData} />}
          {activeTab === 'training' && <TrainingTab data={trainingData} />}
          {activeTab === 'versions' && <VersionsTab history={versionHistory} />}
          {activeTab === 'feedback' && <FeedbackTab logs={feedbackLogs} onUpdate={setFeedbackLogs} />}
        </div>
      </div>
    </div>
  )
}

function OverviewTab({ metrics, modelConfig, feedbackLogs, trainingData }: {
  metrics: Record<string, number>
  modelConfig: ReturnType<typeof configManager.getConfig>
  feedbackLogs: FeedbackEntry[]
  trainingData: TrainingEntry[]
}) {
  const cards = [
    { label: 'Tracking', value: modelConfig.selfImprovement.trackingEnabled ? 'Active' : 'Disabled', color: 'text-nikto-green' },
    { label: 'Feedback Logs', value: String(feedbackLogs.length), color: 'text-blue-400' },
    { label: 'Training Epochs', value: String(trainingData.length), color: 'text-yellow-400' },
    { label: 'Models Active', value: String(Object.keys(modelConfig.models).length), color: 'text-purple-400' },
  ]

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {cards.map(c => (
          <div key={c.label} className="glass-panel rounded-xl p-4 text-center">
            <div className={`text-2xl font-bold ${c.color}`}>{c.value}</div>
            <div className="text-xs text-nikto-muted mt-1">{c.label}</div>
          </div>
        ))}
      </div>

      <div className="glass-panel rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-3">System Metrics</h3>
        {Object.keys(metrics).length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {Object.entries(metrics).map(([key, val]) => (
              <div key={key} className="flex justify-between items-center px-3 py-2 bg-nikto-surface/50 rounded-lg">
                <span className="text-xs text-nikto-muted capitalize">{key.replace(/_/g, ' ')}</span>
                <span className="text-sm font-mono font-medium">{typeof val === 'number' ? val.toFixed(2) : val}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-nikto-muted/60 italic">Connect to a model to see live metrics</p>
        )}
      </div>

      {feedbackLogs.length > 0 && (
        <div className="glass-panel rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-3">Recent Feedback</h3>
          <div className="space-y-2">
            {feedbackLogs.slice(-3).reverse().map(f => (
              <div key={f.id} className="flex items-start gap-3 px-3 py-2 bg-nikto-surface/50 rounded-lg text-xs">
                <span className={`mt-0.5 ${f.applied ? 'text-nikto-green' : 'text-yellow-400'}`}>{f.applied ? '✓' : '○'}</span>
                <div className="flex-1 min-w-0">
                  <p className="truncate text-nikto-muted">{f.message}</p>
                  <p className="truncate text-nikto-text/70 mt-0.5">{f.correction}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function TrainingTab({ data }: { data: TrainingEntry[] }) {
  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-nikto-muted/60">
        <div className="text-3xl mb-3">▦</div>
        <p className="text-sm">No training data available yet</p>
        <p className="text-xs mt-1">Connect to a running model to fetch training history</p>
      </div>
    )
  }

  const maxLoss = Math.max(...data.map(d => d.loss))
  const maxAccuracy = Math.max(...data.map(d => d.accuracy))

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-3">Training Loss</h3>
        <div className="flex items-end gap-1 h-32">
          {data.map((d, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-1">
              <div
                className="w-full bg-nikto-green/60 rounded-t transition-all duration-300 hover:bg-nikto-green"
                style={{ height: `${(d.loss / maxLoss) * 100}%`, minHeight: '4px' }}
                title={`Epoch ${d.epoch}: loss=${d.loss.toFixed(4)}`}
              />
            </div>
          ))}
        </div>
        <div className="flex justify-between text-[10px] text-nikto-muted/60 mt-1">
          <span>Epoch {data[0]?.epoch ?? 0}</span>
          <span>Epoch {data[data.length - 1]?.epoch ?? 0}</span>
        </div>
      </div>

      <div className="glass-panel rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-3">Accuracy</h3>
        <div className="flex items-end gap-1 h-24">
          {data.map((d, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-1">
              <div
                className="w-full bg-blue-400/60 rounded-t transition-all duration-300 hover:bg-blue-400"
                style={{ height: `${(d.accuracy / maxAccuracy) * 100}%`, minHeight: '4px' }}
                title={`Epoch ${d.epoch}: accuracy=${(d.accuracy * 100).toFixed(1)}%`}
              />
            </div>
          ))}
        </div>
        <div className="flex justify-between text-[10px] text-nikto-muted/60 mt-1">
          <span>Epoch {data[0]?.epoch ?? 0}</span>
          <span>Epoch {data[data.length - 1]?.epoch ?? 0}</span>
        </div>
      </div>

      <div className="glass-panel rounded-xl p-5 overflow-x-auto">
        <h3 className="text-sm font-semibold mb-3">Training Log</h3>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-nikto-muted border-b border-nikto-border/30">
              <th className="text-left py-2 pr-4">Epoch</th>
              <th className="text-right py-2 pr-4">Loss</th>
              <th className="text-right py-2">Accuracy</th>
            </tr>
          </thead>
          <tbody>
            {data.map(d => (
              <tr key={d.epoch} className="border-b border-nikto-border/10 hover:bg-nikto-surface/30">
                <td className="py-2 pr-4 font-mono">{d.epoch}</td>
                <td className="py-2 pr-4 text-right font-mono text-nikto-green">{d.loss.toFixed(4)}</td>
                <td className="py-2 text-right font-mono text-blue-400">{(d.accuracy * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function VersionsTab({ history }: { history: VersionEntry[] }) {
  return (
    <div className="glass-panel rounded-xl p-5">
      <h3 className="text-sm font-semibold mb-4">Version History</h3>
      <div className="relative">
        <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-nikto-border/30" />
        <div className="space-y-6">
          {history.map((v, i) => (
            <div key={i} className="relative flex gap-4">
              <div className="w-6 flex items-start justify-center">
                <div className={`w-3 h-3 rounded-full border-2 mt-1 ${
                  i === 0 ? 'bg-nikto-green border-nikto-green' : 'bg-nikto-surface border-nikto-border'
                }`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm">{v.version}</span>
                  <span className="text-[10px] text-nikto-muted/60">{v.date}</span>
                  {i === 0 && <span className="text-[10px] px-1.5 py-0.5 bg-nikto-green/10 border border-nikto-green/20 rounded text-nikto-green">Latest</span>}
                </div>
                <p className="text-xs text-nikto-muted mt-0.5">{v.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function FeedbackTab({ logs, onUpdate }: { logs: FeedbackEntry[]; onUpdate: (l: FeedbackEntry[]) => void }) {
  const [newMessage, setNewMessage] = useState('')
  const [newCorrection, setNewCorrection] = useState('')

  const addFeedback = () => {
    if (!newMessage.trim() || !newCorrection.trim()) return
    const entry: FeedbackEntry = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      timestamp: Date.now(),
      message: newMessage.trim(),
      correction: newCorrection.trim(),
      applied: false,
    }
    const updated = [entry, ...logs]
    onUpdate(updated)
    saveFeedbackLogs(updated)
    setNewMessage('')
    setNewCorrection('')

    api.submitFeedback(entry.message, entry.correction).then(r => {
      if (r.success) {
        const marked = updated.map(e => e.id === entry.id ? { ...e, applied: true } : e)
        onUpdate(marked)
        saveFeedbackLogs(marked)
      }
    })
  }

  return (
    <div className="space-y-5">
      <div className="glass-panel rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-3">Submit Correction</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-nikto-muted mb-1">Model Response to Correct</label>
            <textarea
              value={newMessage}
              onChange={e => setNewMessage(e.target.value)}
              className="input-area text-xs resize-none"
              rows={2}
              placeholder="Paste the model's response that needs correction..."
            />
          </div>
          <div>
            <label className="block text-xs text-nikto-muted mb-1">Corrected Response</label>
            <textarea
              value={newCorrection}
              onChange={e => setNewCorrection(e.target.value)}
              className="input-area text-xs resize-none"
              rows={2}
              placeholder="Provide the correct response for retraining..."
            />
          </div>
          <button onClick={addFeedback} className="btn-primary text-xs">
            Submit Feedback
          </button>
        </div>
      </div>

      {logs.length > 0 && (
        <div className="glass-panel rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-3">Correction Log ({logs.length})</h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {logs.map(f => (
              <div key={f.id} className="flex items-start gap-3 px-3 py-2.5 bg-nikto-surface/50 rounded-lg border border-nikto-border/20">
                <span className={`text-lg mt-0.5 ${f.applied ? 'text-nikto-green' : 'text-yellow-400'}`}>
                  {f.applied ? '✓' : '○'}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${f.applied ? 'bg-nikto-green/10 text-nikto-green' : 'bg-yellow-400/10 text-yellow-400'}`}>
                      {f.applied ? 'Applied' : 'Pending'}
                    </span>
                    <span className="text-[10px] text-nikto-muted/50">{new Date(f.timestamp).toLocaleString()}</span>
                  </div>
                  <p className="text-xs text-nikto-muted mb-0.5"><span className="text-nikto-text/60">Original:</span> {f.message.slice(0, 120)}{f.message.length > 120 ? '...' : ''}</p>
                  <p className="text-xs text-nikto-green/80"><span className="text-nikto-text/60">Corrected:</span> {f.correction.slice(0, 120)}{f.correction.length > 120 ? '...' : ''}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function loadFeedbackLogs(): FeedbackEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_FEEDBACK)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

function saveFeedbackLogs(logs: FeedbackEntry[]) {
  try { localStorage.setItem(STORAGE_FEEDBACK, JSON.stringify(logs)) } catch {}
}
