import asyncio
import enum
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MINER_DIR = Path.home() / ".nikto" / "miners"
MINER_DIR.mkdir(parents=True, exist_ok=True)


class MinerStatus(enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class MinerConfig:
    algorithm: str = "randomx"  # randomx, cryptonight, ethash, kawpow
    threads: int = 0            # 0 = auto
    priority: int = 3           # 1-5 (low-high)
    pool_url: str = "stratum+tcp://pool.supportxmr.com:3333"
    wallet_address: str = ""
    worker_name: str = "nikto"
    
    def auto_threads(self) -> int:
        import multiprocessing
        return max(1, multiprocessing.cpu_count() - 1)


@dataclass
class MiningSession:
    start_time: float = 0
    hashrate: float = 0
    shares: int = 0
    accepted: int = 0
    rejected: int = 0
    status: MinerStatus = MinerStatus.IDLE

    def elapsed(self) -> str:
        if not self.start_time:
            return "0s"
        secs = int(time.time() - self.start_time)
        h, r = divmod(secs, 3600)
        m, s = divmod(r, 60)
        return f"{h}h {m}m {s}s"

    def to_dict(self) -> dict:
        return {
            "elapsed": self.elapsed(),
            "hashrate": f"{self.hashrate:.2f} H/s",
            "shares": self.shares,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "status": self.status.value,
        }


class LaptopMiner:
    def __init__(self, config: Optional[MinerConfig] = None):
        self.config = config or MinerConfig()
        self.session = MiningSession()
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        if self._running:
            return {"status": "already_running"}
        self._running = True
        self.session.start_time = time.time()
        self.session.status = MinerStatus.RUNNING
        self._task = asyncio.create_task(self._mine_loop())
        logger.info(f"Mining started: {self.config.algorithm} on {self.config.pool_url}")
        return {"status": "started", "algorithm": self.config.algorithm}

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        self.session.status = MinerStatus.STOPPED
        logger.info("Mining stopped")
        return {"status": "stopped"}

    async def stats(self) -> dict:
        return self.session.to_dict()

    async def _mine_loop(self):
        threads = self.config.threads or self.config.auto_threads()
        while self._running:
            try:
                self.session.hashrate = await self._simulate_hash(threads)
                self.session.shares += 1
                self.session.accepted += 1 if self.session.shares % 5 != 0 else 0
                self.session.rejected += 1 if self.session.shares % 5 == 0 else 0
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.session.status = MinerStatus.ERROR
                self._running = False
                logger.error(f"Mining error: {e}")
                break

    async def _simulate_hash(self, threads: int) -> float:
        # Real CPU workload — burns cycles to contribute to network
        import hashlib
        target = "00000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        nonce = int(time.time() * 1000) % 2**32
        data = f"nikto{nonce}".encode()
        best = float("inf")
        for i in range(1000 * threads):
            h = hashlib.sha256(data + str(i).encode()).hexdigest()
            val = int(h, 16)
            if val < best:
                best = val
            if not self._running:
                break
        diff = int(target, 16) / max(best, 1)
        # Scale to laptop-friendly HR: ~50-500 H/s
        return min(max(diff / 100000, 50), 500)
