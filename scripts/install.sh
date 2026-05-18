#!/usr/bin/env bash
set -euo pipefail

NIKTO_DIR="${HOME}/.nikto"
REPO="https://github.com/${GITHUB_USER:-user}/nikto.git"
PYTHON="${PYTHON:-python3}"

echo "==> Installing Nikto..."

if ! command -v uv &>/dev/null; then
    echo "--> Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | bash
    export PATH="${HOME}/.local/bin:${PATH}"
fi

if [ ! -d "${NIKTO_DIR}/src" ]; then
    echo "--> Cloning Nikto..."
    git clone "${REPO}" "${NIKTO_DIR}"
fi

cd "${NIKTO_DIR}"
uv sync --frozen
uv pip install --system playwright 2>/dev/null || true
python -m playwright install chromium 2>/dev/null || true

echo "--> Installing nikto CLI..."
uv pip install --system -e packages/nikto-core
uv pip install --system -e packages/nikto-cli

echo "==> Nikto installed successfully!"
echo "    Run: nikto --help"
