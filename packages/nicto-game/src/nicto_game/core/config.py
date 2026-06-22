from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class GameGenre(str, Enum):
    FPS = "fps"
    MAZE = "maze"
    DUNGEON = "dungeon"
    OPEN_WORLD = "open_world"
    SURVIVAL = "survival"
    RPG = "rpg"
    PLATFORMER = "platformer"
    RACING = "racing"
    PUZZLE = "puzzle"
    STEALTH = "stealth"
    ROGUELIKE = "roguelike"
    TOWER_DEFENSE = "tower_defense"
    CITY_BUILDER = "city_builder"
    ADVENTURE = "adventure"
    HORROR = "horror"
    SANDBOX = "sandbox"
    STRATEGY = "strategy"
    BEAT_EM_UP = "beat_em_up"
    METROIDVANIA = "metroidvania"


class GamePlatform(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    ANDROID = "android"
    WEB = "web"
    MACOS = "macos"


class GraphicsQuality(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"
    CINEMATIC = "cinematic"


class RenderMode(Enum):
    ASCII = "ascii"
    RAYCAST_2D = "raycast_2d"
    SOFTWARE_3D = "software_3d"
    OPENGL = "opengl"
    VULKAN = "vulkan"


class Difficulty(str, Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXTREME = "extreme"


@dataclass
class WorldConfig:
    width: int = 64
    height: int = 64
    seed: Optional[int] = None
    biomes: bool = True
    rivers: bool = True
    vegetation: bool = True
    buildings: bool = True
    enemies: int = 10
    npcs: int = 5
    roads: bool = True
    caves: bool = False
    villages: int = 0
    water_level: float = 0.15
    mountain_roughness: float = 0.5
    tree_density: float = 0.3


@dataclass
class GraphicsConfig:
    quality: GraphicsQuality = GraphicsQuality.MEDIUM
    render_mode: RenderMode = RenderMode.RAYCAST_2D
    resolution_width: int = 800
    resolution_height: int = 600
    fov: float = 90.0
    vsync: bool = True
    shadows: bool = True
    particles: bool = True
    post_processing: bool = False
    texture_size: int = 256
    anti_aliasing: bool = False
    draw_distance: int = 100


@dataclass
class GameplayConfig:
    health: float = 100.0
    speed: float = 3.0
    jump_height: float = 1.0
    gravity: float = 9.8
    difficulty: Difficulty = Difficulty.NORMAL
    multiplayer: bool = False
    max_players: int = 1
    respawn: bool = True
    friendly_fire: bool = False
    day_night_cycle: bool = False
    hunger: bool = False
    thirst: bool = False


@dataclass
class AssetConfig:
    texture_size: int = 256
    generate_textures: bool = True
    generate_audio: bool = True
    generate_models: bool = True
    audio_sample_rate: int = 44100
    audio_bit_depth: int = 16
    model_detail: float = 0.5


@dataclass
class StoryConfig:
    generate_quests: bool = True
    generate_dialogue: bool = True
    generate_lore: bool = True
    num_quests: int = 5
    num_factions: int = 3
    has_main_quest: bool = True
    lore_depth: str = "medium"


@dataclass
class AudioConfig:
    master_volume: float = 0.8
    music_volume: float = 0.6
    sfx_volume: float = 0.8
    generate_music: bool = True
    generate_sfx: bool = True
    music_style: str = "ambient"


@dataclass
class OptimizationConfig:
    target_fps: int = 60
    enable_culling: bool = True
    enable_lod: bool = True
    chunk_size: int = 16
    streaming_enabled: bool = False
    max_polygons: int = 100000
    compression: str = "fast"


@dataclass
class GameConfig:
    name: str = "NICTO_Game"
    genre: GameGenre = GameGenre.FPS
    platform: GamePlatform = GamePlatform.WINDOWS
    render_mode: RenderMode = RenderMode.RAYCAST_2D
    world: WorldConfig = field(default_factory=WorldConfig)
    graphics: GraphicsConfig = field(default_factory=GraphicsConfig)
    gameplay: GameplayConfig = field(default_factory=GameplayConfig)
    assets: AssetConfig = field(default_factory=AssetConfig)
    story: StoryConfig = field(default_factory=StoryConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    output_dir: str = ""
    description: str = ""
    author: str = "NICTO AI"

    def __post_init__(self):
        if not self.output_dir:
            import os
            self.output_dir = os.path.join(os.path.expanduser("~"), ".nicto", "games")
