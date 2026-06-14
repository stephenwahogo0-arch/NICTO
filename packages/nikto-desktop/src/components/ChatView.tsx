import { useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'
import NiktoLogo from './NiktoLogo'
import type { Message } from '../hooks/useChat'

interface Props {
  messages: Message[]
  streamingContent: string
  isLoading: boolean
  error: string | null
  onRetry?: () => void
}

export default function ChatView({ messages, streamingContent, isLoading, error, onRetry }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent, isLoading])

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-md px-8">
          <div className="mb-6 flex justify-center">
            <NiktoLogo size={64} animated />
          </div>
          <h1 className="text-2xl font-semibold text-nikto-text mb-2">Nikto</h1>
          <p className="text-nikto-muted text-sm mb-8">
            Autonomous AI with real reasoning, memory, and learning capabilities.
          </p>
          <div className="grid grid-cols-2 gap-3 text-left">
            {[
              { title: 'Reasoning', desc: 'Multi-style chain-of-thought' },
              { title: 'Memory', desc: 'Long-term persistent storage' },
              { title: 'Learning', desc: 'Self-improvement from feedback' },
              { title: 'Security', desc: 'Pentesting & threat intel' },
            ].map(s => (
              <div key={s.title} className="bg-nikto-surface/50 rounded-xl p-3 border border-nikto-border/30">
                <p className="text-xs font-medium text-nikto-green mb-0.5">{s.title}</p>
                <p className="text-xs text-nikto-muted">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin py-6 space-y-4">
      {messages.map(msg => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {streamingContent && (
        <MessageBubble
          message={{ id: 'streaming', role: 'assistant', content: streamingContent, timestamp: Date.now() }}
          streaming
        />
      )}
      {isLoading && !streamingContent && <TypingIndicator />}
      {error && (
        <div className="flex flex-col items-center gap-2 px-4 py-3 mx-4 bg-red-500/10 border border-red-500/20 rounded-xl text-center">
          <p className="text-sm text-red-400">{error}</p>
          {onRetry && (
            <button onClick={onRetry} className="text-xs text-nikto-green hover:underline">
              Try again
            </button>
          )}
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
