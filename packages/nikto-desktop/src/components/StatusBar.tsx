import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { configManager } from '../config/models'

export default function StatusBar() {
  const [connected, setConnected] = useState(false)
  const [apiVersion, setApiVersion] = useState('')

  const refresh = () => {
    const model = configManager.getActiveModel()
    api.refreshModel()
    api.getStatus().then(s => {
      setConnected(true)
      setApiVersion(s.version || '')
    }).catch(() => setConnected(false))
  }

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 15000)
    return () => clearInterval(interval)
  }, [])

  const activeModel = configManager.getActiveModel()

  return (
    <div className="h-8 bg-nikto-surface/80 backdrop-blur-sm border-b border-nikto-border/50 flex items-center justify-between px-4 text-xs text-nikto-muted">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-nikto-green shadow-[0_0_4px_rgba(34,197,94,0.5)]' : 'bg-red-500'}`} />
          <span>{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
        {apiVersion && <span className="text-nikto-muted/60">v{apiVersion}</span>}
        <span className="text-nikto-muted/30">|</span>
        <span className="text-nikto-green/80 font-medium">{activeModel.name}</span>
        <span className="text-nikto-muted/50">{activeModel.version}</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-nikto-green/60">nikto</span>
      </div>
    </div>
  )
}
