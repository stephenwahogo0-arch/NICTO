#!/usr/bin/env bash
set -euo pipefail

echo "==> Nikto Developer Setup"

if ! command -v uv &>/dev/null; then
    echo "--> Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | bash
    export PATH="${HOME}/.local/bin:${PATH}"
fi

if ! command -v node &>/dev/null; then
    echo "ERROR: Node.js required. Install from https://nodejs.org"
    exit 1
fi

if ! command -v pnpm &>/dev/null; then
    echo "--> Installing pnpm..."
    npm install -g pnpm
fi

echo "--> Python setup..."
uv venv
source .venv/bin/activate
uv sync
uv pip install -e packages/kyros-core
uv pip install -e packages/kyros-cli

echo "--> Web UI setup..."
cd packages/nikto-web
pnpm install
cd ../..

echo "--> Installing Playwright browsers..."
uv run python -m playwright install chromium 2>/dev/null || true

echo "==> Setup complete!"
echo "    Run: uv run nikto"
echo "    Web: cd packages/nikto-web && pnpm dev"
