import asyncio
import logging
import os
import signal
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DaemonConfig:
    host: str = "127.0.0.1"
    port: int = 4890
    api_workers: int = 4
    log_level: str = "INFO"
    pid_file: str = str(Path.home() / ".nikto" / "daemon.pid")
    auto_start_miner: bool = False
    auto_start_orchestrator: bool = True


class NiktoDaemon:
    def __init__(self, config: Optional[DaemonConfig] = None):
        self.config = config or DaemonConfig()
        self._server: Optional[asyncio.AbstractServer] = None
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        self._running = True
        self._write_pid()

        from nikto.orchestrator.engine import Orchestrator, OrchestratorConfig, Budget
        self.orchestrator = Orchestrator(OrchestratorConfig(budget=Budget(total=5000.0)))
        await self.orchestrator.run()
        logger.info("Orchestrator started in daemon")

        if self.config.auto_start_miner:
            from nikto.earn.miner import LaptopMiner
            self.miner = LaptopMiner()
            await self.miner.start()
            logger.info("Miner auto-started in daemon")

        app = await self._build_app()
        runner = asyncio.create_task(self._run_api(app))
        self._tasks.append(runner)
        logger.info(f"Nikto daemon listening on {self.config.host}:{self.config.port}")
        return {"status": "started", "pid": os.getpid()}

    async def stop(self):
        self._running = False
        if self._server:
            self._server.close()
        if hasattr(self, "orchestrator"):
            await self.orchestrator.stop()
        if hasattr(self, "miner"):
            await self.miner.stop()
        for t in self._tasks:
            t.cancel()
        self._remove_pid()
        logger.info("Nikto daemon stopped")

    async def _build_app(self):
        from fastapi import FastAPI
        app = FastAPI(title="Nikto API", version="0.1.0")

        @app.get("/health")
        async def health():
            return {"status": "ok", "pid": os.getpid()}

        @app.get("/status")
        async def status():
            orch = self.orchestrator.status()
            miner_stats = {}
            if hasattr(self, "miner"):
                miner_stats = await self.miner.stats()
            return {"orchestrator": orch, "miner": miner_stats}

        return app

    async def _run_api(self, app):
        import uvicorn
        cfg = uvicorn.Config(app, host=self.config.host, port=self.config.port, log_level=self.config.log_level.lower())
        server = uvicorn.Server(cfg)
        self._server = server
        await server.serve()

    def _write_pid(self):
        Path(self.config.pid_file).parent.mkdir(parents=True, exist_ok=True)
        Path(self.config.pid_file).write_text(str(os.getpid()))

    def _remove_pid(self):
        pf = Path(self.config.pid_file)
        if pf.exists():
            pf.unlink()
