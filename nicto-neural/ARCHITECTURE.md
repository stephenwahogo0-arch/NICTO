# NICTO Neural Core V1 — Architecture

## System Diagram

```
                         ┌─────────────────────────┐
                         │      INPUT (text)        │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │    NictoTokenizer         │
                         │  (character-level + BPE)  │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │    NictoEmbedding         │
                         │  (scaled, weight-tying)   │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │  SinusoidalPositional     │
                         │    Encoding               │
                         └────────────┬─────────────┘
                                      │
                    ┌─────────────────▼──────────────────┐
                    │         TransformerCore             │
                    │  (6 TransformerBlocks)              │
                    │  MHA → Add&Norm → FFN → Add&Norm   │
                    └─────────────────┬──────────────────┘
                                      │
                    ┌─────────────────▼──────────────────┐
                    │         MoE Router                  │
                    │  8 Experts, Top-2 Gating            │
                    │  Load Balancing Loss                │
                    └─────────────────┬──────────────────┘
                                      │
                    ┌─────────────────▼──────────────────┐
                    │         BrainHeads (6)              │
                    │  Each: proj → logits + confidence   │
                    └─────────────────┬──────────────────┘
                                      │
              ┌───────────────────────▼───────────────────────┐
              │              BrainRouter                       │
              │  ELO-based selection + curriculum awareness     │
              └───┬───────┬───────┬───────┬───────┬───────┬───┘
                  │       │       │       │       │       │
            ┌─────▼─┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌─▼────┐
            │Primary│ │Anal.│ │Crea.│ │Strat│ │Know.│ │Intuit│
            │Brain  │ │Brain│ │Brain│ │Brain│ │Brain│ │Brain │
            └───┬───┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬───┘
                └────────┼──────┼──────┼──────┼──────┘
                         │      │      │      │
                    ┌────▼──────▼──────▼──────▼────┐
                    │      BrainBoost Ensemble      │
                    │  Fixed mode | Trained mode     │
                    │  Gradient-boosted over brains  │
                    └──────────────┬────────────────┘
                                   │
                    ┌──────────────▼────────────────┐
                    │         OUTPUT                  │
                    └──────────────┬────────────────┘
                                   │
                    ┌──────────────▼────────────────┐
                    │     Post-Processing            │
                    │  Reflection → ELO Update       │
                    │  Memory Store → Experience     │
                    │  Reward Shaping → Hacking Check│
                    │  Consistency σ → Curriculum     │
                    └──────────────────────────────── ┘
```

## Module Dependency Graph

```
neural_core.py
├── brain/consciousness.py
│   ├── neural/transformer.py
│   │   ├── neural/attention.py
│   │   │   └── neural/tensor_ops.py
│   │   └── neural/positional.py
│   ├── neural/moe_router.py
│   ├── neural/brain_heads.py
│   ├── neural/elo_system.py
│   ├── neural/exploration.py
│   ├── neural/model_selector.py
│   ├── perception/tokenizer.py
│   ├── perception/feature_engine.py
│   ├── perception/normalizer.py
│   ├── memory/manager.py
│   │   ├── memory/episodic.py
│   │   ├── memory/semantic.py
│   │   ├── memory/skills.py
│   │   ├── memory/goals.py
│   │   ├── memory/personality.py
│   │   ├── memory/reflection.py
│   │   ├── memory/performance.py
│   │   ├── memory/task_features.py
│   │   ├── memory/consistency.py
│   │   └── memory/experience.py
│   └── brain/{primary,analytical,creative,strategic,knowledge,intuitive}.py
├── reasoning/brainboost.py
├── reasoning/consistency.py
├── learning/rl_agent.py
├── learning/curriculum.py
├── learning/trainer.py
├── learning/reward_shaper.py
├── learning/reward_model.py
├── evolution/validation.py
└── safety/reward_hacking.py
```

## Key Metrics

| Metric | Formula |
|--------|---------|
| Consistency σ | `0.6 * logical_coherence + 0.4 * output_stability` |
| ELO Expected | `1 / (1 + 10^((Rb - Ra) / 400))` |
| ELO Update | `Ra + K * (actual - expected)` |
| Reward | `α*correctness + β*elo_gain + γ*novelty + δ*consistency - ε*hacking` |
| PPO Objective | `min(ratio * A, clip(ratio, 1±ε) * A)` |

## Feature Vector (15 dimensions)

| Dim | Feature | Range |
|-----|---------|-------|
| 0 | task_type_code | 0-5 |
| 1 | domain_code | 0-9 |
| 2 | complexity | 0.0-1.0 |
| 3 | reasoning_depth | int |
| 4 | confidence_trajectory | slope |
| 5 | memory_recall_count | int |
| 6 | recency | 0-168 hours |
| 7 | brain_activation_count | int |
| 8 | time_elapsed_ms | 0-10000 |
| 9 | tool_call_frequency | int |
| 10 | coherence_score | 0.0-1.0 |
| 11 | exploration_rate | current ε |
| 12 | curriculum_level | 0-5 |
| 13 | reward_trajectory | slope |
| 14 | hacking_flag | 0 or 1 |
