# NICTO — Autonomous AI Platform

**NICTO — neural architecture research platform for multi-brain MoE+MLA systems.**

A research codebase exploring a 7-brain mixture-of-experts architecture with MultiHeadLatentAttention, 70 specialist subnetworks, speed reader, advanced neural layers, and self-contained training infrastructure.

---

## Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| 7-Brain MoE+MLA Architecture (70 subnetworks) | 🏗️ Building | 19 heads, forward-pass tested |
| Advanced Neural Layers (MLA, EnhancedMoE, 10 blocks) | 🏗️ Building | Importable and forward-pass tested |
| Speed Reader (SSM + multi-stream) | 🏗️ Building | DeepUnderstandingEngine at 5 levels |
| Domain/Coding Specialists | 🏗️ Building | 100 domain + 20 coding networks |
| Transformer Training Loop | 🏗️ Building | Cross-entropy LM training |
| NiktoBrain Cognitive Subsystems | 🏗️ Building | 12 subsystems, template reasoning |
| NICTO X TreeOfThought | 🏗️ Building | Replaced templates with Anthropic API |
| Training Data Generation | ✅ Ready | aknow_nicto_bridge.py reconstructed and verified |
| Game Engine (18+ genres) | 🏗️ Building | Procedural generation |
| Colab/Kaggle Training Pipeline | 🏗️ Building | Notebooks prepared |
| GGUF Integration | 🏗️ Building | Integration scripts |
| Desktop App (React/Tauri) | 🏗️ Building | Frontend scaffolding |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        NICTO SYSTEM                          │
├──────────────────┬──────────────────┬───────────────────────┤
│   nikto-core     │    nicto-x       │     nicto-game        │
│   (Brain AI)     │   (Frontier)     │    (Game Engine)      │
├──────────────────┼──────────────────┼───────────────────────┤
│   NiktoBrain     │  NictoXOrch      │   GameDirector        │
│   10 subsystems  │  7 agents        │   11 subsystems       │
│   4-model API    │  NeuralCore      │   18+ genres          │
│   Model routing  │  MoE (8 experts) │   Procedural gen      │
└──────────────────┴──────────────────┴───────────────────────┘
```

### 4-Model Pipeline

```
Request → X-Model-Id header → Unified Server (port 5000)
  ├── ⚡ Kyros  → process_kyros()   → Identity + Memory     (0.6ms)
  ├── ⚖️ Omega  → process()         → Full NiktoBrain       (2.9ms)
  ├── 🔧 Main   → process_main()    → + Security Scanner    (3.0ms)
  └── 🚀 X      → process_x()       → NictoXOrchestrator    (2.4s)
