# CHANGELOG

All notable changes to the NICTO project are documented here.

## [2.1.0] — 2026-06-14

### Added
- **4-Model Pipeline**: Kyros (minimal, 0.6ms), Omega (balanced, 2.9ms), Main (full, 3.0ms), X (frontier, 2.4s)
- **Unified Server**: Single API server dispatches to all 4 models via `X-Model-Id` header
- **Frontend ModelSelector**: Capability badges, tier indicators, vertical layout for 4 models
- **Colab Training Pipeline**: Full notebook (`colab_nicto_training.ipynb`) — 4 base models × 5 adapters
- **GGUF Integration**: `scripts/integrate_gguf.py` wires trained weights into NeuralCore
- **Kaggle Data Prep**: 5 training subsets from 361K ChatML entries with CoT/multi-turn/code enhancement
- **Multi-Model Verification**: `scripts/train_and_verify_all_models.py` — 100% success across all 4 models
- **Documentation**: Full directory structure with READMEs, architecture/setup/training/development guides
- **CHANGELOG.md**: This file

### Changed
- `server.py`: Unified model routing, `/models` endpoint, CLI `--port`/`--no-auth` args
- `brain/core.py`: Added `process_kyros()`, `process_main()`, `process_x()` methods
- `run_all.py`: Single unified server launcher with 4-model ASCII banner
- `models.ts`: 4 model configs (Kyros/Omega/Main/X) with distinct capabilities
- `.gitignore`: Added kaggle_data/, colab_output/, verification reports, .mypy_cache/

### Fixed
- `process_main()`: Scanner method corrected from `scan()` to `search_vulns()`
- `process_x()`: Async coroutine handling with proper event loop management

### Verified
- NICTO X: 66/66 tests pass
- Game Engine: 17/18 tests pass
- 4-Model Benchmark: 100% success rate, all pipelines verified

## [2.0.0] — 2026-05

### Added
- NICTO Hyperbrain v2.0 — 12 architectural advances
- Multi-Path Chain-of-Thought reasoning
- Persistent Cross-Session Memory (SQLite)
- Real-Time Self-Improvement (micro-PPO)
- Calibrated Confidence with domain multipliers
- Domain Specialization Scores (8 domains)
- Super Context with Compression (1M token target)
- Pattern Discovery Engine
- Hallucination Elimination System
- Meta-Learning Engine
- Super Intelligence Benchmarking
- Transparent Reward Function
- NeuralCore Full Integration

### Changed
- All 92 advanced_evolution classes replaced with real implementations
- 168 fake brain regions removed
- 31 simulator instances eliminated
- All engines perform real computations

## [1.0.0] — 2026-04

### Added
- NiktoBrain with 10 cognitive subsystems
- AKNOW# deterministic knowledge engine
- Game engine with 18+ genres
- Desktop app (React + Tauri)
- Voice interface (STT/TTS)
- Self-repair engine
- Plugin system
- Cybersecurity toolkit
- CLI with 15+ commands
- Web UI dashboard
