"""World Partition & Level Streaming System.

Open-world streaming for infinite-scale environments:
- Grid-based world partitioning with LOD streaming
- Chunk streaming (loading/unloading based on distance)
- Persistent level system
- HLOD (Hierarchical LOD) generation
- Streaming volumes and priority queuing
=== DOCUMENTATION: NIKTO WORLD PARTITION ===
World Partition enables massive open worlds by dividing the world
into a grid of cells (chunks) that stream in/out based on the
viewer's position. Key components:

  Chunk          - A cell in the world grid containing actors/objects
  ChunkLOD       - A level-of-detail version of a chunk (lower poly)
  HLOD           - Hierarchical LOD that merges chunks into single meshes
  StreamingVolume- Regions that trigger streaming (boxes, spheres)
  StreamingPriority- Priority queue for managing which chunks load first
  WorldPartition - The central manager that orchestrates everything

Streaming uses distance-based loading/unloading with a ring buffer.
HLOD clusters nearby objects into combined meshes at runtime.
"""
from __future__ import annotations
import math
import json
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class ChunkState(Enum):
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    STREAMING = "streaming"


class HLODLevel(Enum):
    LOD0 = 0  # Full detail
    LOD1 = 1  # Reduced
    LOD2 = 2  # Medium
    LOD3 = 3  # Low
    LOD4 = 4  # Very low (far distance)


class StreamingStrategy(Enum):
    DISTANCE = "distance"
    PRIORITY = "priority"
    VISIBILITY = "visibility"
    PREDICTIVE = "predictive"


@dataclass
class Chunk:
    """A single cell in the world grid."""
    cell_x: int
    cell_y: int
    cell_z: int = 0
    state: ChunkState = ChunkState.UNLOADED
    size: float = 100.0
    lod: int = 0
    objects: List[dict] = field(default_factory=list)
    vertex_count: int = 0
    triangle_count: int = 0
    memory_estimate_kb: float = 0.0
    streaming_priority: float = 0.0
    last_accessed: float = 0.0

    @property
    def world_x(self) -> float:
        return self.cell_x * self.size

    @property
    def world_y(self) -> float:
        return self.cell_y * self.size

    @property
    def world_z(self) -> float:
        return self.cell_z * self.size

    def distance_to(self, px: float, py: float, pz: float) -> float:
        cx = self.world_x + self.size * 0.5
        cy = self.world_y + self.size * 0.5
        cz = self.world_z + self.size * 0.5
        return math.sqrt((px - cx)**2 + (py - cy)**2 + (pz - cz)**2)

    def contains(self, x: float, y: float, z: float) -> bool:
        return (self.world_x <= x < self.world_x + self.size and
                self.world_y <= y < self.world_y + self.size and
                self.world_z <= z < self.world_z + self.size)


@dataclass
class ChunkLOD:
    """A level-of-detail version of a chunk."""
    chunk: Chunk
    lod_level: int
    vertex_count: int = 0
    triangle_count: int = 0
    objects: List[dict] = field(default_factory=list)
    memory_kb: float = 0.0


@dataclass
class HLOD:
    """Hierarchical LOD — merges multiple chunks into one."""
    id: str
    cell_x: int; cell_y: int; cell_z: int
    span_x: int; span_y: int; span_z: int
    lod_level: HLODLevel
    vertex_count: int = 0
    triangle_count: int = 0
    objects_merged: int = 0
    proxy_mesh_data: dict = field(default_factory=dict)


@dataclass
class StreamingVolume:
    """A volume that triggers chunk streaming."""
    name: str
    x: float; y: float; z: float
    radius: float = 100.0
    width: float = 0; height: float = 0; depth: float = 0
    priority: float = 1.0
    auto_load: bool = True
    is_sphere: bool = True


@dataclass
class StreamingPriority:
    chunk: Chunk
    priority: float = 0.0
    reason: str = ""


