# NICTO — Autonomous AI Platform

**NICTO — Autonomous AI Platform with Intira Browser, 7-Brain MoE+MLA, 550B ULTRA Model, and Self-Improvement Pipeline**

A fully autonomous AI platform featuring a Chromium-based private browser (Intira), 7-brain mixture-of-experts architecture with MultiHeadLatentAttention, 70 specialist subnetworks, 100 domain specialists, speed reader, advanced neural layers, 550B-scale ULTRA model configuration, and a complete self-improvement pipeline that searches the web and trains itself across 16 domains.

---

## Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Intira Browser** (Chromium-based) | ✅ Ready | NICTO's private browser: search, fetch, navigate, extract, self-train |
| **Master Self-Improvement Pipeline** | ✅ Ready | 16-domain training, GitHub push, 550B ULTRA config |
| 550B ULTRA Model (d_model=8192, 40 layers, 32 experts) | ✅ Ready | ~1.07T total params, ~201B active/token |
| 7-Brain MoE+MLA Architecture (70 subnetworks) | ✅ Ready | 19 heads, forward-pass verified |
| Advanced Neural Layers (MLA, EnhancedMoE, 10+ blocks) | ✅ Ready | Importable and forward-pass tested |
| Speed Reader (SSM + multi-stream) | ✅ Ready | DeepUnderstandingEngine at 5 levels |
| Domain/Coding Specialists | ✅ Ready | 100 domain + 20 coding networks |
| Transformer Training Loop | ✅ Ready | SuperTrainer with SFT/PPO/GRPO/Curriculum |
| NiktoBrain Cognitive Subsystems | ✅ Ready | 12+ subsystems, process() verified |
| NICTO X TreeOfThought | ✅ Ready | MultiPathCoT with 3 parallel chains |
| Learning Infrastructure | ✅ Ready | DatasetBuilder, NeuralTrainer, RewardModel, Curriculum, FeedbackLoop |
| Training Data Generation | ✅ Ready | aknow_nicto_bridge.py imports cleanly |
| Game Engine (18+ genres) | ✅ Ready | NICTOGameBuilder available |
| Colab/Kaggle Training Pipeline | ✅ Ready | colab_train_all.py with 20-training pipeline |
| GGUF Integration | ✅ Ready | gguf_export.py with 20+ quant types |
| CLI (15+ commands) | ✅ Ready | search, train, chat, voice, build, scan, exploit, dashboard, status, etc. |
| Desktop App (React/Tauri) | ✅ Ready | nikto-desktop scaffolding |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        NICTO SYSTEM                              │
├──────────────────┬──────────────────┬───────────────────────────┤
│   nikto-core     │    nicto-x       │     nicto-game            │
│   (Brain AI)     │   (Frontier)     │    (Game Engine)          │
├──────────────────┼──────────────────┼───────────────────────────┤
│   NiktoBrain     │  NictoXOrch      │   GameDirector            │
│   10 subsystems  │  7 agents        │   11 subsystems           │
│   4-model API    │  NeuralCore      │   18+ genres              │
│   Model routing  │  MoE (8 experts) │   Procedural gen          │
├──────────────────┴──────────────────┴───────────────────────────┤
│                    Intira Browser (Chromium)                     │
│   Search · Fetch · Navigate · Extract · Agent · Self-Train      │
│   DuckDuckGo/Bing/Brave · 16-domain Master Pipeline             │
└─────────────────────────────────────────────────────────────────┘
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
│   ├── intira_browser/      # Intira Browser — NICTO's Chromium browser
│   │   ├── browser.py       #   Core browser (tabs, nav, JS, sessions)
│   │   ├── search.py        #   Web search (DuckDuckGo/Bing/Brave)
│   │   ├── extractor.py     #   Content extraction engine
│   │   ├── agent.py         #   Autonomous web interaction agent
│   │   ├── api.py           #   Programmatic API for NICTO brain
│   │   ├── trainer.py       #   Self-training pipeline
│   │   └── master_trainer.py #  16-domain master self-improvement
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

