"""Multi-platform game export engine with bundling support."""

from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Any, Optional

from nicto_game.core.config import GameConfig, GamePlatform
from nicto_game.core.types import GameMap
from nicto_game.export.adapters.base import PlatformAdapter
from nicto_game.export.adapters.windows import WindowsAdapter
from nicto_game.export.adapters.linux import LinuxAdapter
from nicto_game.export.adapters.android import AndroidAdapter
from nicto_game.export.adapters.web import WebAdapter

logger = logging.getLogger("nicto.game.export")


class ExportEngine:
    """Multi-platform game export with adapter pattern and bundling."""

    def __init__(self):
        self._adapters: dict[GamePlatform, PlatformAdapter] = {
            GamePlatform.WINDOWS: WindowsAdapter(),
            GamePlatform.LINUX: LinuxAdapter(),
            GamePlatform.ANDROID: AndroidAdapter(),
            GamePlatform.WEB: WebAdapter(),
        }
        self._exports: list[dict[str, Any]] = []

    def register_adapter(self, platform: GamePlatform, adapter: PlatformAdapter):
        self._adapters[platform] = adapter

    async def export(self, config: GameConfig, code: str, world_data: Any = None) -> dict[str, Any]:
        output_dir = Path(config.output_dir) / config.name
        output_dir.mkdir(parents=True, exist_ok=True)

        adapter = self._adapters.get(config.platform)
        if not adapter:
            adapter = self._adapters[GamePlatform.WINDOWS]
            logger.warning(f"No adapter for {config.platform}, falling back to Windows")

        result = adapter.export(code, str(output_dir), config.name, world_data)

        export_record = {
            "game_name": config.name,
            "platform": config.platform.value,
            "output_dir": str(output_dir),
            "timestamp": __import__("time").time(),
            **result,
        }
        self._exports.append(export_record)
        return export_record

    async def export_all_platforms(self, config: GameConfig, code: str,
                                   world_data: Any = None) -> dict[str, dict[str, Any]]:
        results = {}
        original_platform = config.platform
        for platform, adapter in self._adapters.items():
            if adapter:
                config.platform = platform
                try:
                    result = await self.export(config, code, world_data)
                    results[platform.value] = result
                except Exception as e:
                    logger.error(f"Export to {platform.value} failed: {e}")
        config.platform = original_platform
        return results

    def list_exports(self) -> list[dict[str, Any]]:
        return list(self._exports)

    def get_available_platforms(self) -> list[str]:
        return [p.value for p, a in self._adapters.items() if a]
