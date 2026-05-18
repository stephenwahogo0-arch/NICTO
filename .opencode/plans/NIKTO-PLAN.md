# Project Nikto — The Ultimate AI Agent Platform

## Vision

**Nikto** is a unified, multimodal, multi-agent orchestration platform that combines the best features from 18+ open-source AI agent systems into a single super-agent. It functions simultaneously as:

- A **CLI coding agent** (like Claude Code, opencode, Kimi Code CLI)
- A **GUI automation agent** (like UI-TARS Desktop)
- An **agent orchestration company** (like Paperclip)
- A **persistent memory system** (like claude-mem)
- A **multi-model proxy and gateway** (like OpenClaw)
- A **desktop application** with web dashboard
- A **cloud-hosted enterprise platform**

---

## Architecture Overview

**Project Nikto** combines all features from the 18 source repositories into a unified system with these layers:

1. **User Interfaces** - Rich CLI/TUI, Web UI (React), Desktop App (Electron), VS Code Extension, Telegram Bridge, Zsh Plugin
2. **Orchestration Layer** (Paperclip-inspired) - Board/CEO Agent, Org Chart, Governance, Budget/Cost Control, Multi-Company
3. **Agent Runtime Core** - Agent Loop, Tool System (30+ tools), Skill Runtime (SKILL.md), Memory (claude-mem), Multi-Model Provider
4. **Capability Modules** - Coding Agent, GUI/Vision Agent, Web/Search Agent, Communication Agent
5. **Integration Layer** - MCP Ecosystem, Plugin System, Sandbox (Docker/K8s), Model Proxy, Multi-Engine Sessions
6. **Data Layer** - PostgreSQL, SQLite FTS5, ChromaDB, Redis, Object Store

## Complete Feature Inventory

The plan documents 100+ features organized into 11 categories, mapped to their source repos and assigned priorities (P0-P2).

### Category 1: Coding Agent (20 features)
Agent loop with streaming, Rich REPL, File ops, Bash exec, Multi-model (Anthropic/OpenAI/Gemini/DeepSeek/Kimi/200+), Plan/Build modes, Subagent delegation, Shell mode, Git ops, ACP/IDE integration, VS Code Ext, LSP, Session persistence, YOLO mode, Approval requests.

### Category 2: Multimodal GUI Agent (11 features)
Screen capture, Computer use (click/type via vision), Browser automation (GUI Agent + DOM hybrid), Remote computer/browser operator, Vision coding (UI to code), Chrome automation, Cross-platform desktop app.

### Category 3: Web Search and Research (11 features)
WebSearch with ranked results, Perplexity_ask/research/reason, Search recency/domain filtering, Context size control, Reasoning effort control, WebFetch, Multiple search backends.

### Category 4: Agent Orchestration (14 features)
Org Chart, Goal alignment, Ticket system, Heartbeat execution, Budget/cost control, Governance/approvals, Multi-company isolation, Routines/schedules, Activity audit log, Secrets storage, Workspaces, Company portability, Plugin system, Identity/access.

### Category 5: Skill System (12 features)
SKILL.md slash commands, 23 production skills (spec/plan/build/test/review/ship), 1000+ skill directory, Connect-apps (500+ apps), Flow skills, Skill Manager UI.

### Category 6: Memory and Context (10 features)
Persistent cross-session memory, 6 lifecycle hooks, Hybrid search (SQLite FTS5 + ChromaDB), 3-layer retrieval, Progressive disclosure, 10x token savings, 256K context, Interleaved thinking.

### Category 7: Multi-Agent (11 features)
Agent Swarm, Multi-agent flow, Council with voting, Parallel scaling (1000s), Data analysis agent, RL-based improvement, Async delegation, Multi-engine sessions, Autoloop, Ultraplan, Ultrareview.

### Category 8: Sandbox and Security (7 features)
Docker sandbox, K8s scaling, File system isolation, Browser in sandbox, Permission system, Secrets injection.

### Category 9: Communication (8 features)
Telegram bridge, MCP ecosystem, OpenAI-compatible proxy, Email, Slack/Discord, GitHub/GitLab, Jira/Linear, Notion/Confluence.

### Category 10: Deployment (7 features)
CLI (pip/npm/homebrew/scoop/choco), Desktop app, Web UI, Cloud/K8s, Docker, Embedded dashboard, Mobile-ready.

### Category 11: Advanced Model (7 features)
1T MoE model, Native multimodality, Thinking/Instant modes, INT4 quantization, vLLM/SGLang/KTransformers, Video input.

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Core Runtime | Python 3.12+ | Agent loop, tools, skills, memory |
| CLI/TUI | Rich + Textual | Terminal interface with streaming |
| Desktop | Electron + React + TypeScript | Native desktop application |
| Web UI | React + TypeScript + Tailwind | Dashboard and management |
| Orchestration API | FastAPI (Python) + Node.js (TypeScript) | API server |
| Database | PostgreSQL + SQLite | Data persistence |
| Vector Store | ChromaDB | Semantic search |
| Cache | Redis | Sessions, rate limiting |
| LLM Integration | litellm | 200+ model providers |
| MCP | TypeScript + Python MCP SDKs | Tool ecosystem |
| Sandbox | Docker + Kubernetes | Secure execution |
| Browser Automation | Playwright | Browser control |
| Computer Use | PyAutoGUI + mss | Screen/mouse/keyboard |
| Build | pnpm + uv/poetry | Monorepo management |

