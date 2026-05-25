# NICTO Neural Core V1 — Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NICTO NEURAL CORE                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      PERCEPTION LAYER                        │   │
│  │  Tokenizer → Embedding → Feature Engine → Normalizer        │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │                    NEURAL FOUNDATION                         │   │
│  │  Transformer Core (6 layers, 8 heads, 512 dim)              │   │
│  │  MoE Router (8 experts, top-2 gating)                       │   │
│  │  Brain Head Ensemble (6 specialist heads)                    │   │
│  │  Model Selector (adaptive path by data size)                 │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │                    MEMORY SYSTEM                             │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐   │   │
│  │  │Episodic│ │Semantic│ │ Skills │ │ Goals  │ │Personality│   │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘   │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐   │   │
│  │  │Reflect.│ │Perform.│ │TaskFeat│ │Consist.│ │Experience│   │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘   │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │                    6-BRAIN SYSTEM                            │   │
│  │  ┌─────────┐ ┌───────────┐ ┌─────────┐ ┌──────────┐         │   │
│  │  │ Primary │ │Analytical │ │ Creative │ │ Strategic│         │   │
│  │  └─────────┘ └───────────┘ └─────────┘ └──────────┘         │   │
│  │  ┌─────────┐ ┌───────────┐ ┌────────────────────────────┐   │   │
│  │  │Knowledge│ │ Intuitive │ │   BrainRouter (ELO-weighted)│   │   │
│  │  └─────────┘ └───────────┘ └────────────────────────────┘   │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │                   REASONING LAYER                            │   │
│  │  Planner → BrainBoost → Chain Engine → Confidence →          │   │
│  │  Evaluator → Reflection → Consistency → Interpretability    │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │                    LEARNING ENGINE                           │   │
│  │  Dataset Builder → Trainer (Supervised/RL) → Reward Model    │   │
│  │  PPO Agent → Experience Buffer → Curriculum → Feedback Loop  │   │
│  │  Fine-Tuner (LoRA Q,K,V,O)                                   │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │                   EVOLUTION ENGINE                           │   │
│  │  EvolutionEngine → Improvement → Validation → CurriculumMgr │   │
│  │  CostEstimator                                               │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │                EXECUTION + SAFETY                            │   │
│  │  ToolRegistry → ActionExecutor → Agents → Orchestration     │   │
│  │  PermissionMgr → RollbackMgr → AuditLogger → PolicyEngine    │   │
│  │  RewardHackingDetector                                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Mathematical Formulations

### ELO Rating

```
E_A = 1 / (1 + 10^((R_B - R_A) / 400))
R_A' = R_A + K * (S_A - E_A)
```

Where R_A is current rating, K is factor (default 32), S_A is outcome (1=win, 0=loss), E_A is expected score.

### Transformer Attention

```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W_O
```

### BrainBoost (Gradient Boosted Ensemble)

```
F_0(x) = 0
For m = 1 to M:
  r_im = -[∂L(y_i, F(x_i)) / ∂F(x_i)]
  h_m = argmin Σ(r_im - h(x_i))^2
  F_m(x) = F_{m-1}(x) + ν * h_m(x)
```

Where ν is the learning rate (shrinkage), M is number of stages.

### PPO (Proximal Policy Optimization)

```
L^CLIP(θ) = E_t[min(r_t(θ)A_t, clip(r_t(θ), 1-ε, 1+ε)A_t)]
```

Where r_t(θ) = π_θ(a_t|s_t) / π_θ_old(a_t|s_t), A_t is advantage estimate.

### Memory Schema (SQLite)

Each store uses sqlite3 with WAL journaling:

```sql
CREATE TABLE entries (
    key TEXT PRIMARY KEY,
    value TEXT,
    metadata TEXT,
    timestamp REAL,
    embedding BLOB
);
```

FAISS index files stored alongside for vector similarity search.

## Safety Policies

| Policy | Default | Description |
|--------|---------|-------------|
| Recursion depth | 10 | Max nested reasoning depth |
| Max iterations | 100 | Max steps per task |
| Rate limit (brain:think) | 50/min | Prevents runaway loops |
| Rate limit (execution:shell) | 10/min | Sandboxed execution |
| Memory protection | 1 GB | Max per store |

## Reward Hacking Detection

```
If reward_trend > 0.5 AND quality_trend < 0.05 → FLAG
If reward_variance < 0.01 AND quality_trend < -0.1 → FLAG
```

Flagged brains have rewards penalized by suspicion score.

## Curriculum Levels

| Level | Description | Unlock |
|-------|-------------|--------|
| 0 | Single-step tasks | Default |
| 1 | Multi-step (2-3) | 75% plateau over 5 evals |
| 2 | Domain depth | Level 1 mastery |
| 3 | Cross-domain | Level 2 mastery |
| 4 | Long-horizon | Level 3 mastery |
| 5 | Meta-reasoning | Level 4 mastery |

## File Map

```
nicto-neural/
├── neural_core.py          # Top-level facade
├── perception/             # Input pipeline (8 files)
├── neural/                 # Core computation (10 files)
├── memory/                 # Persistent stores (12 files)
├── brain/                  # 6-brain system (8 files)
├── reasoning/              # Reasoning engine (8 files)
├── learning/               # Training engine (9 files)
├── evolution/              # Self-evolution (5 files)
├── execution/              # Agent system (4 files)
├── safety/                 # Safety controls (5 files)
├── api/                    # Public interfaces (6 files)
├── tests/                  # 22 test files
├── setup.py
├── README.md
└── ARCHITECTURE.md
```
