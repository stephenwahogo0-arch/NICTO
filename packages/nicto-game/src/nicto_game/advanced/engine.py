"""NIKTO Advanced Game Engine Director.

Orchestrates all UE5-class subsystems:
- Virtual Geometry (Nanite)
- Global Illumination (Lumen)
- Blueprint Scripting
- MetaHuman characters
- PCG world generation
- VFX / particle effects
- Chaos Physics
- World Partition streaming
- Asset Library (Megascans)

Provides a unified API for game creation and real-time control.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from .virtual_geometry import VirtualGeometryEngine
from .global_illumination import GlobalIlluminationEngine as GlobalIllumination, LightProbe
from .blueprint_script import BlueprintSystem, BlueprintNode
BlueprintEngine = BlueprintSystem
from .metahuman import MetaHumanGenerator
from .pcg_engine import PCGEngine, PCGContext
from .vfx_system import VFXSystem, ParticleEffect
from .chaos_physics import ChaosPhysics, PhysObject, BodyType, ShapeType
from .world_partition import WorldPartition, Chunk
from .asset_library import AssetLibrary, Asset, AssetType


class GameState(Enum):
    EDITOR = "editor"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class GamePerformance:
    fps: float = 60.0
    frame_time_ms: float = 16.67
    draw_calls: int = 0
    triangles_rendered: int = 0
    memory_mb: float = 0.0
    streaming_chunks: int = 0
    particle_count: int = 0
    physics_bodies: int = 0

    def to_dict(self) -> dict:
        return {
            "fps": round(self.fps, 1),
            "frame_time_ms": round(self.frame_time_ms, 2),
            "draw_calls": self.draw_calls,
            "triangles": self.triangles_rendered,
            "memory_mb": round(self.memory_mb, 1),
            "streaming_chunks": self.streaming_chunks,
            "particles": self.particle_count,
            "physics_bodies": self.physics_bodies,
        }


@dataclass
class GameSession:
    name: str = "Untitled Game"
    state: GameState = GameState.EDITOR
    time: float = 0.0
    frame: int = 0
    world_width: int = 512
    world_height: int = 512
    viewer: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    performance: GamePerformance = field(default_factory=GamePerformance)


class NiktoEngine:
    """Unified game engine director — orchestrates all subsystems.

    Provides:
    - Lifecycle management (init, play, pause, stop)
    - Per-frame update for all subsystems
    - World generation with PCG
    - Real-time physics, VFX, streaming
    - Performance monitoring
    """

    def __init__(self):
        self.session = GameSession()
        self.virtual_geometry = VirtualGeometryEngine()
        self.global_illumination = GlobalIllumination()
        self.blueprint_engine = BlueprintEngine()
        self.metahuman_generator = MetaHumanGenerator()
        self.pcg_engine = PCGEngine()
        self.vfx_system = VFXSystem()
        self.chaos_physics = ChaosPhysics()
        self.world_partition = WorldPartition()
        self.asset_library = AssetLibrary()
        self._initialized = False
        self._lumen_enabled = True
        self._nanite_enabled = True
        self._physics_enabled = True
        self._vfx_enabled = True
        self._subsystems: Dict[str, Any] = {}

    def initialize(self):
        """Initialize all subsystems and register default rules/routes."""
        if self._initialized:
            return
        self.pcg_engine.register_default_rules()
        self.world_partition.create_world_grid(radius_cells=20)
        self._setup_default_blueprints()
        self._initialized = True
        self._subsystems = {
            "virtual_geometry": self.virtual_geometry,
            "global_illumination": self.global_illumination,
            "blueprint_engine": self.blueprint_engine,
            "metahuman": self.metahuman_generator,
            "pcg": self.pcg_engine,
            "vfx": self.vfx_system,
            "physics": self.chaos_physics,
            "world_partition": self.world_partition,
            "asset_library": self.asset_library,
        }

    def _setup_default_blueprints(self):
        """Register starter blueprint scripts."""
        bp = self.blueprint_engine
        bp.create_default_player_controller()
        bp.create_sample_ai_behavior()
        for name in ["HealthSystem", "Inventory", "QuestManager",
                     "DoorOpen", "WeaponSystem", "DayNightCycle"]:
            bp.create_graph(name)

    def new_game(self, name: str = "NewGame", world_width: int = 512,
                 world_height: int = 512, seed: int = 0) -> GameSession:
        self.initialize()
        self.session = GameSession(name=name, world_width=world_width, world_height=world_height)
        self.world_partition.create_world_grid(radius_cells=20)
        pcg_result = self.pcg_engine.generate_world(width=world_width, height=world_height, seed=seed)
        for sp in pcg_result.spawn_points:
            if "building" in sp.tags:
                self.chaos_physics.create_rigid_body(
                    sp.x * 2, sp.y * 2, sp.z * 2, ShapeType.BOX,
                    mass=500, size=sp.data.get("floors", 3) * 0.2
                )
        self.vfx_system.create_fire(50, 5, 50)
        self.session.state = GameState.EDITOR
        return self.session

    def start_playing(self):
        self.session.state = GameState.PLAYING
        self.session.time = 0

    def pause(self):
        self.session.state = GameState.PAUSED

    def stop(self):
        self.session.state = GameState.STOPPED

    def update(self, dt: float):
        if self.session.state != GameState.PLAYING:
            return
        self.session.time += dt
        self.session.frame += 1
        if self._nanite_enabled:
            self.virtual_geometry.update_view(self.session.viewer["x"], self.session.viewer["y"], self.session.viewer["z"])
            self.virtual_geometry.process_frame()
        if self._lumen_enabled:
            self.global_illumination.update(dt)
        if self._physics_enabled:
            self.chaos_physics.step(dt)
        if self._vfx_enabled:
            self.vfx_system.update(dt)
        self.world_partition.set_viewer_position(
            self.session.viewer["x"], self.session.viewer["y"], self.session.viewer["z"]
        )
        self.world_partition.update_streaming(dt)
        self._update_performance(dt)

    def _update_performance(self, dt: float):
        perf = self.session.performance
        perf.frame_time_ms = dt * 1000
        perf.fps = 1.0 / dt if dt > 0 else 60
        perf.streaming_chunks = self.world_partition.get_stats()["loaded_chunks"]
        perf.particle_count = self.vfx_system.get_stats()["total_particles"]
        perf.physics_bodies = len(self.chaos_physics.solver.bodies) + len(self.chaos_physics.solver.chunks)
        perf.memory_mb = self.world_partition.get_stats().get("memory_mb", 0)

    def set_viewer(self, x: float, y: float, z: float):
        self.session.viewer = {"x": x, "y": y, "z": z}

    def spawn_actor(self, asset_name: str, x: float, y: float, z: float,
                    scale: float = 1.0) -> Optional[PhysObject]:
        assets = self.asset_library.search(asset_name)
        if not assets:
            return None
        body = self.chaos_physics.create_rigid_body(x, y, z, ShapeType.MESH,
                                                    mass=10, size=scale)
        return body

    def spawn_explosion(self, x: float, y: float, z: float, scale: float = 1.0):
        self.vfx_system.create_explosion(x, y, z, scale)
        self.chaos_physics.simulate_explosion(x, y, z, radius=5*scale, force=50*scale)
        self.chaos_physics.fracture_at(x, y, z, chunk_count=int(10*scale))

    def spawn_character(self, name: str = "Character") -> dict:
        mh = self.metahuman_generator.generate(name=name)
        return mh.to_dict()

    def generate_dungeon(self, rooms: int = 10) -> List[dict]:
        points = self.pcg_engine.generate_dungeon(rooms=rooms)
        return [{"x": p.x, "z": p.z, "tags": p.tags} for p in points]

    def execute_blueprint(self, script_id: str, context: Optional[dict] = None) -> Any:
        return self.blueprint_engine.execute(script_id, context or {})

    def get_status(self) -> dict:
        return {
            "session": {
                "name": self.session.name,
                "state": self.session.state.value,
                "time": round(self.session.time, 2),
                "frame": self.session.frame,
            },
            "performance": self.session.performance.to_dict(),
            "subsystems": {k: self._get_subsystem_stats(k) for k in self._subsystems},
        }

    def _get_subsystem_stats(self, name: str) -> dict:
        mapping = {
            "virtual_geometry": lambda: self.virtual_geometry.get_stats() if hasattr(self.virtual_geometry, 'get_stats') else {},
            "global_illumination": lambda: {"active": True},
            "blueprint_engine": lambda: self.blueprint_engine.get_stats(),
            "metahuman": lambda: self.metahuman_generator.get_stats(),
            "pcg": lambda: self.pcg_engine.get_stats(),
            "vfx": lambda: self.vfx_system.get_stats(),
            "physics": lambda: self.chaos_physics.save_state(),
            "world_partition": lambda: self.world_partition.get_stats(),
            "asset_library": lambda: self.asset_library.get_stats(),
        }
        fn = mapping.get(name, lambda: {})
        try: return fn()
        except: return {"error": "unavailable"}
