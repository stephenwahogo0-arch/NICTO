from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class PlatformAdapter(ABC):
    """Abstract base for platform-specific export adapters."""

    @abstractmethod
    def export(self, code: str, output_dir: str, game_name: str, world_data: dict) -> dict:
        ...
