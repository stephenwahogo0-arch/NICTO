"""NIKTO Advanced Game Engine — UE5-class subsystems.

Provides virtual geometry (Nanite), global illumination (Lumen),
blueprint scripting, MetaHuman characters, PCG world generation,
VFX systems, chaos physics, world partition streaming, and
Quixel Megascans-style asset management.
"""

from .engine import NiktoEngine, GameSession, GameState, GamePerformance
from .virtual_geometry import VirtualGeometryEngine, VirtualMesh, QuadTreeNode, LODLevel
from .global_illumination import GlobalIlluminationEngine as GlobalIllumination, LightProbe, LightType
from .blueprint_script import BlueprintSystem, BlueprintGraph, BlueprintNode, BlueprintCompiler, PinType
BlueprintEngine = BlueprintSystem
BlueprintScript = BlueprintGraph
NodeDataType = PinType
from .metahuman import MetaHumanGenerator, MetaHuman, Gender, Ethnicity
from .pcg_engine import PCGEngine, PCGContext, PCGRule, PCGSpawnPoint, PCGRegion
from .vfx_system import VFXSystem, ParticleEffect, Particle, SpawnMode, ParticleShape
from .chaos_physics import ChaosPhysics, ChaosSolver, PhysObject, FractureChunk, BodyType, ShapeType, ConstraintType, FractureGeometry
from .world_partition import WorldPartition, Chunk, ChunkState, HLOD, StreamingVolume
from .asset_library import AssetLibrary, Asset, SurfacePreset, AssetPack, AssetType, AssetStyle

__all__ = [
    "NiktoEngine", "GameSession", "GameState", "GamePerformance",
    "VirtualGeometryEngine", "VirtualMesh", "QuadTreeNode", "LODLevel",
    "GlobalIllumination", "LightProbe", "LightType",
    "BlueprintEngine", "BlueprintScript", "BlueprintNode", "BlueprintCompiler", "NodeDataType",
    "MetaHumanGenerator", "MetaHuman", "Gender", "Ethnicity",
    "PCGEngine", "PCGContext", "PCGRule", "PCGSpawnPoint", "PCGRegion",
    "VFXSystem", "ParticleEffect", "Particle", "SpawnMode", "ParticleShape",
    "ChaosPhysics", "ChaosSolver", "PhysObject", "FractureChunk", "BodyType",
    "ShapeType", "ConstraintType", "FractureGeometry",
    "WorldPartition", "Chunk", "ChunkState", "HLOD", "StreamingVolume",
    "AssetLibrary", "Asset", "SurfacePreset", "AssetPack", "AssetType", "AssetStyle",
]
