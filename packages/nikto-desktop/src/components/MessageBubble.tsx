import { marked } from 'marked'
import NiktoLogo from './NiktoLogo'
import type { Message } from '../hooks/useChat'

interface Props {
  message: Message
  streaming?: boolean
}

export default function MessageBubble({ message, streaming }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex items-start gap-3 px-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-nikto-green/20 flex items-center justify-center flex-shrink-0 ring-1 ring-nikto-green/30">
          <NiktoLogo size={18} animated />
        </div>
      )}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 ring-1 ring-blue-500/30">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </div>
      )}
      <div className={`max-w-[80%] ${isUser ? 'message-user ml-auto' : 'message-ai mr-auto'}`}>
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div
            className={`prose prose-invert prose-sm max-w-none prose-code:bg-white/10 prose-code:px-1 prose-code:rounded prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-700 ${streaming ? 'after:content-["▊"] after:animate-pulse after:text-nikto-green after:ml-0.5' : ''}`}
            dangerouslySetInnerHTML={{ __html: marked.parse(message.content, { breaks: true }) as string }}
          />
        )}
      </div>
    </div>
  )
}
