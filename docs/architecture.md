# NICTO Architecture Guide

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        NICTO SYSTEM                          │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  nikto-core  │   nicto-x    │  nicto-game  │ nikto-desktop  │
│  (Brain AI)  │ (Frontier)   │ (Game Engine)│   (Desktop)    │
├──────────────┼──────────────┼──────────────┼────────────────┤
│  NiktoBrain  │ NictoXOrch   │ GameDirector │  React + Tauri │
│  10 subsys   │ 7 agents     │ 11 subsystems│  4-model UI    │
│  4-model API │ Neural Core  │ 18+ genres   │  ModelSelector │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

## 4-Model Pipeline

```
Request → X-Model-Id header → Dispatcher
  ├── Kyros  → process_kyros()   → Identity + Memory (0.6ms)
  ├── Omega  → process()         → Full NiktoBrain (2.9ms)
  ├── Main   → process_main()    → +Security Scanner (3.0ms)
  └── X      → process_x()       → NictoXOrchestrator (2.4s)
```

## Cognitive Architecture (NiktoBrain)

```
NiktoBrain
├── Identity      — Self-concept, personality, core values
├── Knowledge     — Fact/concept/belief store, inference engine
├── Memory        — Tag-indexed, importance-scored, decay + consolidation
├── Emotion       — Valence/arousal model, trigger learning
├── Conscience    — Moral reasoning, ethical rules, dilemma detection
├── Reasoner      — 10 thinking styles, chain-of-thought, metacognition
├── Language      — Tokenization, entity extraction, sentiment, intent
├── Learner       — Skill acquisition, mastery tracking, curiosity
├── Goals         — Hierarchical goal management, prioritization
├── Truth Engine  — Fact verification, contradiction detection
├── Dream Steerer — Memory consolidation, pattern extraction
├── Performance   — Time-series metrics, trend analysis
├── Meta-Cognition — Self-awareness, bias detection, quality assessment
├── Autopilot     — Automated task execution, scheduling
├── Eagle Eye     — Pattern detection, anomaly/threat/opportunity scanning
└── Future Engine — Trend extrapolation, prediction, Bayesian updating
```

## NICTO X Architecture (Frontier)

```
NictoXOrchestrator
├── NeuralCore        — MoE transformer, numpy-accelerated (70ms)
├── NeuralTokenizer   — 32K vocab, embedding generation
├── 7 Agents          — Research, Coding, Planning, Evaluation, Memory, Vision, Security
├── Reasoning         — TreeOfThought, SelfReflection, ConfidenceEstimator
├── Memory            — Episodic, Semantic, Working, Consolidation
├── Knowledge         — KnowledgeGraph, VectorStore (numpy)
├── Software Engineer — 8-language code gen, test gen, validation
├── Scientific Research — Literature review, hypothesis, experiment planning
├── Self-Improvement  — BenchmarkRunner, skill tracking, improvement plans
├── Distributed Exec  — Priority queue, worker pool, horizontal scaling
└── Auth/Security     — API key management, token validation
```

## Game Engine Architecture

```
GameDirector
├── Planner     — Game concept, genre selection
├── Architect   — World layout, biome generation
├── WorldGen    — 5 types: FPS, Maze, Dungeon, OpenWorld, Survival
├── Characters  — NPC generation, dialogue trees
├── Story       — Quest generation, narrative arcs
├── CodeGen     — Pygame code synthesis
├── Audio       — Procedural WAV synthesis (11 SFX, genre music)
├── Textures    — Color palette generation
├── Testing     — Playability validation
├── Optimization — Frame rate, memory usage
└── Export      — Multi-platform (Windows, Linux, Android, Web)
```

## 4-Model Routing

```
Frontend (ModelSelector)
       │
       ▼
   X-Model-Id header
       │
       ▼
   Unified Server (port 5000)
       │
       ├── nicto_kyros → NiktoBrain.process_kyros()
       ├── nicto_omega → NiktoBrain.process()
       ├── nicto_main  → NiktoBrain.process_main()
       └── nicto_x     → NiktoBrain.process_x()
                              │
                              ▼
                    NictoXOrchestrator (if available)
```
