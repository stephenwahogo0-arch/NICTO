# NICTO Documentation

Architectural and user documentation for the NICTO AI platform.

## Contents

| Document | Description |
|----------|-------------|
| `setup.md` | Installation and configuration guide |
| `architecture.md` | System architecture overview |
| `training.md` | Training pipeline documentation |
| `development.md` | Developer guide |
| `deployment.md` | Deployment and operations guide |
| `api.md` | API reference |

## Core Architecture

NICTO is organized as a monorepo with four packages:

```
packages/
├── nikto-core/    — Brain, cognitive subsystems, API server
├── nicto-x/       — Frontier AI: neural core, agents, reasoning, distributed execution
├── nicto-game/    — Game engine: procedural generation, audio, export
└── nikto-desktop/  — Desktop UI (React/Tauri)
```

## Quick Links

- [Main README](../README.md)
- [Architecture Guide](architecture.md)
- [Setup Guide](setup.md)
- [Training Guide](training.md)
