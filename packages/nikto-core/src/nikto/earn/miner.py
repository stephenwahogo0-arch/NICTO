import time
import hashlib
import threading
from uuid import uuid4


class MinerConfig:
    def __init__(self, threads: int = 2, difficulty: int = 4):
        self.threads = threads
        self.difficulty = difficulty


class LaptopMiner:
    def __init__(self, config: MinerConfig = None):
        self.config = config or MinerConfig()
        self.miner_id = str(uuid4())[:12]
        self._running = False
        self._thread = None
        self._hash_count = 0
        self._start_time = None

    def _mine_loop(self):
        target = "0" * self.config.difficulty
        nonce = 0
        data = f"nikto-block-{self.miner_id}"
        while self._running:
            h = hashlib.sha256(f"{data}{nonce}".encode()).hexdigest()
            self._hash_count += 1
            if h.startswith(target):
                pass
            nonce += 1

    def start(self) -> dict:
        if self._running:
            return {"success": False, "error": "Already running"}
        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._mine_loop, daemon=True)
        self._thread.start()
        return {"success": True, "miner_id": self.miner_id, "status": "started"}

    def stop(self) -> dict:
        self._running = False
        return {"success": True, "miner_id": self.miner_id, "status": "stopped"}

    def stats(self) -> dict:
        return {"status": "running" if self._running else "stopped", "miner_id": self.miner_id, "hash_count": self._hash_count, "uptime": time.time() - self._start_time if self._start_time else 0}
