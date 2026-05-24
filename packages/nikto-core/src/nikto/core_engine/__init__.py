"""NIKTO Core Engine — Rust ECS backend with Python bridge.

This module wraps the compiled native `nikto_core_engine.pyd`/`.so`
and provides a Pythonic interface. If the native binary is not yet
compiled, it raises a clear build instruction.

Usage:
    from nikto.core_engine import NiktoEngine
    engine = NiktoEngine()
    engine.spawn(0.0, 0.0, 10.0)

Build instructions:
    cd packages/nikto-core-engine
    cargo build --release
    cp target/release/nikto_core_engine.pyd ../nikto-core/src/nikto/core_engine/
    # (Windows) or .so on Linux/macOS
"""

import numpy as np

try:
    import nikto_core_engine as _native
    HAS_NATIVE = True
except ImportError:
    HAS_NATIVE = False


class NiktoEngine:
    """High-performance 3D engine core backed by Rust ECS.

    All spatial data lives in contiguous Rust memory arrays.
    Numpy arrays are exchanged zero-copy where possible.
    Entity processing runs in parallel across all CPU cores.
    """

    def __init__(self, chunk_size: int = 16, generate_mesh: bool = True):
        if not HAS_NATIVE:
            raise RuntimeError(
                "NIKTO Core Engine native module not found.\n\n"
                "Build it:\n"
                "  cd packages/nikto-core-engine\n"
                "  cargo build --release\n"
                "  cp target/release/nikto_core_engine.pyd packages/nikto-core/src/nikto/core_engine/\n\n"
                "Requires Rust: https://rustup.rs"
            )
        self._engine = _native.NiktoEngine(chunk_size=chunk_size, generate_mesh=generate_mesh)

    # ── Entity lifecycle ────────────────────────────────────────────

    def spawn(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> int:
        """Spawn a single entity at (x, y, z). Returns unique entity ID."""
        return self._engine.spawn(x, y, z)

    def spawn_batch(self, positions: list) -> list[int]:
        """Spawn multiple entities from [[x,y,z], ...] or numpy N×3 array.

        Args:
            positions: list of [x,y,z] triples or (N,3) numpy float32 array.

        Returns:
            list of entity IDs.
        """
        if isinstance(positions, np.ndarray):
            positions = positions.tolist()
        return self._engine.spawn_batch(positions)

    def despawn(self, entity_id: int) -> bool:
        """Remove an entity by ID. Returns True if found."""
        return self._engine.despawn(entity_id)

    def clear(self):
        """Remove all entities from the world."""
        self._engine.clear()

    @property
    def entity_count(self) -> int:
        """Number of entities currently in the world."""
        return self._engine.entity_count()

    def reserve(self, additional: int):
        """Pre-allocate capacity to avoid reallocation."""
        self._engine.reserve(additional)

    # ── Spatial data ────────────────────────────────────────────────

    @property
    def positions(self) -> np.ndarray:
        """All entity positions as (N×3) float32 numpy array."""
        flat = self._engine.get_positions()
        return flat.reshape(-1, 3)

    @property
    def matrices(self) -> np.ndarray:
        """All entity transforms as (N×16) float32 numpy array (column-major)."""
        flat = self._engine.get_matrices()
        return flat.reshape(-1, 16)

    def get_entity_spatial(self, entity_id: int) -> dict | None:
        """Get an entity's spatial state as a dict.

        Returns None if the entity ID doesn't exist.
        """
        raw = self._engine.get_entity_spatial(entity_id)
        if raw is None:
            return None
        return {
            "x": raw[0], "y": raw[1], "z": raw[2],
            "rotation_x": raw[3], "rotation_y": raw[4], "rotation_z": raw[5],
            "scale_x": raw[6], "scale_y": raw[7], "scale_z": raw[8],
        }

    def set_position(self, entity_id: int, x: float, y: float, z: float) -> bool:
        """Set an entity's position by ID. Returns True if found."""
        return self._engine.set_position(entity_id, x, y, z)

    # ── World generation ────────────────────────────────────────────

    def ingest_voxels(self, voxels: np.ndarray) -> tuple:
        """Ingest a 3D voxel grid from a brain's procedural generator.

        Args:
            voxels: 3D uint32 numpy array (non-zero = solid).

        Returns:
            (entity_count, vertex_count, index_count)
        """
        if voxels.dtype != np.uint32:
            voxels = voxels.astype(np.uint32)
        # Ensure C-contiguous for zero-copy
        voxels = np.ascontiguousarray(voxels)
        return self._engine.ingest_voxels(voxels)

    def ingest_voxels_parallel(self, voxels: np.ndarray) -> tuple:
        """Ingest a large voxel grid with parallel chunked processing.

        For grids larger than ~32³, this is significantly faster than
        the single-threaded `ingest_voxels`.

        Returns:
            (entity_count, vertex_count, index_count)
        """
        if voxels.dtype != np.uint32:
            voxels = voxels.astype(np.uint32)
        voxels = np.ascontiguousarray(voxels)
        return self._engine.ingest_voxels_parallel(voxels)

    def ingest_coordinates(self, coords: np.ndarray) -> list[int]:
        """Ingest a point cloud from a coordinate matrix.

        Args:
            coords: (N×3) float32 numpy array of [x,y,z] positions.

        Returns:
            list of entity IDs created.
        """
        if coords.dtype != np.float32:
            coords = coords.astype(np.float32)
        coords = np.ascontiguousarray(coords).ravel()
        return self._engine.ingest_coordinates(coords)

    # ── Parallel updates ────────────────────────────────────────────

    def apply_wave(self, time: float = 0.0, amplitude: float = 1.0, frequency: float = 1.0):
        """Apply a sinusoidal oscillation to all visible entities.

        Runs in parallel across all CPU cores.
        """
        self._engine.apply_wave(time, amplitude, frequency)

    def apply_float(self, speed: float = 1.0) -> int:
        """Float all visible entities upward. Returns count of affected entities."""
        return self._engine.apply_float(speed)

    # ── Info ────────────────────────────────────────────────────────

    def info(self) -> dict:
        """Engine metadata."""
        items = self._engine.info()
        return dict(items)

    def __repr__(self) -> str:
        info = self.info()
        return (
            f"<NiktoEngine v{info.get('version', '?')} "
            f"entities={info.get('entity_count', '?')} "
            f"workers={info.get('parallel_workers', '?')}>"
        )
