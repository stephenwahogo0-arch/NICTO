# Agent System

Multi-agent orchestration system for autonomous task execution.

## Architecture

```
┌─────────────────────────────────────────────┐
│              AgentBus (Message Bus)          │
├──────────┬──────────┬──────────┬────────────┤
│ Research │  Coding  │ Planning │ Evaluation │
├──────────┼──────────┼──────────┼────────────┤
│  Memory  │  Vision  │ Security │    API     │
└──────────┴──────────┴──────────┴────────────┘
```

## Agents

| Agent | Responsibility | Implementation |
|-------|---------------|----------------|
| **Research** | Web search, literature review, fact checking | `packages/nicto-x/src/nicto_x/agents/research_agent.py` |
| **Coding** | Multi-language code generation, test creation | `packages/nicto-x/src/nicto_x/agents/coding_agent.py` |
| **Planning** | Task decomposition, dependency tracking | `packages/nicto-x/src/nicto_x/agents/planning_agent.py` |
| **Evaluation** | Response grading, rubric-based scoring | `packages/nicto-x/src/nicto_x/agents/evaluation_agent.py` |
| **Memory** | Retrieval, consolidation, working memory | `packages/nicto-x/src/nicto_x/agents/memory_agent.py` |
| **Vision** | Image analysis, OCR, edge detection | `packages/nicto-x/src/nicto_x/agents/vision_agent.py` |
| **Security** | SQLi/XSS detection, port scanning, CVE lookup | `packages/nicto-x/src/nicto_x/agents/security_agent.py` |