class WorldPartition:
    """Manages chunks, streaming, and HLOD for infinite open worlds.

    The world is divided into a 3D grid. Chunks near the viewer are
    streamed in at full LOD; distant chunks use HLOD proxies.
    """

    def __init__(self):
        self.chunks: Dict[Tuple[int, int, int], Chunk] = {}
        self.hlods: Dict[str, HLOD] = {}
        self.streaming_volumes: List[StreamingVolume] = []
        self.priority_queue: List[StreamingPriority] = []
        self.stream_distance: float = 500.0
        self.unload_distance: float = 700.0
        self.lod_distances: List[float] = [0, 100, 250, 500, 800]
        self.chunk_size: float = 100.0
        self.viewer_x: float = 0.0
        self.viewer_y: float = 0.0
        self.viewer_z: float = 0.0
        self.max_streaming_per_frame: int = 4
        self._memory_usage_mb: float = 0.0
        self._loaded_chunks: int = 0
        self._total_chunk_cells: int = 0
        self._streaming_history: List[dict] = []
        self._frame_count: int = 0

    def create_chunks_in_region(self, x_min: int, x_max: int, y_min: int, y_max: int,
                                 z_min: int = 0, z_max: int = 0):
        """Reserve (but don't load) chunks in a rectangular region."""
        for cx in range(x_min, x_max + 1):
            for cy in range(y_min, y_max + 1):
                for cz in range(z_min, z_max + 1):
                    key = (cx, cy, cz)
                    if key not in self.chunks:
                        self.chunks[key] = Chunk(
                            cell_x=cx, cell_y=cy, cell_z=cz,
                            state=ChunkState.UNLOADED, size=self.chunk_size
                        )
        self._total_chunk_cells = len(self.chunks)

    def create_world_grid(self, radius_cells: int = 10):
        """Create a square grid of chunks around origin."""
        self.create_chunks_in_region(-radius_cells, radius_cells,
                                     -radius_cells, radius_cells)

    def set_viewer_position(self, x: float, y: float, z: float):
        self.viewer_x, self.viewer_y, self.viewer_z = x, y, z

    def update_streaming(self, dt: float = 0.016):
        """Update chunk streaming based on viewer position."""
        self._frame_count += 1
        self._build_priority_queue()
        loaded_this_frame = 0
        unloading_this_frame = 0

        for sp in sorted(self.priority_queue, key=lambda x: -x.priority):
            chunk = sp.chunk
            dist = chunk.distance_to(self.viewer_x, self.viewer_y, self.viewer_z)

            if dist < self.stream_distance and chunk.state == ChunkState.UNLOADED:
                if loaded_this_frame < self.max_streaming_per_frame:
                    chunk.state = ChunkState.LOADING
                    self._load_chunk(chunk)
                    chunk.state = ChunkState.LOADED
                    loaded_this_frame += 1

            elif dist > self.unload_distance and chunk.state == ChunkState.LOADED:
                if unloading_this_frame < self.max_streaming_per_frame:
                    chunk.state = ChunkState.UNLOADING
                    self._unload_chunk(chunk)
                    chunk.state = ChunkState.UNLOADED
                    unloading_this_frame += 1
            else:
                chunk.lod = self._calculate_lod(dist)
        self._compute_hlods()
        self._update_memory_stats()

    def _build_priority_queue(self):
        self.priority_queue.clear()
        for chunk in self.chunks.values():
            dist = chunk.distance_to(self.viewer_x, self.viewer_y, self.viewer_z)
            priority = 1.0 / (1.0 + dist * 0.01)
            if chunk.state == ChunkState.LOADING or chunk.state == ChunkState.LOADED:
                priority *= 0.5
            for vol in self.streaming_volumes:
                if vol.is_sphere:
                    vd = math.sqrt((self.viewer_x - vol.x)**2 + (self.viewer_y - vol.y)**2 + (self.viewer_z - vol.z)**2)
                    if vd < vol.radius:
                        priority += vol.priority * 2.0
                else:
                    if abs(chunk.world_x - vol.x) < vol.width and abs(chunk.world_y - vol.y) < vol.height:
                        priority += vol.priority * 2.0
            self.priority_queue.append(StreamingPriority(chunk, priority))

    def _calculate_lod(self, dist: float) -> int:
        for i, d in enumerate(self.lod_distances):
            if dist < d:
                return i
        return len(self.lod_distances) - 1

    def _load_chunk(self, chunk: Chunk):
        chunk.objects = [
            {"type": "static_mesh", "lod": chunk.lod, "objects": 10 + chunk.lod * 5},
            {"type": "foliage", "instances": 50 - chunk.lod * 10},
        ]
        chunk.vertex_count = max(100, 10000 - chunk.lod * 2000)
        chunk.triangle_count = max(50, 5000 - chunk.lod * 1000)
        chunk.memory_estimate_kb = chunk.vertex_count * 32 / 1024
        self._streaming_history.append({
            "frame": self._frame_count,
            "action": "load",
            "cell": (chunk.cell_x, chunk.cell_y, chunk.cell_z),
            "lod": chunk.lod,
        })

    def _unload_chunk(self, chunk: Chunk):
        chunk.objects.clear()
        chunk.vertex_count = 0
        chunk.triangle_count = 0
        chunk.memory_estimate_kb = 0
        self._streaming_history.append({
            "frame": self._frame_count,
            "action": "unload",
            "cell": (chunk.cell_x, chunk.cell_y, chunk.cell_z),
        })

    def _compute_hlods(self):
        group_size = 4
        for cx_start in range(-50, 51, group_size):
            for cy_start in range(-50, 51, group_size):
                hlod_id = f"HLOD_{cx_start}_{cy_start}"
                exists = any(h.cell_x == cx_start and h.cell_y == cy_start for h in self.hlods.values())
                if not exists:
                    merged_objects = 0
                    for dx in range(group_size):
                        for dy in range(group_size):
                            key = (cx_start + dx, cy_start + dy, 0)
                            if key in self.chunks and self.chunks[key].state == ChunkState.LOADED:
                                merged_objects += len(self.chunks[key].objects)
                    self.hlods[hlod_id] = HLOD(
                        id=hlod_id,
                        cell_x=cx_start, cell_y=cy_start, cell_z=0,
                        span_x=group_size, span_y=group_size, span_z=1,
                        lod_level=HLODLevel.LOD2,
                        vertex_count=5000, triangle_count=2500,
                        objects_merged=merged_objects,
                        proxy_mesh_data={"type": "merged_static", "objects": merged_objects}
                    )

    def _update_memory_stats(self):
        self._loaded_chunks = sum(1 for c in self.chunks.values() if c.state == ChunkState.LOADED)
        memory_kb = sum(c.memory_estimate_kb for c in self.chunks.values() if c.state == ChunkState.LOADED)
        self._memory_usage_mb = memory_kb / 1024

    def add_streaming_volume(self, volume: StreamingVolume):
        self.streaming_volumes.append(volume)

    def get_chunk_at(self, x: float, y: float, z: float) -> Optional[Chunk]:
        cx = int(x // self.chunk_size)
        cy = int(y // self.chunk_size)
        cz = int(z // self.chunk_size)
        return self.chunks.get((cx, cy, cz))

    def get_chunks_in_radius(self, x: float, y: float, z: float, radius: float) -> List[Chunk]:
        results = []
        for chunk in self.chunks.values():
            if chunk.distance_to(x, y, z) < radius:
                results.append(chunk)
        return results

    def get_stats(self) -> dict:
        return {
            "total_chunks": self._total_chunk_cells,
            "loaded_chunks": self._loaded_chunks,
            "memory_mb": round(self._memory_usage_mb, 2),
            "streaming_volumes": len(self.streaming_volumes),
            "hlods": len(self.hlods),
            "viewer_pos": (self.viewer_x, self.viewer_y, self.viewer_z),
            "stream_distance": self.stream_distance,
            "unload_distance": self.unload_distance,
            "pending_stream": len(self.priority_queue),
            "frames": self._frame_count,
        }
