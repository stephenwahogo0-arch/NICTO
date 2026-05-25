# NICTO Neural Core V1 — HYPERBRAIN EVOLUTION ENGINE

A production-grade neural intelligence layer that transforms NICTO from a modular AI framework into a persistent, memory-driven, self-improving intelligence platform.

## Architecture

```
Input → Tokenizer → Embedding → Transformer → MoE Router → BrainHeads
  → BrainRouter (ELO-weighted) → 6 Specialist Brains
  → BrainBoost Ensemble → Reflection → Evaluation → Output
```

### The 6 Brains

| Brain | Domain | Role |
|-------|--------|------|
| Primary | General | Task routing, conversation, state control |
| Analytical | Code, Math | Logic, structured reasoning |
| Creative | Design | Generation, brainstorming |
| Strategic | Planning | Goal planning, mission trees |
| Knowledge | RAG | Retrieval-augmented generation |
| Intuitive | Ranking | Confidence estimation, pattern selection |

### Key Systems

- **ELO Rating System** — Dynamic skill scoring per brain per domain, updated after every task
- **BrainBoost** — Gradient-boosted ensemble with fixed (equal weights) and trained (learned weights) modes
- **Memory System** — 12 SQLite+FAISS stores (episodic, semantic, skills, goals, personality, reflection, performance, task features, consistency, experience)
- **PPO RL Agent** — Proximal Policy Optimization for reinforcement learning from experience
- **Curriculum Learning** — Adaptive difficulty progression with plateau detection
- **Reward Shaping** — Multi-component reward with gating and anti-hacking
- **Feature Engineering** — 15-dimensional state vector for task representation
- **Safety** — Permission manager, rollback snapshots, tamper-evident audit logging, reward hacking detection

## Installation

```bash
pip install torch numpy
git clone <repo>
cd nicto-neural
pip install -e .
```

## Quick Start

```python
from nicto_neural import NeuralCore
from nicto_neural.neural.config import NeuralConfig

config = NeuralConfig(d_model=512)
core = NeuralCore(config=config)

# Process a task
result = core.process({"input": "solve x^2 + 2x + 1 = 0", "domain": "math"})

# Train from interaction data
history = core.train(mode="supervised")

# Reflect on a result
reflection = core.reflect(task, result)
```

## Training Guide

### Step 1 — Prepare Data
- Collect from conversation logs, task history, reflections, corrections
- Clean, deduplicate, normalize features (15-dim state vectors)
- Split 80/20 into training and hold-out validation

### Step 2 — Choose Model
- `model_selector.py` picks the right complexity based on dataset size:
  - < 100 examples → BrainBoost fixed (simple)
  - 100–10,000 → BrainBoost trained
  - 10,000+ → Full transformer + RL

### Step 3 — Train
- Supervised: Cross-entropy on labeled task data
- RL: PPO updates from experience buffer
- Curriculum: Unlocks harder levels on accuracy plateau

## API Reference

- `BrainAPI.think(input, domain)` — Process a task
- `MemoryAPI.store(key, value, store_type)` — Store in memory
- `AgentAPI.run_task(task, mode)` — Run agents in parallel/sequential
- `ReflectionAPI.reflect(task, result)` — Post-task reflection
- `EvolutionAPI.trigger_training(reason)` — Trigger improvement cycle
- `ELOAPI.get_rating(brain, domain)` — Query brain skill rating

## Testing

```bash
pytest tests/ -v
pytest tests/ -v -m gpu  # GPU-specific tests
```

## License

NICTO AI — Proprietary