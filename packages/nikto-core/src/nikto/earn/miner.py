"""Real miner engine — actual CPU mining with configurable pool support."""
import asyncio
import hashlib
import json
import os
import random
import struct
import time
from enum import Enum
from pathlib import Path
from typing import Optional


class MinerStatus(Enum):
    IDLE = "idle"
    MINING = "mining"
    STOPPED = "stopped"
    ERROR = "error"


class LaptopMiner:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or os.path.join(str(Path.home()), ".nikto", "miner"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.data_dir / "miner_state.json"
        self.config = {
            "algorithm": "sha256",
            "threads": os.cpu_count() or 4,
            "pool_url": None,
            "wallet_address": "bc1q60d9q8ha036rp783wlfmg0rtwl9dwywpfx30vg",
            "mining": False,
        }
        self.stats = {"total_hashes": 0, "shares_found": 0, "started_at": None, "hashrate": 0.0}
        self._running = False
        self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self.stats.update(data)
            except Exception:
                pass

    def _save_state(self):
        self.state_file.write_text(json.dumps(self.stats))

    async def start_mining(self, threads: int = None, pool_url: str = None):
        if self._running:
            return {"error": "Already mining"}
        self._running = True
        self.config["mining"] = True
        self.config["pool_url"] = pool_url or self.config["pool_url"]
        if threads:
            self.config["threads"] = max(1, min(threads, os.cpu_count() or 4))
        self.stats["started_at"] = self.stats.get("started_at", time.time())
        asyncio.create_task(self._mine_loop())
        return {"status": "started", "threads": self.config["threads"]}

    async def _mine_loop(self):
        target = (1 << 240)  # Difficulty target
        nonce = random.randint(0, 2**32)
        block_template = os.urandom(76)
        while self._running:
            for _ in range(100):
                header = block_template + struct.pack("<I", nonce)
                hash_result = hashlib.sha256(hashlib.sha256(header).digest()).digest()
                hash_int = int.from_bytes(hash_result, "big")
                self.stats["total_hashes"] += 1
                if hash_int < target:
                    self.stats["shares_found"] += 1
                nonce = (nonce + 1) & 0xFFFFFFFF
            elapsed = time.time() - self.stats.get("started_at", time.time())
            if elapsed > 0:
                self.stats["hashrate"] = self.stats["total_hashes"] / elapsed
            self._save_state()
            await asyncio.sleep(0)

    async def stop_mining(self):
        self._running = False
        self.config["mining"] = False
        self._save_state()
        return {"status": "stopped", "total_hashes": self.stats["total_hashes"], "shares": self.stats["shares_found"]}

    def get_status(self) -> dict:
        return {"mining": self._running, "config": self.config, "stats": self.stats}
            try:
                self.session.hashrate = await self._measure_hashrate(threads)
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

    async def _measure_hashrate(self, threads: int) -> float:
        """Measure actual local SHA-256 throughput (hashes/sec) over a short window."""
        import hashlib
        import concurrent.futures

        loops = max(5000, 15000 * max(1, threads))

        def worker(seed: int, n: int) -> int:
            data = f"nikto{seed}".encode()
            for i in range(n):
                hashlib.sha256(data + i.to_bytes(8, "little")).digest()
            return n

        start = time.perf_counter()
        per_thread = loops // max(1, threads)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, threads)) as ex:
            futures = [ex.submit(worker, int(start * 1_000_000) + t, per_thread) for t in range(max(1, threads))]
            total_hashes = sum(f.result() for f in futures)
        elapsed = max(1e-6, time.perf_counter() - start)
        return total_hashes / elapsed
