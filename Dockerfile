FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git build-essential \
    nmap sqlmap nikto dirb wpscan hashcat hydra \
    && rm -rf /var/lib/apt/lists/*

ENV UV_PYTHON=/usr/local/bin/python3.12
ENV PATH="/root/.local/bin:${PATH}"

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

COPY pyproject.toml .
COPY packages/nikto-core/pyproject.toml packages/nikto-core/
COPY packages/nikto-cli/pyproject.toml packages/nikto-cli/

RUN uv sync --frozen --no-dev

COPY packages/nikto-core/src packages/nikto-core/src/
COPY packages/nikto-cli/src packages/nikto-cli/src/

RUN uv sync --frozen --no-dev

RUN uv pip install --system playwright && python -m playwright install chromium

EXPOSE 4890

ENTRYPOINT ["nikto"]
CMD ["daemon"]