## Intira Browser — NICTO's Private Chromium Browser

Intira is NICTO's own Chromium-based browser engine. It searches the web, fetches pages, extracts content, navigates autonomously, and self-trains by injecting knowledge into NICTO's brain.

| Component | What it does |
|-----------|-------------|
| **IntiraBrowser** | Chromium headless browser: tabs, navigation, JS execution, screenshots, form filling, session persistence |
| **IntiraSearch** | Web search via DuckDuckGo/Bing/Brave through real Chromium with stealth anti-detection |
| **ContentExtractor** | Extracts keywords, headings, links, images, summaries from any web page |
| **IntiraAgent** | Autonomous multi-step browsing: search → navigate → click → fill → extract |
| **IntiraAPI** | Clean async API for NICTO brain to control the browser programmatically |
| **IntiraTrainer** | Self-training pipeline: web data → KnowledgeCore facts + LongTermMemory + Learner skills + TruthEngine |
| **MasterPipeline** | 16-domain self-improvement: searches web across all domains, builds 550B model, pushes to GitHub |

### Data Flow

```
NICTO brain → IntiraAPI.search("topic")
                ↓
         Intira Browser (Chromium headless)
                ↓
         DuckDuckGo / Bing / Brave
                ↓
         Results shown to user via CLI
                ↓
         IntiraTrainer injects into brain:
           + KnowledgeCore — permanent facts
           + LongTermMemory — episodic memories
           + Learner — skills with mastery tracking
           + TruthEngine — verified claims with source reliability
                ↓
         NICTO grows smarter (skills reach MASTER level)
```

### CLI Usage

```bash
# Search the web
python nikto_cli/main.py search "autonomous AI agents" -n 10

# NICTO self-trains from web
python nikto_cli/main.py train "reinforcement learning" -n 5 -m full

# Autonomous mode: NICTO picks what to learn
python nikto_cli/main.py train --autonomous

# Full master pipeline (all 16 domains)
python nikto_cli/main.py train --master

# Specific domains
python nikto_cli/main.py train --master -d "coding,mathematics,ai_ml,business"
```

### 550B ULTRA Model Configuration

| Setting | Value |
|---------|-------|
| d_model | 8192 |
| n_layers | 40 |
| n_experts | 32 (6 active) |
| d_ff | 32768 |
| Total params | 1,074,010,259,456 (~1.07T) |
| Active per token | ~201B |
| Architecture | MoE + GQA + RoPE + FlashAttention + SSM + Speculative Decoding |

### 16 Training Domains

`coding` · `programming` · `mathematics` · `business` · `science` · `engineering` · `ai_ml` · `cybersecurity` · `data_science` · `cloud_devops` · `game_dev` · `networking` · `databases` · `robotics` · `blockchain` · `quantum`

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

# 6. Intira Browser — search and self-train
python nikto_cli/main.py search "quantum computing" -n 5
python nikto_cli/main.py train "machine learning" -n 3 -m full
python nikto_cli/main.py train --master -d "coding,ai_ml,mathematics"

# 7. Training data generation (now ready)
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
| **v8.0.0** | 2026-06 | **Intira Browser** — NICTO's Chromium browser, IntiraSearch, IntiraAgent, IntiraAPI, IntiraTrainer, MasterPipeline (16-domain self-improvement), 550B ULTRA config, GitHub push |
| **v7.0.0** | 2026-06 | MetaHead shape fix, Training Loop fix, aknow_nicto_bridge.py reconstructed (comment-eating bug), 10/12 integration tests pass |
| **v4.0.0** | 2026-06 | 7-brain MoE+MLA architecture (70 subnetworks, 19 heads), speed reader, advanced layers, domain/coding specialists, learning paradigms |
| **v3.1.0** | 2026-06 | SuperNeuralCore, SuperHeadEnsemble, MultiHeadedReasoning, 12 architectural advances |
| **v0.1.0** | 2026-04 | Initial neural architecture experiments |

---

## License

This project is for research and educational purposes.
