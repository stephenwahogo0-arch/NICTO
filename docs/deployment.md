# NICTO Deployment Guide

## Deployment Options

### 1. Local Development Server

```bash
# Start unified API server
python packages/nikto-core/src/nikto/run_all.py --no-auth
# → http://127.0.0.1:5000
# → All 4 models available via X-Model-Id header
```

### 2. Docker Deployment

```bash
# Build and run all services
docker-compose up -d --build

# Verify
curl http://localhost:5000/health
```

### 3. Production Deployment

**Requirements:**
- Linux server (Ubuntu 22.04+)
- 8GB+ RAM
- GPU optional (CPU fallback available)
- Nginx reverse proxy (recommended)

```bash
# Using systemd service
sudo cp deployment/nikto.service /etc/systemd/system/
sudo systemctl enable nikto
sudo systemctl start nikto
```

### 4. Desktop App

```bash
cd packages/nikto-desktop

# Development
npm run dev

# Production build (requires 16GB+ RAM for Rust)
npm run tauri build
# → packages/nikto-desktop/src-tauri/target/release/Nikto.exe
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System status, active model |
| `/models` | GET | Available models with capabilities |
| `/chat` | POST | Chat completion (send `X-Model-Id`) |
| `/chat/stream` | POST | Streaming chat completion |
| `/metrics` | GET | Performance metrics |
| `/feedback` | POST | Submit feedback |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NIKTO_PORT` | 5000 | API server port |
| `NIKTO_HOST` | 127.0.0.1 | Bind address |
| `NIKTO_AUTH` | true | Require API key |
| `NIKTO_STATE_PATH` | ~/.nikto/ | Brain state directory |

## Monitoring

- Health endpoint: `/health`
- Metrics: `/metrics` (latency, request count, brain status)
- Training data generation metrics tracked automatically
