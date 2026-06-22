export interface ModelConfig {
  id: string
  name: string
  endpoint: string
  apiKey: string
  version: string
  description: string
  capabilities: string[]
}

export interface AppConfig {
  activeModelId: string
  models: Record<string, ModelConfig>
  selfImprovement: {
    trackingEnabled: boolean
    logPath: string
    feedbackEnabled: boolean
  }
}

const STORAGE_KEY = 'nikto-app-config'
const DEFAULT_PATH = '~/.nikto/improvement_logs/'

const defaultModels: Record<string, ModelConfig> = {
  nicto_kyros: {
    id: 'nicto_kyros',
    name: 'Kyros',
    endpoint: 'http://127.0.0.1:5000',
    apiKey: '',
    version: 'v0.1',
    description: 'Lightning-fast minimal brain — identity, basic memory, direct response. No reasoning, emotion, or agents.',
    capabilities: ['Chat', 'Memory', 'Identity'],
  },
  nicto_omega: {
    id: 'nicto_omega',
    name: 'Omega',
    endpoint: 'http://127.0.0.1:5000',
    apiKey: '',
    version: 'v0.2',
    description: 'Core reasoning engine — deep chain-of-thought, memory consolidation, ethical deliberation.',
    capabilities: ['Reasoning', 'Memory', 'Learning', 'Emotional Core', 'Conscience', 'Metacognition', 'Dream Steerer', 'Truth Engine'],
  },
  nicto_main: {
    id: 'nicto_main',
    name: 'Main',
    endpoint: 'http://127.0.0.1:5000',
    apiKey: '',
    version: 'v0.3',
    description: 'Full-featured brain — Omega + security scanning, enhanced reasoning, autopilot suggestions.',
    capabilities: ['Reasoning', 'Memory', 'Learning', 'Emotional Core', 'Conscience', 'Security Scanning', 'Metacognition', 'Dream Steerer', 'Truth Engine', 'Autopilot', 'Performance Graph'],
  },
  nicto_x: {
    id: 'nicto_x',
    name: 'X',
    endpoint: 'http://127.0.0.1:5000',
    apiKey: '',
    version: 'v1.0',
    description: 'Frontier agent system — multi-agent orchestration, planning, coding, research, distributed execution.',
    capabilities: ['Research', 'Coding', 'Planning', 'Evaluation', 'Memory Agent', 'Vision Agent', 'Security Agent', 'Agent Swarming', 'Distributed Execution', 'Self-Improvement', 'Science Research'],
  },
}

function defaultConfig(): AppConfig {
  return {
    activeModelId: 'nicto_omega',
    models: defaultModels,
    selfImprovement: {
      trackingEnabled: true,
      logPath: DEFAULT_PATH,
      feedbackEnabled: true,
    },
  }
}

export class ConfigManager {
  private config: AppConfig

  constructor() {
    this.config = this.load()
  }

  private load(): AppConfig {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw) as AppConfig
        const merged = defaultConfig()
        Object.assign(merged.models, parsed.models)
        merged.activeModelId = parsed.activeModelId || 'nicto_omega'
        merged.selfImprovement = { ...merged.selfImprovement, ...parsed.selfImprovement }
        return merged
      }
    } catch { /* fall through */ }
    return defaultConfig()
  }

  save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.config))
      this.tryWriteConfigFile()
    } catch { /* storage full or unavailable */ }
  }

  private async tryWriteConfigFile() {
    try {
      const content = JSON.stringify(this.config, null, 2)
      const win = typeof window !== 'undefined' ? (window as unknown as Record<string, unknown>) : null
      if (win?.__TAURI__) {
        try {
          // @ts-expect-error — optional Tauri plugin, handled at runtime
          const fs = await import('@tauri-apps/plugin-fs')
          await fs.writeTextFile('nikto-config.json', content, { baseDir: (fs as any).BaseDirectory.AppConfig })
        } catch { /* tauri plugin not available at runtime */ }
      }
    } catch { /* tauri fs unavailable */ }
  }

  getActiveModel(): ModelConfig {
    return this.config.models[this.config.activeModelId] || this.config.models.nicto_omega
  }

  setActiveModel(id: string) {
    if (this.config.models[id]) {
      this.config.activeModelId = id
      this.save()
    }
  }

  getModel(id: string): ModelConfig | undefined {
    return this.config.models[id]
  }

  updateModel(id: string, updates: Partial<ModelConfig>) {
    if (this.config.models[id]) {
      Object.assign(this.config.models[id], updates)
      this.save()
    }
  }

  getAllModels(): ModelConfig[] {
    return Object.values(this.config.models)
  }

  getConfig(): AppConfig {
    return this.config
  }

  updateSelfImprovement(updates: Partial<AppConfig['selfImprovement']>) {
    Object.assign(this.config.selfImprovement, updates)
    this.save()
  }
}

export const configManager = new ConfigManager()