## Implementation Phases (24 weeks total)

### Phase 1: Core Agent Runtime (Weeks 1-3)
Monorepo setup, Agent loop, Core tools (file ops, bash), Multi-model via litellm, Rich REPL, Plan/Build modes, Git ops, Session persistence

### Phase 2: Memory and Skills (Weeks 4-5)
claude-mem inspired memory (SQLite FTS5 + ChromaDB), 6 lifecycle hooks, SKILL.md runtime, 23 production skills, 7 slash commands, Flow skills

### Phase 3: Web Search and MCP (Weeks 6-7)
Perplexity MCP tools, WebFetch/WebSearch, MCP server host, Search filtering, Research depth control

### Phase 4: Orchestration Platform (Weeks 8-11)
PostgreSQL backend, Org Chart, Ticket system, Heartbeat engine, Budget control, Governance, Schedules, Audit log, Multi-company

### Phase 5: Web UI and Desktop (Weeks 12-14)
React web dashboard, Electron desktop app, Real-time event streaming, Cost visualization, Mobile-responsive

### Phase 6: Multimodal GUI Agent (Weeks 15-17)
Screen capture, Computer use, Browser automation, Remote operator, Vision coding, Chrome DevTools

### Phase 7: Advanced Multi-Agent (Weeks 18-20)
Agent Swarm, Council voting, Autoloop, Ultraplan, Ultrareview, Async delegation, Multi-engine sessions

### Phase 8: Cloud and Sandbox (Weeks 21-24)
Docker sandbox, K8s deployment, Telegram bridge, Voice mode, Plugin marketplace, Poor Mode, RL improvement, All integrations

## Project Structure

`
nikto/
├── packages/
│   ├── nikto-core/           # Python: agent runtime, tools, loop
│   ├── nikto-cli/            # Python: CLI/TUI interface
│   ├── nikto-orchestrator/   # Python: Paperclip-style orchestration
│   ├── nikto-desktop/        # TypeScript: Electron desktop app
│   ├── nikto-web/            # TypeScript: Web dashboard (React)
│   ├── nikto-vision/         # Python: GUI Agent, computer use
│   ├── nikto-mcp/            # TypeScript: MCP server host
│   ├── nikto-plugins/        # Python: Plugin system
│   └── nikto-skills/         # SKILL.md files
├── docs/
├── docker/
├── k8s/
├── scripts/
├── package.json
├── pyproject.toml
└── pnpm-workspace.yaml
`

## Source Repos Mapped

All features sourced from:
1. bytedance/UI-TARS-desktop - Multimodal GUI, browser agent, Event Stream, Desktop app
2. paperclipai/paperclip - Agent orchestration, org chart, budgets, governance, multi-company
3. perplexityai/modelcontextprotocol - Web search, research, reasoning MCP tools
4. GPT-AGI/Clawd-Code - Python agent runtime, 30+ tools, SKILL.md system, REPL
5. MoonshotAI/Kimi-K2.5 - 1T MoE model, vision coding, agent swarm, 256K context
6. MoonshotAI/kimi-cli - CLI agent, shell mode, VS Code, ACP, plugins, subagents
7. OpenHands/OpenHands - Docker sandbox, SWE-Bench, parallel agents, MCP
8. addyosmani/agent-skills - 23 production skills, 7 slash commands
9. ComposioHQ/awesome-claude-skills - 1000+ skills, connect-apps, SaaS integrations
10. claude-code-best/claude-code - Open-source Claude Code, voice, Chrome, Poor Mode
11. thedotmack/claude-mem - Persistent memory, hybrid search, lifecycle hooks
12. anthropics/claude-code - Official Claude Code, git workflows, plugins
13. FoundationAgents/OpenManus - Multi-agent flow, data analysis, RL
14. 51AutoPilot/openclaw-claude-proxy - Telegram bridge, multi-engine, councils
15. jamesmurdza/awesome-ai-devtools - Tool directory reference
16. google-labs-code/jules-awesome-list - Task prompt templates
17. gemini-cli-extensions/jules - Async task delegation
18. anomalyco/opencode - Plan/Build modes, skill system, MCP, TUI

## Next Steps

1. Set up monorepo with Python (uv) + TypeScript (pnpm) workspaces
2. Implement core agent loop with streaming
3. Build basic tool system (file ops + bash)
4. Integrate litellm for multi-model support
5. Create Rich TUI with REPL
6. Implement Plan/Build modes
7. Begin memory system with SQLite FTS5