```

---

## Repository Structure

```
NICTO/
├── packages/
│   ├── nikto-core/          # Brain AI: NiktoBrain, cognitive subsystems, API server
│   │   └── src/nikto/
│   │       ├── brain/       # 10 cognitive subsystems (identity, memory, emotion...)
│   │       ├── server.py    # Unified API server (4-model routing)
│   │       ├── run_all.py   # Server launcher
│   │       ├── security/    # Scanner, exploit DB, threat intel
│   │       ├── autopilot/   # Autonomous operation
│   │       └── builder/     # Codegen, project scaffolding
│   ├── nicto-x/             # Frontier AI: neural core, agents, reasoning
│   │   └── src/nicto_x/
│   │       ├── neural/      # NeuralCore (MoE transformer, numpy-accelerated)
│   │       ├── agents/      # 7 agents (Research, Coding, Planning, Evaluation, Memory, Vision, Security)
│   │       ├── reasoning/   # TreeOfThought, SelfReflection, ConfidenceEstimator
│   │       ├── memory/      # Episodic, Semantic, Working, Consolidation
│   │       ├── knowledge/   # KnowledgeGraph, VectorStore
│   │       ├── software/    # 8-language code generation
│   │       ├── research/    # Literature review, hypothesis gen
│   │       └── distributed/ # Worker pool, task queue
│   ├── nicto-game/          # Game engine: procedural generation, audio, export
│   │   └── src/nicto_game/
│   │       ├── core/        # GameDirector, config, world gen
│   │       ├── audio/       # Procedural WAV synthesis
│   │       ├── codegen/     # Pygame code generation
│   │       └── export/      # Multi-platform export
│   └── nikto-desktop/       # Desktop app (React + Tauri + Vite)
│       └── src/
│           ├── components/  # ModelSelector, CredentialManager, ChatView
│           ├── config/      # 4-model configuration
│           └── utils/       # API client with X-Model-Id routing
├── nicto_neural/            # Training infrastructure, neural modules
│   ├── training_data/       # ChatML datasets (361K entries)
│   ├── train_nicto.py       # Unsloth LoRA training pipeline
│   ├── build_training_data.py  # ChatML data generation
│   └── build_super_data_v3.py  # 57-domain synthetic data
├── nikto_cli/               # Command-line interface
├── scripts/                 # Build, test, deployment scripts
│   ├── kaggle_prepare_data.py     # Data subset splitting
│   ├── colab_train_all.py         # Colab training pipeline
│   ├── integrate_gguf.py          # GGUF weight integration
│   └── train_and_verify_all_models.py  # Multi-model benchmark
├── docs/                    # Documentation
│   ├── architecture.md      # System architecture guide
│   ├── setup.md             # Installation guide
│   ├── training.md          # Training guide
│   └── development.md       # Developer guide
├── kaggle_data/             # Training data subsets (gitignored)
├── notebooks/               # Colab notebooks
├── datasets/                # Dataset documentation
├── training/                # Training infrastructure docs
├── evaluation/              # Benchmark and evaluation docs
├── agents/                  # Agent system docs
├── memory/                  # Memory system docs
├── tools/                   # Tool system docs
├── deployment/              # Deployment configuration
└── configs/                 # Configuration files
```

---

## Cognitive Architecture (NiktoBrain)

| Subsystem | Function | File |
|-----------|----------|------|
| **Identity** | Self-concept, personality, core values | `brain/identity.py` |
| **Knowledge** | Fact/concept/belief store, inference engine | `brain/knowledge.py` |
| **Memory** | Tag-indexed, importance-scored, decay + consolidation | `brain/memory.py` |
| **Emotion** | Valence/arousal model, trigger learning | `brain/emotion.py` |
| **Conscience** | Moral reasoning, ethical rules, dilemma detection | `brain/conscience.py` |
| **Reasoner** | 10 thinking styles, chain-of-thought, metacognition | `brain/reasoner.py` |
| **Language** | Tokenization, entity extraction, sentiment, intent | `brain/language.py` |
| **Learner** | Skill acquisition, mastery tracking, curiosity | `brain/learner.py` |
| **Goals** | Hierarchical goal management, prioritization | `brain/goals.py` |
| **Truth Engine** | Fact verification, contradiction detection | `brain/truth_engine.py` |
| **Dream Steerer** | Memory consolidation, pattern extraction | `dream/steerer.py` |
| **Performance** | Time-series metrics, trend analysis | `metrics/performance_graph.py` |
| **Meta-Cognition** | Self-awareness, bias detection, quality assessment | `brain/meta_cognition.py` |
| **Eagle Eye** | Pattern detection, anomaly/threat scanning | `eagle_eye/enhanced_eye.py` |
| **Future Engine** | Trend extrapolation, Bayesian prediction | `prediction/future_engine.py` |

---

## NICTO X — Frontier Agent System

| Agent | Responsibility | Capabilities |
|-------|---------------|--------------|
| **Research** | Web search, literature review | DuckDuckGo + Wikipedia, deep search, gap analysis |
| **Coding** | Multi-language code generation | Python, JS, TS, Rust, Go, Java, C++, Swift |
| **Planning** | Task decomposition | Recursive decomposition, dependency tracking |
| **Evaluation** | Response grading | 6-criterion rubric, A-F scoring |
| **Memory** | Retrieval and consolidation | Episodic search, semantic query, working memory |
| **Vision** | Image analysis | Color histograms, edge detection, OCR |
| **Security** | Vulnerability detection | SQLi/XSS patterns, 17 port signatures, CVE lookup |

**Neural Core**: Experimental MoE transformer (8 experts, top-2 routing, 8-head attention, 131K token context, numpy-accelerated). Quarantined behind `NIKTO_ENABLE_EXPERIMENTAL=1` until verified.

---

## Game Engine

18+ genres, procedural generation, multi-platform export:

| Genre | Description |
|-------|-------------|
| FPS | Raycasting 3D engine |
| RPG | Top-down with quests, inventory |
| Platformer | Side-scrolling with physics |
| Racer | Top-down with AI opponents |
| Puzzle | Match-3 mechanics |
| Tower Defense | Wave-based, upgradeable towers |
| Fighter | Versus combat with combos |
| Survival | Resource management |
| Stealth | Line-of-sight, hiding |
| Open World | Procedural terrain, biomes |
| Dungeon Crawler | Room-corridor generation |
| Simulation | Life sim with needs/relationships |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -e packages/nikto-core
pip install -e packages/nicto-x
pip install -e packages/nicto-game

# 2. Start API server (all 4 models)
python packages/nikto-core/src/nikto/run_all.py --no-auth

# 3. Test with different models
curl -X POST http://127.0.0.1:5000/chat \
  -H "X-Model-Id: nicto_kyros" \
  -d '{"message":"Hello, what is AI?"}'

curl -X POST http://127.0.0.1:5000/chat \
  -H "X-Model-Id: nicto_main" \
  -d '{"message":"Scan this for vulnerabilities: SELECT * FROM users WHERE id=1"}'

# 4. Desktop app
cd packages/nikto-desktop && npm install && npm run dev

# 5. Run verification
python packages/nicto-x/tests/test_all.py
python scripts/train_and_verify_all_models.py

# 6. Training data generation (now ready)
python scripts/build_training_data.py
python scripts/train_nicto.py
```

---

## Training on Colab

1. Open `colab_nicto_training.ipynb` in Google Colab with GPU runtime
2. Trains 4 base models (Phi-3, Llama-3.2, Qwen2.5-7B, Mistral-7B) × 5 adapters each
3. Outputs GGUF files to Google Drive
4. Integrate with `python scripts/integrate_gguf.py`
5. Training data generation now ready via `python scripts/build_training_data.py`

---



## Version History
| Version | Date | Highlights |
|---------|------|------------|
| **v7.0.0** | 2026-06 | MetaHead shape fix, Training Loop fix, aknow_nicto_bridge.py reconstructed (comment-eating bug), 10/12 integration tests pass |
| **v4.0.0** | 2026-06 | 7-brain MoE+MLA architecture (70 subnetworks, 19 heads), speed reader, advanced layers, domain/coding specialists, learning paradigms |
| **v3.1.0** | 2026-06 | SuperNeuralCore, SuperHeadEnsemble, MultiHeadedReasoning, 12 architectural advances |
| **v0.1.0** | 2026-04 | Initial neural architecture experiments |

---

## License

This project is for research and educational purposes.
