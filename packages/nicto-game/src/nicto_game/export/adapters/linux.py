from __future__ import annotations
import os
from nicto_game.export.adapters.base import PlatformAdapter


class LinuxAdapter(PlatformAdapter):
    """Exports game as a standalone Python script for Linux."""

    def export(self, code: str, output_dir: str, game_name: str, world_data: dict) -> dict:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{game_name}.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        sh_path = os.path.join(output_dir, f"run_{game_name}.sh")
        with open(sh_path, "w") as f:
            f.write(f'#!/bin/bash\npython3 "{game_name}.py"\n')
        os.chmod(sh_path, 0o755)
        return {"file_path": file_path, "sh_path": sh_path, "platform": "linux"}
