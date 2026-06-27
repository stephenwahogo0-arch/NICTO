"""AI Game Director — orchestrates the entire AI-native game creation pipeline."""

from __future__ import annotations
import os
import time
import logging
from typing import Any, Optional

from nicto_game.core.config import GameConfig, GameGenre, GamePlatform, RenderMode
from nicto_game.core.types import GameMap
from nicto_game.world.generator import WorldGenerator
from nicto_game.characters.generator import CharacterGenerator
from nicto_game.story.engine import StoryEngine
from nicto_game.code.engine import CodeEngine
from nicto_game.audio.engine import AudioEngine
from nicto_game.assets.textures import AssetFactory
from nicto_game.testing.engine import TestingEngine
from nicto_game.optimization.engine import OptimizationEngine
from nicto_game.export.engine import ExportEngine
from nicto_game.agents.base import AgentCoordinator
from nicto_game.agents.planner import PlannerAgent, ArchitectAgent, QAAgent
from nicto_game.advanced import (
    NiktoEngine, GameState, AssetType, BodyType, ShapeType,
    PCGRegion, SpawnMode,
)

logger = logging.getLogger("nicto.game")


class GameDirector:
    """AI Game Director — orchestrates all subsystems through an AI-native pipeline."""

    def __init__(self, config: Optional[GameConfig] = None):
        self.config = config or GameConfig()
        self.world_gen = WorldGenerator()
        self.char_gen = CharacterGenerator()
        self.story_engine = StoryEngine()
        self.code_engine = CodeEngine()
        self.audio_engine = AudioEngine()
        self.asset_factory = AssetFactory()
        self.testing = TestingEngine()
        self.optimization = OptimizationEngine()
        self.export = ExportEngine()
        self.coordinator = AgentCoordinator()
        self.nikto_engine = NiktoEngine()
        self._games_built = 0
        self._build_history: list[dict[str, Any]] = []

        self.coordinator.register(PlannerAgent())
        self.coordinator.register(ArchitectAgent())
        self.coordinator.register(QAAgent())

    async def design_game(self, prompt: str) -> GameConfig:
        """Use AI agents to interpret a prompt into a full GameConfig."""
        prompt_lower = prompt.lower()
        cfg = GameConfig(description=prompt)

        # Genre detection
        genre_map = {
            "fps": GameGenre.FPS, "shooter": GameGenre.FPS, "doom": GameGenre.FPS,
            "maze": GameGenre.MAZE, "labyrinth": GameGenre.MAZE,
            "dungeon": GameGenre.DUNGEON, "rpg dungeon": GameGenre.DUNGEON,
            "open world": GameGenre.OPEN_WORLD, "sandbox": GameGenre.SANDBOX,
            "survival": GameGenre.SURVIVAL, "craft": GameGenre.SURVIVAL,
            "rpg": GameGenre.RPG, "rpg game": GameGenre.RPG, "adventure": GameGenre.ADVENTURE,
            "platformer": GameGenre.PLATFORMER, "platform": GameGenre.PLATFORMER,
            "racing": GameGenre.RACING, "car": GameGenre.RACING,
            "puzzle": GameGenre.PUZZLE, "horror": GameGenre.HORROR,
            "stealth": GameGenre.STEALTH, "sneak": GameGenre.STEALTH,
            "roguelike": GameGenre.ROGUELIKE, "rogue": GameGenre.ROGUELIKE,
            "tower defense": GameGenre.TOWER_DEFENSE, "td": GameGenre.TOWER_DEFENSE,
            "city builder": GameGenre.CITY_BUILDER, "city": GameGenre.CITY_BUILDER,
        }
        for keyword, genre in genre_map.items():
            if keyword in prompt_lower:
                cfg.genre = genre
                break

        # Size detection
        if "tiny" in prompt_lower or "small" in prompt_lower:
            cfg.world.width, cfg.world.height = 16, 16
            cfg.world.enemies = 3
        elif "large" in prompt_lower or "huge" in prompt_lower or "open" in prompt_lower:
            cfg.world.width, cfg.world.height = 128, 128
            cfg.world.enemies = 25
        elif "epic" in prompt_lower or "massive" in prompt_lower:
            cfg.world.width, cfg.world.height = 256, 256
            cfg.world.enemies = 50

        # Feature detection
        if "multiplayer" in prompt_lower or "multi-player" in prompt_lower or "co-op" in prompt_lower:
            cfg.gameplay.multiplayer = True
            cfg.gameplay.max_players = 4
        if "realistic" in prompt_lower or "cinematic" in prompt_lower:
            cfg.graphics.quality = cfg.graphics.quality.__class__.CINEMATIC
        if "pbr" in prompt_lower or "physically based" in prompt_lower:
            cfg.render_mode = RenderMode.OPENGL
        if "no enemies" in prompt_lower or "peaceful" in prompt_lower or "creative" in prompt_lower:
            cfg.world.enemies = 0
        if "many enemies" in prompt_lower or "horde" in prompt_lower:
            cfg.world.enemies = max(cfg.world.enemies, 30)
        if "story" in prompt_lower or "quest" in prompt_lower:
            cfg.story.generate_quests = True
            cfg.story.num_quests = 5
        if "survival" in prompt_lower:
            cfg.gameplay.hunger = True
            cfg.gameplay.thirst = True
            cfg.gameplay.day_night_cycle = True

        # Extract name from prompt
        words = [w.capitalize() for w in prompt_lower.split()
                 if len(w) > 3 and w not in ("with", "that", "this", "from", "very", "many", "realistic")]
        cfg.name = "NICTO_" + ("_".join(words[:3]) if words else "Adventure")

        # Run planner agent
        await self.coordinator.execute_pipeline(cfg)
        return cfg

    async def build_game(self, config: Optional[GameConfig] = None) -> dict[str, Any]:
        """Full AI-native pipeline: plan -> world -> characters -> story -> code -> assets -> test -> optimize -> export."""
        cfg = config or self.config
        start = time.time()
        result: dict[str, Any] = {"name": cfg.name, "genre": cfg.genre.value}

        try:
            game_map = await self.world_gen.generate(cfg)
            result["world_size"] = f"{game_map.width}x{game_map.height}"
        except Exception as e:
            logger.error(f"World generation failed: {e}")
            game_map = GameMap(width=max(cfg.world.width, 8), height=max(cfg.world.height, 8),
                               tiles=[[0] * max(cfg.world.width, 8) for _ in range(max(cfg.world.height, 8))])

        try:
            characters = await self.char_gen.generate(cfg)
            result["characters"] = len(characters)
        except Exception as e:
            logger.warning(f"Character generation failed: {e}")
            characters = []

        try:
            story_data = await self.story_engine.generate(cfg)
            result["quests"] = len(story_data.get("quests", []))
        except Exception as e:
            logger.warning(f"Story generation failed: {e}")
            story_data = {}

        try:
            source_code = await self.code_engine.generate(cfg, game_map, characters,
                                                          story_data.get("quests"))
            result["lines_of_code"] = len(source_code.splitlines())
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            source_code = self._fallback_game_template(cfg)

        audio_assets = {}
        try:
            output_dir = os.path.join(cfg.output_dir, cfg.name)
            audio_assets = await self.audio_engine.generate(cfg, output_dir)
            result["audio_assets"] = len(audio_assets)
        except Exception as e:
            logger.warning(f"Audio generation failed: {e}")

        try:
            textures = await self.asset_factory.generate_all(output_dir, cfg.assets.texture_size)
            result["textures"] = len(textures.get("textures", []))
        except Exception as e:
            logger.warning(f"Asset generation failed: {e}")

        try:
            test_result = await self.testing.validate_game(source_code, cfg)
            result["test_score"] = test_result.get("score", 0)
            result["test_issues"] = len(test_result.get("potential_issues", []))
        except Exception as e:
            logger.warning(f"Testing failed: {e}")

        try:
            opt_result = await self.optimization.analyze(source_code, cfg)
            result["opt_quality"] = opt_result.get("quality", {}).get("grade", "N/A")
            result["opt_fps"] = opt_result.get("estimated_fps", 60)
        except Exception as e:
            logger.warning(f"Optimization analysis failed: {e}")

        try:
            export_result = await self.export.export(cfg, source_code, game_map)
            result["export_path"] = export_result.get("file_path", "")
        except Exception as e:
            logger.error(f"Export failed: {e}")

        result["build_time"] = round(time.time() - start, 1)
        self._games_built += 1
        self._build_history.append(result)
        return result

    def build_advanced_world(self, name: str = "AdvancedGame", seed: int = 0) -> dict:
        """Build an advanced UE5-class world using NiktoEngine subsystems."""
        self.nikto_engine.initialize()
        session = self.nikto_engine.new_game(name=name, seed=seed)
        self.nikto_engine.spawn_character("Hero")
        for i in range(3):
            self.nikto_engine.spawn_character(f"NPC_{i}")
        dungeon = self.nikto_engine.generate_dungeon(rooms=8)
        return {
            "name": session.name,
            "state": session.state.value,
            "subsystems": list(self.nikto_engine._subsystems.keys()),
            "dungeon_rooms": len(dungeon),
            "world_chunks": self.nikto_engine.world_partition.get_stats()["total_chunks"],
            "assets_loaded": self.nikto_engine.asset_library.get_stats()["total_assets"],
            "physics_bodies": len(self.nikto_engine.chaos_physics.solver.bodies),
        }

    async def build_from_prompt(self, prompt: str) -> dict[str, Any]:
        """Design + build from a single natural language prompt."""
        cfg = await self.design_game(prompt)
        self.config = cfg
        return await self.build_game(cfg)

    def get_status(self) -> dict[str, Any]:
        return {
            "games_built": self._games_built,
            "last_build": self._build_history[-1] if self._build_history else None,
            "build_history": len(self._build_history),
            "agents_registered": list(self.coordinator.agents.keys()),
        }

    def _fallback_game_template(self, cfg: GameConfig) -> str:
        return f'''
import pygame, sys, math, random
pygame.init()
W, H = 640, 480
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT: running = False
    screen.fill((20, 20, 30))
    pygame.display.flip()
    clock.tick(30)
pygame.quit()
print("{cfg.name} — built by NICTO Omega Game Engine")
'''
