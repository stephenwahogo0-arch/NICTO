# Memory System

Hierarchical memory architecture supporting short-term, long-term, and knowledge retrieval.

## Architecture

```
┌──────────────────────────────────────────────────┐
│              NICTO Memory System                  │
├───────────────┬────────────────┬─────────────────┤
│ Working Memory│ Episodic Memory│  Semantic Memory │
│ (short-term)  │ (experiences)  │  (knowledge)     │
├───────────────┴────────────────┴─────────────────┤
│              Memory Consolidation                 │
├──────────────────────────────────────────────────┤
│           Knowledge Graph / Vector Store          │
└──────────────────────────────────────────────────┘
```

## Memory Types

| Type | Duration | Capacity | Purpose |
|------|----------|----------|---------|
| **Working** | Session | ~10 slots | Active context, immediate reasoning |
| **Episodic** | Persistent | Unlimited | Experiences, conversations, events |
| **Semantic** | Persistent | Unlimited | Facts, concepts, relationships |

## Implementations

- **NICTO X**: `packages/nicto-x/src/nicto_x/memory/` — EpisodicMemory, SemanticMemory, WorkingMemory, MemoryConsolidator
- **NiktoBrain**: `packages/nikto-core/src/nikto/brain/memory.py` — NiktoLongTermMemory with tag-indexed storage, importance scoring, decay, consolidation
- **Cross-Session**: `nicto_neural/memory/cross_session.py` — SQLite-backed persistent memory across restarts
- **Context Compression**: `nicto_neural/memory/context_compressor.py` — Importance-based compression for 1M-token context
