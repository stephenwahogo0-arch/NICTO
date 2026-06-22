import { configManager } from '../config/models'

export interface ChatResponse {
  response: string
  conversation_id?: string
}

export interface StatusInfo {
  status: string
  version?: string
  brain_active?: boolean
  uptime?: string
  model?: string
}

export class NiktoAPI {
  private activeModelId: string

  constructor() {
    this.activeModelId = configManager.getActiveModel().id
  }

  private get model() {
    return configManager.getActiveModel()
  }

  refreshModel() {
    this.activeModelId = configManager.getActiveModel().id
  }

  getModelId() { return this.model.id }
  getModelName() { return this.model.name }
  getBaseUrl() { return this.model.endpoint }
  getApiKey() { return this.model.apiKey }
  getModelVersion() { return this.model.version }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    }
    if (this.model.apiKey) headers['X-API-Key'] = this.model.apiKey
    headers['X-Model-Id'] = this.model.id

    const res = await fetch(`${this.model.endpoint}${path}`, { ...options, headers })
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      throw new Error(`API ${res.status}: ${text || res.statusText}`)
    }
    return res.json()
  }

  async chat(message: string, conversationId?: string): Promise<ChatResponse> {
    return this.request('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, conversation_id: conversationId, model_id: this.model.id }),
    })
  }

  async *chatStream(message: string, conversationId?: string): AsyncGenerator<string> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (this.model.apiKey) headers['X-API-Key'] = this.model.apiKey
    headers['X-Model-Id'] = this.model.id

    const res = await fetch(`${this.model.endpoint}/chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message, conversation_id: conversationId, model_id: this.model.id }),
    })

    if (!res.ok) {
      const text = await res.text().catch(() => '')
      throw new Error(`API ${res.status}: ${text || res.statusText}`)
    }

    const reader = res.body?.getReader()
    if (!reader) {
      const data = await res.json() as ChatResponse
      yield data.response
      return
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          if (data === '[DONE]') return
          try {
            const parsed = JSON.parse(data)
            yield parsed.choices?.[0]?.delta?.content || parsed.response || data
          } catch {
            yield data
          }
        }
      }
    }
  }

  async getStatus(): Promise<StatusInfo> {
    return this.request('/health')
  }

  async getConversations(): Promise<{ id: string; title: string; updated_at: string }[]> {
    return this.request('/conversations')
  }

  async deleteConversation(id: string): Promise<void> {
    return this.request(`/conversations/${id}`, { method: 'DELETE' })
  }

  async getPerformanceMetrics(): Promise<Record<string, number>> {
    try { return await this.request('/metrics') } catch { return {} }
  }

  async getTrainingHistory(): Promise<{ entries: { epoch: number; loss: number; accuracy: number }[] }> {
    try { return await this.request('/training/history') } catch { return { entries: [] } }
  }

  async submitFeedback(message: string, correction: string): Promise<{ success: boolean }> {
    try {
      return await this.request('/feedback', {
        method: 'POST',
        body: JSON.stringify({ message, correction, model_id: this.model.id }),
      })
    } catch { return { success: false } }
  }

  async testConnection(): Promise<{ connected: boolean; version?: string; error?: string }> {
    try {
      const status = await this.getStatus()
      return { connected: true, version: status.version }
    } catch (e) {
      return { connected: false, error: (e as Error).message }
    }
  }
}

export const api = new NiktoAPI()
