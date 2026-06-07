# NIKTO — Autonomous AI System

**NIKTO is not an AI agent. NIKTO is an AI system.**

A unified, self-improving artificial intelligence system with its own cognitive architecture (NICTO Hyperbrain v2.0), AKNOW# deterministic knowledge engine, and a complete game engine capable of producing 1GB+ games.

---

## Programming Languages Used

| Language | Files | Purpose |
|----------|-------|---------|
| **Python** | 516 | Primary language — brain, engines, CLI, builders |
| **AKNOW#** | 24 | Deterministic knowledge engine — seed-based expansion, 64-domain HyperDomainTree, NeuralRosetta, VirtualLab, GenesisCore |
| **Rust** | 53 | High-performance core engine, super kernel, triple engine |
| **Go** | 5 | Background monitor, graph core, hsync engine, odds feed, network scanner |
| **C++** | 2 | Wi-Fi capture, desktop streamer |
| **MATLAB (.m)** | 1 | AKNOW# optimizer module |
| **JavaScript** | 1 | Desktop Electron wrapper |
| **TypeScript** | 1 | React UI with gesture controls |
| **HTML** | 1 | Web interface |
| **CSS** | 1 | Web styling |
| **Shell (sh)** | 2 | Build scripts |
| **Batch (bat)** | 5 | Windows utilities + AKNOW# build |
| **SQL** | 1 | Database operations |
| **R** | 1 | Statistical computing |
| **PHP** | 1 | Server-side scripting |
| **Ada** | 1 | Low-level systems |
| **TOML** | 7 | Configuration |
| **YAML** | 2 | CI/CD configs |
| **JSON** | 488 | Data, manifests, configs |
| **Markdown** | 15 | Documentation |

---

## What NIKTO Is

NIKTO is a full-spectrum AI system with capabilities spanning:

| Domain | Capability |
|--------|-----------|
| **Autonomous Brain** | NICTO Hyperbrain v2.0 — 10 integrated cognitive subsystems (identity, memory, emotion, conscience, reasoning, language, learning, goals, truth, dream) |
| **Deterministic Knowledge** | AKNOW# engine — 64 domains across 14 families, seed-based deterministic expansion (C++ native core, Rust parser, Go CLI, MATLAB optimizer), instant FactTable lookup (463 facts) |
| **Real-Time Intelligence** | GodsEye — live geo-location, weather, time, network awareness |
| **Virtual Labs** | 11 simulation models — SIR/SEIR/SIRD disease modeling, drug discovery, genetics, optimization |
| **Code & Development** | Full project scaffolding, code generation in Python/JS/TS/Rust/Go |
| **Cybersecurity** | Port scanning, CVE lookup, vulnerability assessment, exploit database, threat intelligence |
| **Game Engine** | Full ECS engine with physics, rendering, audio, AI, VFX, procedural generation, networking, visual scripting |
| **1GB Game Builder** | Procedural audio synthesis, terrain generation, dungeon generation — produces complete playable games with 1GB+ of assets |
| **Voice** | Speech-to-text, text-to-speech |
| **Multi-Modal Input** | Images, PDFs, audio, URLs, code files |
| **Plugin System** | Load Python plugins by path, install from PyPI |
| **Self-Repair** | Health checks, broken import detection, pip-based fix |

---

## Architecture

```
NIKTO/
├── nikto/                          # Core NIKTO AI system
│   ├── brain/                      # Autonomous cognitive subsystems
│   │   ├── core.py                 # NiktoBrain — central orchestrator
│   │   ├── aknow_bridge.py         # AKNOW# integration (64 domains)
│   │   ├── fact_table.py           # 463 instant-lookup facts
│   │   ├── gods_eye.py             # Real-time geo/weather/time
│   │   ├── virtual_labs.py         # 11 simulation models
│   │   ├── conscience.py           # 10 moral rules, safety
│   │   ├── reasoner.py             # 10 thinking styles
│   │   ├── meta_cognition.py       # Self-awareness, bias detection
│   │   ├── truth_engine.py         # Anti-hallucination
│   │   ├── dream/steerer.py        # Dream patterns
│   │   └── ...                     # Identity, memory, emotion, language, learner, goals
│   ├── autopilot/                  # Autonomous operation
│   ├── security/                   # Scanner, exploit DB, threat intel
│   ├── builder/                    # Codegen, project scaffolding
│   └── ...                         # Voice, plugins, reporting, swarm
├── kyros/                          # Game engine & arcade games
│   ├── game_engine/                # Full ECS game engine
│   │   ├── core.py                 # 866 lines — engine, scenes, cameras, collision
│   │   ├── physics.py              # 506 lines — rigid bodies, joints, soft bodies
│   │   ├── renderer.py             # 280 lines — lighting, shadows, post-processing
│   │   ├── audio.py                # 337 lines — 3D audio, synthesis, effects
│   │   ├── ai.py                   # 380 lines — behavior trees, state machines, pathfinding
│   │   ├── animation.py            # 324 lines — skeletal animation, IK, sprite sheets
│   │   ├── vfx.py                  # 335 lines — particle systems, presets
│   │   ├── procedural.py           # 190 lines — terrain, dungeon, quest generation
│   │   ├── builder.py              # 1829 lines — 10 game templates + build system
│   │   ├── asset_generator.py      # 1GB+ procedural asset pipeline
│   │   └── visual_script.py        # 412 lines — Blueprint-like node graphs
│   └── games/                      # Playable arcade games
│       └── engine.py               # Pong, Snake, Tetris, Platformer, RogueLike
├── nicto_neural/                   # NICTO Neural systems
│   ├── nicto_game_builder.py       # Standalone raycasting FPS generator
│   └── nicto_outputs/games/        # Generated game samples
├── packages/                       # Rust high-performance engines
│   ├── nikto-core-engine/          # Rust ECS/renderer/world gen
│   ├── nikto-super-kernel/         # Rust neural/memory/security/swarm
│   └── nikto-triple-engine/        # Rust triple-engine
└── AKNOW##/                        # AKNOW# deterministic knowledge engine
    ├── aknow_omega.py              # GenesisCore, HyperDomainTree (64 domains)
    ├── genesis_core.cpp            # Native C++ core (compiled to genesis_core.dll)
    ├── doll_parser.rs              # Rust parser
    ├── build_iq.go                 # Go CLI tool
    ├── optimizer.m                 # MATLAB optimizer
    ├── aknowc.exe                  # AKNOW# native compiler
    └── sdk/                        # Python SDK, NeuralRosetta
```

