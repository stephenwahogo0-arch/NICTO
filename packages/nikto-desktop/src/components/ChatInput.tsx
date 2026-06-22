import { useState, useRef, useEffect, type KeyboardEvent } from 'react'

interface Props {
  onSend: (message: string) => void
  onStop: () => void
  isLoading: boolean
  disabled?: boolean
}

export default function ChatInput({ onSend, onStop, isLoading, disabled }: Props) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!isLoading && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [isLoading])

  const autoResize = () => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`
    }
  }

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSend(input)
      setInput('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t border-nikto-border/50 bg-nikto-bg/95 backdrop-blur-sm">
      <div className="max-w-4xl mx-auto p-4">
        <div className="flex items-end gap-2 bg-nikto-surface rounded-xl border border-nikto-border focus-within:border-nikto-green/50 focus-within:ring-1 focus-within:ring-nikto-green/30 transition-all duration-200">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => { setInput(e.target.value); autoResize() }}
            onKeyDown={handleKeyDown}
            placeholder="Message Nikto..."
            rows={1}
            disabled={disabled}
            className="flex-1 bg-transparent px-4 py-3 text-sm text-nikto-text placeholder-nikto-muted focus:outline-none resize-none max-h-[200px] scrollbar-thin"
          />
          <div className="flex items-center gap-1 px-2 pb-2">
            {isLoading ? (
              <button
                onClick={onStop}
                className="w-9 h-9 flex items-center justify-center rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
                title="Stop generating"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="6" width="12" height="12" rx="1" />
                </svg>
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="w-9 h-9 flex items-center justify-center rounded-lg bg-nikto-green text-black hover:bg-nikto-green-dim disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200"
                title="Send message"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            )}
          </div>
        </div>
        <p className="text-[11px] text-nikto-muted text-center mt-2">
          Nikto may produce inaccurate information. Verify important facts.
        </p>
      </div>
    </div>
  )
}
