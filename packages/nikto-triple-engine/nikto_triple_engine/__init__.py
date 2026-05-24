"""NIKTO Triple-Engine — Zig + Mojo + Rust integrated native module.

This module wraps the compiled `nikto_triple_engine.pyd` / `.so` and
provides a Pythonic interface. If the native binary is not yet compiled,
it raises a clear build instruction.

Architecture:
   Zig     — Owns the entity memory (cache-line-aligned linear arena)
   Mojo 🔥 — SIMD physics simulation (parallel across all cores)
   Rust    — Orchestrator + PyO3 bridge (exposes as native Python module)

Usage:
    from nikto_triple_engine import NiktoTripleEngine

    engine = NiktoTripleEngine()

    # Spawn entities
    engine.spawn(0.0, 0.0, 0.0)
    engine.spawn_batch([[10, 0, 0], [20, 0, 0], [30, 0, 0]])

    # Run physics (Mojo SIMD on all cores)
    engine.update_physics(dt=0.016, gravity=9.81, time=1.0)

    # Read results
    positions = engine.get_positions_list()
    print(f"Center of mass: {engine.center_of_mass()}")
"""

try:
    import nikto_triple_engine as _native
    HAS_NATIVE = True
except ImportError:
    HAS_NATIVE = False


class NiktoTripleEngine:
    """High-performance 3D engine with Zig memory + Mojo physics + Rust bridge.

    All entity data lives in Zig's linear arena (cache-line-aligned).
    Physics runs in Mojo via SIMD across all CPU cores.
    Python receives results as lists or numpy-compatible arrays.
    """

    def __init__(self):
        if not HAS_NATIVE:
            raise RuntimeError(
                "NIKTO Triple-Engine native module not found.\n\n"
                "Build instructions:\n"
                "  1. Install prerequisites:\n"
                "     - Rust:    https://rustup.rs\n"
                "     - Zig:     https://ziglang.org/download\n"
                "     - Mojo:    https://docs.modular.com/mojo (optional)\n\n"
                "  2. Build:\n"
                "     cd packages/nikto-triple-engine\n"
                "     cargo build --release\n\n"
                "  3. Copy to Python package:\n"
                "     cp target/release/nikto_triple_engine.pyd .\n\n"
                "  4. Import:\n"
                "     from nikto_triple_engine import NiktoTripleEngine"
            )
        self._engine = _native.NiktoTripleEngine()

    # ── Entity lifecycle ────────────────────────────────────────────

    def spawn(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> int:
        """Spawn a single entity at (x, y, z). Returns unique ID."""
        return self._engine.spawn(x, y, z)

    def spawn_batch(self, positions: list) -> list[int]:
        """Spawn multiple entities from [[x,y,z], ...].

        Args:
            positions: list of [x, y, z] triples.

        Returns:
            list of entity IDs.
        """
        return self._engine.spawn_batch(positions)

    def clear(self):
        """Remove all entities from the arena."""
        self._engine.clear()

    @property
    def entity_count(self) -> int:
        """Number of entities currently allocated."""
        return self._engine.entity_count

    @property
    def capacity(self) -> int:
        """Maximum number of entities the arena can hold."""
        return self._engine.capacity

    # ── Physics ────────────────────────────────────────────────────

    def update_physics(
        self,
        dt: float = 0.016,
        gravity: float = 9.81,
        time: float = 0.0,
    ) -> int:
        """Run one physics tick on all entities.

        Executes in Mojo with SIMD vectorization across all CPU cores.

        Args:
            dt: Delta time in seconds (0.016 ≈ 60 FPS).
            gravity: Gravitational acceleration.
            time: Current simulation time.

        Returns:
            Number of entities processed.
        """
        return self._engine.update_physics(dt, gravity, time)

    def detect_collisions(self, radius: float = 1.0) -> int:
        """Detect and resolve collisions between nearby entities.

        Uses Mojo SIMD-accelerated broad-phase collision detection.

        Args:
            radius: Collision radius.

        Returns:
            Number of collisions detected and resolved.
        """
        return self._engine.detect_collisions(radius)

    # ── Position queries ────────────────────────────────────────────

    def get_positions_list(self) -> list[list[float]]:
        """Get all entity positions as [[x, y, z], ...]."""
        return self._engine.get_positions_list()

    def get_position(self, index: int) -> list[float] | None:
        """Get a single entity's position by index. Returns None if invalid."""
        result = self._engine.get_position(index)
        return list(result) if result else None

    def set_position(self, index: int, x: float, y: float, z: float) -> bool:
        """Set a single entity's position by index."""
        return self._engine.set_position(index, x, y, z)

    def set_velocity(self, index: int, vx: float, vy: float, vz: float) -> bool:
        """Set a single entity's velocity by index."""
        return self._engine.set_velocity(index, vx, vy, vz)

    # ── Analysis ────────────────────────────────────────────────────

    def center_of_mass(self) -> list[float]:
        """Compute the center of mass across all entities.

        Returns [cx, cy, cz].
        """
        return list(self._engine.center_of_mass())

    # ── Info ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"<NiktoTripleEngine entities={self.entity_count}/{self.capacity} "
            f"layers=[Zig/Mojo/Rust]>"
        )
