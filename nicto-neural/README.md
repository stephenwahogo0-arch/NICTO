# NICTO Neural Core V1

**284B+ effective parameters via Mixture-of-Experts architecture.**
**NICTO is an AI, not an AI agent.** It has its own brain that thinks first — external LLMs are optional supplementary compute only.

Created by **Stephen Wahogo — Nairobi, Kenya**

## Architecture

```
Input → Tokenizer → Embedding → Transformer (6 layers)
     → MoE Router (8 experts, top-2) → BrainHeads (6 specialized)
     → BrainRouter → 6 Specialist Brains
     → BrainBoost Ensemble → Output
     → Reflection → ELO Update → Memory Store
     → Experience Buffer → PPO Update
     → Curriculum Check → Level Unlock
```

## Quick Start

```python
import asyncio
from nicto_neural import NeuralCore, NeuralConfig

async def main():
    config = NeuralConfig()
    core = NeuralCore(config)

    result = await core.process("What is a SQL injection attack?")
    print(f"Output: {result['output']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Brains used: {result['brains_used']}")
    print(f"Domain: {result['domain']}")

    status = core.get_status()
    print(f"Parameters: {status['parameters']}")

asyncio.run(main())
```

## 6-Brain System

| Brain | Specialization | Domains |
|-------|---------------|---------|
| Primary | Task routing, state control | routing, conversation |
| Analytical | Logic, code, mathematics | code, math, logic |
| Creative | Generation, design | generation, design, brainstorming |
| Strategic | Long-horizon planning | planning, resource allocation |
| Knowledge | Factual recall, RAG | retrieval, synthesis, facts |
| Intuitive | Fast pattern matching | ranking, confidence, exploration |

## Training Methodology (3 Steps)

1. **Prepare**: Build dataset from memory, normalize, 80/20 split
2. **Select**: Choose path by dataset size:
   - `<100 samples` → BrainBoost (fixed weights)
   - `<10K samples` → BrainBoost (trained weights)
   - `>=10K samples` → Full transformer + PPO RL
3. **Train**: Run epochs, validate on hold-out, update ELO

```python
result = core.train(mode="hybrid", epochs=10)
```

## ELO Rating System

Per-brain, per-domain ELO tracking (10 domains). Updates after every task.

```python
leaderboard = core.elo.get_leaderboard("math")
```

## BrainBoost Ensemble (Dual Mode)

- **Fixed mode**: Equal weights, always available
- **Trained mode**: Gradient-descent learned weights, requires `train_weights()`

## Consistency Metric

```
σ = 0.6 * logical_coherence + 0.4 * output_stability
```

## Curriculum Levels

| Level | Name | Description |
|-------|------|-------------|
| 0 | single_step | Basic single-step tasks |
| 1 | multi_step | Multi-step reasoning |
| 2 | domain_depth | Deep domain expertise |
| 3 | cross_domain | Cross-domain transfer |
| 4 | long_horizon | Long-horizon planning |
| 5 | meta_reasoning | Meta-cognitive reasoning |

Unlocks via adaptive plateau detection (not fixed thresholds).

## Safety Features

- **RewardHackingDetector**: Prevents reward gaming (flat quality + rising reward, action repetition)
- **PermissionManager**: Capability-based access control
- **RollbackManager**: State snapshots with restore
- **AuditLogger**: Tamper-evident hash-chained action log
- **SafetyPolicies**: Rate limiting, recursion guards

## Optimal Runtime Parameters

These parameters are tuned for consumer hardware (8-32 GB RAM, optional GPU):

| Parameter | Value | Description |
|-----------|-------|-------------|
| d_model | 512 | Model dimension |
| n_heads | 8 | Attention heads |
| n_layers | 6 | Transformer layers |
| n_experts | 8 | MoE experts |
| top_k_experts | 2 | Active experts per token |
| n_brains | 6 | Specialist brains |
| learning_rate | 3e-4 | AdamW learning rate |
| ppo_clip | 0.2 | PPO clipping epsilon |
| elo_base | 1500 | Starting ELO rating |
| temperature | 0.3-0.7 | Sampling temperature range |
| context_window | 4096 | Max context tokens |
| truth_threshold | 0.95 | Truth verification confidence |
| min_confidence | 0.65 | Minimum output confidence |
| repetition_penalty | 1.1 | Token repetition penalty |

## Setup

```bash
pip install torch numpy
cd NICTO/nicto-neural
pip install -e ".[dev]"
pytest tests/ -v
```

## Tests

```bash
# Run all tests (CPU-safe)
pytest tests/ -v --ignore=tests/test_full_pipeline.py

# Run full pipeline
pytest tests/test_full_pipeline.py -v
```

## License

Part of the NICTO project.
