from __future__ import annotations
import os
from nicto_game.export.adapters.base import PlatformAdapter


class WindowsAdapter(PlatformAdapter):
    """Exports game as a standalone Python script for Windows."""

    def export(self, code: str, output_dir: str, game_name: str, world_data: dict) -> dict:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{game_name}.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        bat_path = os.path.join(output_dir, f"run_{game_name}.bat")
        with open(bat_path, "w") as f:
            f.write(f'@echo off\npython "{game_name}.py"\npause\n')
        return {"file_path": file_path, "bat_path": bat_path, "platform": "windows"}