---

## Game Engine

NIKTO's game engine is a complete, professional-grade system:

### Features
- **ECS Architecture** — GameObject/Scene/Component system with full lifecycle
- **Physics Engine** — Rigid bodies, joints (distance/spring/hinge), soft bodies (cloth), destruction system, gravity wells, collision layers
- **Renderer** — Dynamic lighting, soft shadows, bloom, vignette, depth of field, color grading, skybox with day/night cycle
- **Audio Engine** — 3D positional audio, Doppler effect, DSP effects (reverb/chorus/delay), audio buses, WAV synthesizer
- **AI Engine** — Behavior trees, state machines, utility AI, A* pathfinding, nav grids
- **Animation** — Skeletal animation, forward/inverse kinematics, sprite sheets, motion warping
- **VFX System** — Niagara-like particle system with 8 presets (fire, smoke, explosion, spark, magic, rain, snow)
- **Procedural Generation** — Perlin noise terrain, biome maps, dungeon generation (rooms + corridors), quest generation
- **Visual Scripting** — Blueprint-like node graph with 19 node types, serialization
- **Networking** — UDP multiplayer server/client
- **1GB Asset Pipeline** — Procedural audio synthesis (WAV), terrain heightmaps, biome maps, dungeon data

### Game Templates (10 genres)
1. **2D Platformer** — Side-scrolling with enemies, coins, power-ups
2. **Top-Down RPG** — Movement, NPCs, inventory, combat
3. **Raycasting FPS** — Wolfenstein-style 3D engine
4. **Top-Down Racer** — Multiple tracks, AI opponents
5. **Match-3 Puzzle** — Swap-and-match mechanics
6. **Tower Defense** — Wave-based enemy spawning, upgradeable towers
7. **2D Fighter** — Versus combat with combos and health bars
8. **Life Simulation** — Villagers, needs, building, relationships
9. **Space Shooter** — Side-scrolling ship combat
10. **Stealth Game** — Guards, line of sight, hiding mechanics

### Generated Game Samples
- `nicto_neural/nicto_outputs/games/test_game.py` — 138-line raycasting FPS (12x12 map, colored walls, minimap, crosshair)
- `nicto_outputs/games/nicto_openworld.py` — 256x256 procedurally generated world
- `nicto_outputs/games/nicto_dungeoncrawl.py` — 128x128 dungeon explorer
- `nicto_outputs/games/nicto_survival.py` — 200x200 survival world

Run any with: `python <file>.py` (requires `pygame`)

---

## Quick Start

```bash
# Install dependencies
pip install -e packages/nikto-core
pip install -e packages/kyros-core

# Test the brain
python -c "from nikto import NiktoBrain; b = NiktoBrain(); print(b.process('What is the speed of light?'))"

# Build a 1GB game world
python -c "from kyros.game_engine import GameEngine; GameEngine.build_1gb_game('./my_game')"

# Run a generated game
python nicto_outputs/games/nicto_openworld.py
```

---

## Version History

- **v3.0** — 1GB Game Engine, procedural asset pipeline, 4 autonomous engines (Autopilot Pro, Zero-Capital, Eagle Eye, Future Prediction)
- **v2.1** — Real AI pipeline (training, inference, image/video/game generation)
- **v2.0** — NICTO Hyperbrain v2.0 (12 architectural advances), AKNOW# integration
- **v1.0** — Initial autonomous brain with 10 subsystems
