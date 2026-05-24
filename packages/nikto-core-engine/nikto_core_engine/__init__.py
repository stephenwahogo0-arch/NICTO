"""NIKTO Core Engine — Rust ECS + wgpu GPU renderer.

Three integrated layers:
  1. ECS: cache-line-aligned entity storage with parallel systems
  2. World gen: procedural voxel/mesh ingestion from AI brains
  3. Scene + Renderer: octree scene graph + wgpu GPU pipeline

Usage:
    from nikto_core_engine import NiktoEngine

    engine = NiktoEngine()

    # ECS operations
    engine.spawn_batch([[0,0,0], [10,0,0]])
    engine.apply_wave(time=1.0, amplitude=2.0)

    # GPU rendering window
    engine.start_window(1280, 720, "NIKTO Engine")
    engine.demo_cubes(count=8, spacing=2.5)
    engine.set_camera(15, 10, 15, 0, 0, 0)
"""

try:
    import nikto_core_engine as _native
    HAS_NATIVE = True
except ImportError:
    HAS_NATIVE = False


class NiktoEngine:
    def __init__(self, chunk_size: int = 16, generate_mesh: bool = True):
        if not HAS_NATIVE:
            raise RuntimeError(
                "Native module not found. Build:\n"
                "  cd packages/nikto-core-engine\n"
                "  cargo build --release\n"
                "  cp target/release/nikto_core_engine.pyd nikto_core_engine/"
            )
        self._engine = _native.NiktoEngine(chunk_size=chunk_size, generate_mesh=generate_mesh)

    # ── ECS ─────────────────────────────────────────────────────────

    def spawn(self, x: float = 0, y: float = 0, z: float = 0) -> int:
        return self._engine.spawn(x, y, z)

    def spawn_batch(self, positions: list) -> list[int]:
        return self._engine.spawn_batch(positions)

    def despawn(self, entity_id: int) -> bool:
        return self._engine.despawn(entity_id)

    def clear(self):
        self._engine.clear()

    @property
    def entity_count(self) -> int:
        return self._engine.entity_count()

    def get_positions(self):
        return self._engine.get_positions().reshape(-1, 3)

    def set_position(self, entity_id: int, x: float, y: float, z: float) -> bool:
        return self._engine.set_position(entity_id, x, y, z)

    # ── World generation ───────────────────────────────────────────

    def ingest_voxels(self, voxels) -> tuple:
        return self._engine.ingest_voxels(voxels)

    def ingest_voxels_parallel(self, voxels) -> tuple:
        return self._engine.ingest_voxels_parallel(voxels)

    def ingest_coordinates(self, coords) -> list[int]:
        return self._engine.ingest_coordinates(coords)

    # ── Parallel systems ───────────────────────────────────────────

    def apply_wave(self, time: float = 0, amplitude: float = 1, frequency: float = 1):
        self._engine.apply_wave(time, amplitude, frequency)

    def apply_float(self, speed: float = 1) -> int:
        return self._engine.apply_float(speed)

    # ── GPU Rendering ──────────────────────────────────────────────

    def start_window(self, width: int = 1280, height: int = 720, title: str = "NIKTO Engine"):
        self._engine.start_window(width, height, title)

    def close_window(self):
        self._engine.close_window()

    @property
    def is_window_open(self) -> bool:
        return self._engine.is_window_open()

    def set_camera(self, x: float, y: float, z: float, target_x: float = 0, target_y: float = 0, target_z: float = 0):
        self._engine.set_camera(x, y, z, target_x, target_y, target_z)

    def add_mesh(self, vertices: list, indices: list):
        self._engine.add_mesh(vertices, indices)

    def spawn_mesh(self, mesh_index: int, x: float, y: float, z: float):
        self._engine.spawn_mesh(mesh_index, x, y, z)

    def demo_cubes(self, count: int = 8, spacing: float = 2.5):
        """Spawn a grid of cubes to verify the render pipeline."""
        self._engine.demo_cubes(count, spacing)

    # ── Info ────────────────────────────────────────────────────────

    def info(self) -> dict:
        return dict(self._engine.info())

    def __repr__(self) -> str:
        i = self.info()
        return (
            f"<NiktoEngine v{i.get('version','?')} "
            f"entities={i.get('entity_count','?')} "
            f"renderer={i.get('renderer','?')}>"
        )
