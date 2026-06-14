import { useState, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatView from './components/ChatView'
import ChatInput from './components/ChatInput'
import StatusBar from './components/StatusBar'
import CredentialManager from './components/CredentialManager'
import SelfImprovementDashboard from './components/SelfImprovementDashboard'
import ModelSelector from './components/ModelSelector'
import { useChat } from './hooks/useChat'
import { api } from './utils/api'
import { configManager } from './config/models'

interface Conversation {
  id: string
  title: string
  updated_at: string
}

export default function App() {
  const { messages, streamingContent, isLoading, error, sendMessage, stopGeneration, clearMessages } = useChat()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [dashboardOpen, setDashboardOpen] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string>()
  const [modelKey, setModelKey] = useState(0)

  const handleModelChange = useCallback(() => {
    api.refreshModel()
    setModelKey(k => k + 1)
    clearMessages()
  }, [clearMessages])

  const handleNewChat = useCallback(() => {
    clearMessages()
    setActiveConversationId(undefined)
  }, [clearMessages])

  const handleSelectConversation = useCallback((id: string) => {
    setActiveConversationId(id)
  }, [])

  const handleDeleteConversation = useCallback((id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id))
    if (activeConversationId === id) {
      clearMessages()
      setActiveConversationId(undefined)
    }
  }, [activeConversationId, clearMessages])

  const handleRetry = useCallback(() => {
    if (messages.length >= 2) {
      const lastUserMsg = [...messages].reverse().find(m => m.role === 'user')
      if (lastUserMsg) sendMessage(lastUserMsg.content)
    }
  }, [messages, sendMessage])

  return (
    <div className="h-screen flex flex-col bg-nikto-bg">
      <StatusBar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          open={sidebarOpen}
          onToggle={() => setSidebarOpen(false)}
          onNewChat={handleNewChat}
          conversations={conversations}
          activeId={activeConversationId}
          onSelect={handleSelectConversation}
          onDelete={handleDeleteConversation}
          onOpenSettings={() => setSettingsOpen(true)}
          onOpenDashboard={() => setDashboardOpen(true)}
        />
        <div className="flex-1 flex flex-col min-w-0">
          {!sidebarOpen && (
            <div className="flex items-center justify-between px-4 py-2 border-b border-nikto-border/30">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="btn-ghost p-1.5"
                  title="Open sidebar"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
                  </svg>
                </button>
                <div className="w-48" key={modelKey}>
                  <ModelSelector onModelChange={handleModelChange} />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => setDashboardOpen(true)} className="btn-ghost p-1.5 text-xs" title="Self-Improvement Dashboard">
                  ◈
                </button>
                <button onClick={() => setSettingsOpen(true)} className="btn-ghost p-1.5" title="Credentials">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                  </svg>
                </button>
                <button onClick={handleNewChat} className="btn-ghost p-1.5" title="New chat">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                </button>
              </div>
            </div>
          )}
          <ChatView
            messages={messages}
            streamingContent={streamingContent}
            isLoading={isLoading}
            error={error}
            onRetry={handleRetry}
          />
          <ChatInput
            onSend={sendMessage}
            onStop={stopGeneration}
            isLoading={isLoading}
          />
        </div>
      </div>
      <CredentialManager open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <SelfImprovementDashboard open={dashboardOpen} onClose={() => setDashboardOpen(false)} />
    </div>
  )
}
