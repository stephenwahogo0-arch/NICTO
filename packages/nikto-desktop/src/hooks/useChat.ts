import { useState, useCallback, useRef } from 'react'
import { api, type ChatResponse } from '../utils/api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [streamingContent, setStreamingContent] = useState('')
  const conversationIdRef = useRef<string | undefined>(undefined)
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return

    setError(null)
    const userMsg: Message = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      role: 'user',
      content: content.trim(),
      timestamp: Date.now(),
    }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)
    setStreamingContent('')

    const controller = new AbortController()
    abortRef.current = controller

    try {
      let fullResponse = ''
      const stream = api.chatStream(content, conversationIdRef.current)
      for await (const chunk of stream) {
        if (controller.signal.aborted) break
        fullResponse += chunk
        setStreamingContent(fullResponse)
      }

      if (!controller.signal.aborted) {
        const aiMsg: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: fullResponse,
          timestamp: Date.now(),
        }
        setMessages(prev => [...prev, aiMsg])
        setStreamingContent('')
      }
    } catch (err) {
      if ((err as Error).name === 'AbortError') return
      try {
        const res = await api.chat(content, conversationIdRef.current)
        const aiMsg: Message = {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
          role: 'assistant',
          content: res.response,
          timestamp: Date.now(),
        }
        setMessages(prev => [...prev, aiMsg])
        if (res.conversation_id) conversationIdRef.current = res.conversation_id
      } catch (fallbackErr) {
        setError(fallbackErr instanceof Error ? fallbackErr.message : 'Request failed')
      }
    } finally {
      setIsLoading(false)
      setStreamingContent('')
      abortRef.current = null
    }
  }, [isLoading])

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
    setStreamingContent('')
    setError(null)
    conversationIdRef.current = undefined
  }, [])

  return {
    messages,
    streamingContent,
    isLoading,
    error,
    sendMessage,
    stopGeneration,
    clearMessages,
  }
}
