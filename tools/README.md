# Tool System

Extensible plugin architecture for NICTO's tool ecosystem.

## Plugin Architecture

Tools follow a common interface pattern:

```python
class BaseTool:
    name: str
    description: str
    
    async def execute(self, params: dict) -> dict:
        """Execute the tool with given parameters."""
        pass
```

## Available Tools

| Tool | Category | Description |
|------|----------|-------------|
| **Knowledge Graph** | Retrieval | BFS graph traversal, concept neighbors |
| **Vector Store** | Search | N-gram embedding search, batch query |
| **Security Scanner** | Analysis | Port scan, CVE lookup, SQLi/XSS detection |
| **Code Generator** | Development | Multi-language code gen, test gen, Dockerfile gen |
| **Search** | Retrieval | DuckDuckGo + Wikipedia integration |
| **File Manager** | System | Read/write/delete files, directory operations |
| **Calculator** | Math | Expression evaluation, formula solving |

## Implementations

- `packages/nicto-x/src/nicto_x/knowledge/` — KnowledgeGraph, VectorStore
- `packages/nicto-x/src/nicto_x/software/` — SoftwareEngineer (code gen)
- `packages/nicto-x/src/nicto_x/agents/research_agent.py` — Search
- `packages/nikto-core/src/nikto/security/` — Scanner, exploit DB
