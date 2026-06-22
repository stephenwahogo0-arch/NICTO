"""
Laptop Miner for NIKTO.

CPU-only mining simulation.  The wallet address MUST come from config
(NiktoConfig.crypto.wallet) — never hardcoded.  Logs a clear warning
until a real pool_url is configured.
"""

import asyncio
import logging
import time
from typing import Any, Optional

from nikto.config.settings import NiktoConfig

logger = logging.getLogger("nikto.miner")


class MinerConfig:
    """Configuration for the laptop miner."""

    def __init__(
        self,
        algorithm: str = "randomx",
        threads: int = 1,
        pool_url: str = "",
        wallet_address: str = "",
    ) -> None:
        self.algorithm = algorithm
        self.threads = threads
        self.pool_url = pool_url
        self.wallet_address = wallet_address


class LaptopMiner:
    """CPU-only mining simulation.

    No real earnings occur unless a real ``pool_url`` is configured.
    """

    def __init__(self, config: Optional[MinerConfig] = None) -> None:
        self.config = config or MinerConfig()
        self._running = False
        self._hashes: int = 0
        self._start_time: float = 0.0
        self._load_wallet()

    def _load_wallet(self) -> None:
        """Load wallet address from config; never hardcode."""
        if not self.config.wallet_address:
            try:
                cfg = NiktoConfig()
                # Try to find wallet address in config
                crypto_wallet = getattr(cfg, "crypto", None)
                if crypto_wallet:
                    self.config.wallet_address = getattr(crypto_wallet, "wallet", "") or ""
            except Exception:
                pass

        if not self.config.wallet_address:
            logger.warning(
                "No wallet address configured. Mining will not produce real earnings."
            )

        if not self.config.pool_url:
            logger.warning(
                "Mining is CPU-only simulation. No pool connected. No real earnings."
            )

    async def start(self) -> None:
        """Start the mining loop."""
        self._running = True
        self._start_time = time.time()
        logger.info("Miner started (simulation mode)")

    async def stats(self) -> dict[str, Any]:
        """Return current mining statistics."""
        elapsed = max(1, time.time() - self._start_time)
        hashrate = self._hashes / elapsed
        return {
            "status": "running" if self._running else "stopped",
            "algorithm": self.config.algorithm,
            "threads": self.config.threads,
            "hashrate_hps": round(hashrate, 2),
            "total_hashes": self._hashes,
            "uptime_seconds": round(elapsed),
            "pool_url": self.config.pool_url or "none (simulation)",
            "wallet_address": self.config.wallet_address or "not set",
        }

    async def stop(self) -> dict[str, Any]:
        """Stop the miner."""
        self._running = False
        return await self.stats()
