# Deployment

Deployment configurations for NICTO AI system.

## Deployment Options

### 1. Local Development

```bash
# Start API server
python packages/nikto-core/src/nikto/run_all.py --no-auth

# Start desktop app
cd packages/nikto-desktop && npm run dev
```

### 2. Docker

```bash
docker-compose up -d
```

### 3. Production

| Component | Port | Description |
|-----------|------|-------------|
| Nikto API Server | 5000 | Brain + 4-model routing |
| Nicto X Server | 8000 | Frontier agent system |

### 4. Desktop (Tauri)

```bash
cd packages/nikto-desktop
npm install
npm run tauri build
```
*Requires 16GB+ RAM for Rust compilation*

### 5. Colab Training

Upload `colab_nicto_training.ipynb` to Google Colab with GPU runtime.

## Configuration

- `pyproject.toml` — Python project configuration
- `docker-compose.yml` — Multi-service deployment
- `Dockerfile` — Container build
- `.gitignore` — File exclusion rules
