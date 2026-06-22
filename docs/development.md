# NICTO Development Guide

## Repository Structure

```
NICTO/
├── packages/
│   ├── nikto-core/     — Brain AI: NiktoBrain, cognitive subsystems, API server
│   ├── nicto-x/        — Frontier AI: neural core, agents, reasoning, distributed
│   ├── nicto-game/     — Game engine: procedural generation, audio, export
│   └── nikto-desktop/  — Desktop UI: React + Tauri + Vite
├── nicto_neural/       — Training infrastructure, neural modules, hyperbrain
├── nikto_cli/          — Command-line interface
├── scripts/            — Build, test, deployment scripts
├── docs/               — Documentation
├── tests/              — Integration tests
├── kaggle_data/        — Training data subsets (gitignored)
├── notebooks/          — Jupyter/Colab notebooks
└── configs/            — Configuration files
```

## Coding Standards

- **Python**: Type hints, docstrings, snake_case functions
- **TypeScript**: TypeScript strict mode, PascalCase components, camelCase functions
- **Rust**: Rust edition 2021, snake_case, Result returns
- All code must import cleanly (no broken imports)
- Tests required for all new modules

## Development Workflow

```bash
# 1. Run tests before committing
python packages/nicto-x/tests/test_all.py

# 2. Verify TypeScript builds
cd packages/nikto-desktop && npx tsc --noEmit

# 3. Start development server
python packages/nikto-core/src/nikto/run_all.py --no-auth

# 4. Desktop dev mode
cd packages/nikto-desktop && npm run dev
```

## Adding a New Feature

1. Implement in the appropriate package
2. Add type hints and docstrings
3. Write tests (minimal: import + init test)
4. Run existing test suite to verify no regressions
5. Update relevant README
6. Commit with descriptive message

## Key Design Principles

- **Modularity**: Each package is self-contained with its own dependencies
- **Fallback**: Systems degrade gracefully — trained models fall back to symbolic engine
- **Colab-First**: Training infrastructure targets Google Colab GPU environment
- **Measure Everything**: All pipelines have latency, response length, and success rate tracking
