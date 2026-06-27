"""NICTO Omega Game Engine — AI-native game creation platform.

Build complete games from natural language descriptions.
Includes UE5-class advanced subsystems: Virtual Geometry (Nanite),
Global Illumination (Lumen), Blueprint Scripting, MetaHuman,
PCG, VFX (Niagara), Chaos Physics, World Partition, Asset Library.
"""

from nicto_game.core.director import GameDirector
from nicto_game.core.config import (
    GameConfig, GameGenre, GamePlatform, GraphicsQuality, RenderMode, Difficulty,
    WorldConfig, GraphicsConfig, GameplayConfig, AssetConfig,
    StoryConfig, AudioConfig, OptimizationConfig,
)
from nicto_game.core.types import TileType, GameMap, CharacterDef, QuestDef, Biome
from nicto_game.world.generator import WorldGenerator
from nicto_game.world.biomes import BiomeGenerator
from nicto_game.characters.generator import CharacterGenerator
from nicto_game.story.engine import StoryEngine
from nicto_game.code.engine import CodeEngine
from nicto_game.audio.engine import AudioEngine
from nicto_game.assets.textures import TextureGenerator, AssetFactory
from nicto_game.testing.engine import TestingEngine
from nicto_game.optimization.engine import OptimizationEngine
from nicto_game.export.engine import ExportEngine
from nicto_game.agents.base import GameAgent, AgentCoordinator
from nicto_game.agents.planner import PlannerAgent, ArchitectAgent, QAAgent
from nicto_game.advanced import (
    NiktoEngine, GameSession, GameState, GamePerformance,
    VirtualGeometryEngine, VirtualMesh,
    GlobalIllumination, LightProbe, LightType,
    BlueprintEngine, BlueprintScript, BlueprintNode, NodeDataType,
    MetaHumanGenerator, MetaHuman, Gender, Ethnicity,
    PCGEngine, PCGContext, PCGRule, PCGSpawnPoint, PCGRegion,
    VFXSystem, ParticleEffect, Particle, SpawnMode, ParticleShape,
    ChaosPhysics, ChaosSolver, PhysObject, FractureChunk, BodyType,
    ShapeType, ConstraintType, FractureGeometry,
    WorldPartition, Chunk, ChunkState, HLOD, StreamingVolume,
    AssetLibrary, Asset, SurfacePreset, AssetPack, AssetType, AssetStyle,
)

__all__ = [
    "GameDirector", "GameConfig", "GameGenre", "GamePlatform",
    "GraphicsQuality", "RenderMode", "Difficulty",
    "WorldConfig", "GraphicsConfig", "GameplayConfig", "AssetConfig",
    "StoryConfig", "AudioConfig", "OptimizationConfig",
    "TileType", "GameMap", "CharacterDef", "QuestDef", "Biome",
    "WorldGenerator", "BiomeGenerator", "CharacterGenerator",
    "StoryEngine", "CodeEngine", "AudioEngine",
    "TextureGenerator", "AssetFactory",
    "TestingEngine", "OptimizationEngine", "ExportEngine",
    "GameAgent", "AgentCoordinator", "PlannerAgent", "ArchitectAgent", "QAAgent",
    "NiktoEngine", "GameSession", "GameState", "GamePerformance",
    "VirtualGeometryEngine", "VirtualMesh",
    "GlobalIllumination", "LightProbe", "LightType",
    "BlueprintEngine", "BlueprintScript", "BlueprintNode", "NodeDataType",
    "MetaHumanGenerator", "MetaHuman", "Gender", "Ethnicity",
    "PCGEngine", "PCGContext", "PCGRule", "PCGSpawnPoint", "PCGRegion",
    "VFXSystem", "ParticleEffect", "Particle", "SpawnMode", "ParticleShape",
    "ChaosPhysics", "ChaosSolver", "PhysObject", "FractureChunk", "BodyType",
    "ShapeType", "ConstraintType", "FractureGeometry",
    "WorldPartition", "Chunk", "ChunkState", "HLOD", "StreamingVolume",
    "AssetLibrary", "Asset", "SurfacePreset", "AssetPack", "AssetType", "AssetStyle",
]
