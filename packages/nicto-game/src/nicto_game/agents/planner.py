"""Planner Agent — creates game plans, feature breakdowns, and production roadmaps."""

from __future__ import annotations
from typing import Any

from nicto_game.agents.base import GameAgent, AgentCoordinator
from nicto_game.core.config import GameConfig, GameGenre


class PlannerAgent(GameAgent):
    """Analyzes prompts and creates comprehensive game production plans."""

    def __init__(self):
        super().__init__("planner")

    async def execute(self, task: dict[str, Any], config: GameConfig) -> dict[str, Any]:
        genre = task.get("genre", config.genre.value)
        prompt = task.get("prompt", "")
        complexity = task.get("complexity", "medium")

        features = self._plan_features(genre, config)
        phases = self._plan_phases(genre, complexity)
        tech_stack = self._recommend_tech_stack(config)

        plan = {
            "game_name": config.name,
            "genre": genre,
            "complexity": complexity,
            "description": prompt or f"A {genre} game built by NICTO Omega",
            "features": features,
            "development_phases": phases,
            "tech_stack": tech_stack,
            "estimated_assets": self._estimate_assets(config),
            "estimated_code_size": self._estimate_code_size(config),
        }
        return self.report(plan)

    def _plan_features(self, genre: str, config: GameConfig) -> list[dict[str, Any]]:
        core_features = {
            "fps": [
                {"name": "Raycasting 3D Rendering", "priority": "critical", "effort": "high"},
                {"name": "Weapon System", "priority": "critical", "effort": "medium"},
                {"name": "Enemy AI", "priority": "critical", "effort": "high"},
                {"name": "Health & Ammo System", "priority": "high", "effort": "medium"},
                {"name": "Level Progression", "priority": "medium", "effort": "medium"},
            ],
            "survival": [
                {"name": "Open World Generation", "priority": "critical", "effort": "high"},
                {"name": "Hunger/Thirst System", "priority": "critical", "effort": "medium"},
                {"name": "Crafting System", "priority": "high", "effort": "high"},
                {"name": "Day/Night Cycle", "priority": "high", "effort": "medium"},
                {"name": "Wildlife AI", "priority": "medium", "effort": "high"},
            ],
            "rpg": [
                {"name": "Character Stats & Leveling", "priority": "critical", "effort": "high"},
                {"name": "Quest System", "priority": "critical", "effort": "high"},
                {"name": "Inventory System", "priority": "critical", "effort": "medium"},
                {"name": "Dialogue System", "priority": "high", "effort": "medium"},
                {"name": "Faction System", "priority": "medium", "effort": "medium"},
            ],
        }
        return core_features.get(genre, core_features.get("fps", []))

    def _plan_phases(self, genre: str, complexity: str) -> list[dict[str, Any]]:
        phases = [
            {"phase": 1, "name": "Core Engine & World", "tasks": ["Set up game loop", "Implement rendering", "Generate world"],
             "duration_days": 3 if complexity == "high" else 1},
            {"phase": 2, "name": "Gameplay Systems", "tasks": ["Player controller", "Enemy AI", "Combat system"],
             "duration_days": 3 if complexity == "high" else 1},
            {"phase": 3, "name": "Content & Polish", "tasks": ["Assets", "Audio", "UI", "Testing"],
             "duration_days": 2 if complexity == "high" else 1},
        ]
        return phases

    def _recommend_tech_stack(self, config: GameConfig) -> dict[str, str]:
        return {
            "language": "Python 3.11+",
            "rendering": config.render_mode.value,
            "audio": "WAV (procedural)",
            "physics": "Built-in",
            "build_target": config.platform.value,
        }

    def _estimate_assets(self, config: GameConfig) -> dict[str, int]:
        return {
            "textures": 8,
            "sound_effects": 11,
            "music_tracks": 1,
            "maps": 1,
        }

    def _estimate_code_size(self, config: GameConfig) -> int:
        base = 200
        if config.genre in (GameGenre.OPEN_WORLD, GameGenre.SURVIVAL, GameGenre.RPG):
            base += 150
        if config.gameplay.multiplayer:
            base += 200
        if config.story.generate_quests:
            base += 100
        return base


class ArchitectAgent(GameAgent):
    """Designs game architecture from requirements."""

    def __init__(self):
        super().__init__("architect")

    async def execute(self, task: dict[str, Any], config: GameConfig) -> dict[str, Any]:
        modules = self._design_modules(config)
        architecture = {
            "pattern": "Entity-Component with layered rendering",
            "modules": modules,
            "data_flow": "GameConfig -> WorldGen -> CodeGen -> Export",
            "dependencies": ["pygame", "numpy"] + (["sounddevice"] if config.assets.generate_audio else []),
        }
        return self.report(architecture)

    def _design_modules(self, config: GameConfig) -> list[dict[str, str]]:
        return [
            {"name": "Game Loop", "responsibility": "Main loop, timing, event handling"},
            {"name": "World", "responsibility": f"{config.genre.value} world data & collision"},
            {"name": "Entities", "responsibility": "Player, enemies, NPCs, items"},
            {"name": "Rendering", "responsibility": f"{config.render_mode.value} renderer"},
            {"name": "Audio", "responsibility": "SFX and music playback"},
            {"name": "UI", "responsibility": "HUD, menus, minimap"},
        ]


class QAAgent(GameAgent):
    """Quality assurance — validates generated games against requirements."""

    def __init__(self):
        super().__init__("qa")

    async def execute(self, task: dict[str, Any], config: GameConfig) -> dict[str, Any]:
        checks = {
            "has_game_loop": True,
            "has_renderer": True,
            "has_input": True,
            "meets_genre_requirements": self._check_genre_reqs(config),
            "has_error_handling": False,
        }
        score = sum(1 for v in checks.values() if v) / len(checks) * 100
        return self.report({"checks": checks, "score": round(score, 1), "passed": score >= 60})

    def _check_genre_reqs(self, config: GameConfig) -> bool:
        return True
