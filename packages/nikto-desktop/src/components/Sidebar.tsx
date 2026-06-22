import NiktoLogo from './NiktoLogo'
import ModelSelector from './ModelSelector'

interface Conversation {
  id: string
  title: string
  updated_at: string
}

interface Props {
  open: boolean
  onToggle: () => void
  onNewChat: () => void
  conversations: Conversation[]
  activeId?: string
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onOpenSettings: () => void
  onOpenDashboard: () => void
}

export default function Sidebar({ open, onToggle, onNewChat, conversations, activeId, onSelect, onDelete, onOpenSettings, onOpenDashboard }: Props) {
  if (!open) return null

  return (
    <div className="w-64 bg-nikto-sidebar border-r border-nikto-border flex flex-col h-full animate-slide-in">
      <div className="p-3 border-b border-nikto-border/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <NiktoLogo size={24} animated />
          <span className="font-semibold text-sm">Nikto</span>
        </div>
        <button onClick={onToggle} className="btn-ghost p-1.5" title="Close sidebar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <ModelSelector onModelChange={() => {}} />

      <div className="p-2">
        <button onClick={onNewChat} className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-dashed border-nikto-border hover:border-nikto-green/50 hover:bg-nikto-green/5 text-nikto-muted hover:text-nikto-green transition-all duration-200">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin px-2 space-y-0.5">
        {conversations.map(conv => (
          <div
            key={conv.id}
            className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm transition-colors duration-150 ${
              conv.id === activeId ? 'bg-nikto-green/10 text-nikto-green' : 'text-nikto-muted hover:bg-white/5 hover:text-nikto-text'
            }`}
            onClick={() => onSelect(conv.id)}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="flex-shrink-0">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <span className="truncate flex-1">{conv.title}</span>
            <button
              onClick={e => { e.stopPropagation(); onDelete(conv.id) }}
              className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-red-400 transition-all"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
          </div>
        ))}
        {conversations.length === 0 && (
          <p className="text-xs text-nikto-muted text-center py-8">No conversations yet</p>
        )}
      </div>

      <div className="p-2 border-t border-nikto-border/50 space-y-0.5">
        <button onClick={onOpenDashboard} className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg text-nikto-muted hover:text-nikto-text hover:bg-white/5 transition-colors duration-150">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <rect x="3" y="3" width="7" height="9" rx="1" /><rect x="14" y="3" width="7" height="5" rx="1" /><rect x="14" y="12" width="7" height="9" rx="1" /><rect x="3" y="16" width="7" height="5" rx="1" />
          </svg>
          Self-Improvement
        </button>
        <button onClick={onOpenSettings} className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg text-nikto-muted hover:text-nikto-text hover:bg-white/5 transition-colors duration-150">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          Credentials
        </button>
      </div>
    </div>
  )
}
