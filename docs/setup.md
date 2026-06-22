# NICTO Setup Guide

## Prerequisites

- Python 3.10+
- Node.js 18+ (for desktop app)
- Rust toolchain (for Tauri desktop build, optional)
- 8GB+ RAM (16GB+ for Tauri build)
- GPU recommended for training (T4/V100/A100)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/stephenwahogo0-arch/NICTO.git
cd NICTO
```

### 2. Python Dependencies

```bash
pip install -e .
pip install -e packages/nikto-core
pip install -e packages/nicto-x
pip install -e packages/nicto-game
```

### 3. Desktop App Dependencies

```bash
cd packages/nikto-desktop
npm install
```

### 4. Configuration

```bash
# Auto-detect hardware and configure
python nicto_neural/setup_real_ai.py
```

## Running

### API Server

```bash
# Start unified server (handles all 4 models: Kyros/Omega/Main/X)
python packages/nikto-core/src/nikto/run_all.py --no-auth
```

### Desktop App

```bash
cd packages/nikto-desktop
npm run dev
```

### CLI

```bash
python nikto_cli/main.py chat
python nikto_cli/main.py status
python nikto_cli/main.py game build "RPG with quests"
```

## Training on Colab

1. Open `colab_nicto_training.ipynb` in Google Colab
2. Select GPU runtime (Runtime → Change runtime type)
3. Run all cells
4. Download trained GGUF models from Google Drive

## Verification

```bash
# Run NICTO X test suite
python packages/nicto-x/tests/test_all.py

# Run multi-model benchmark
python scripts/train_and_verify_all_models.py
```
