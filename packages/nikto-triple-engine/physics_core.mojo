/// NIKTO Triple-Engine — Neural Physics & Simulation Core (Mojo 🔥)
///
/// Leverages Mojo's SIMD vectorization and parallelize to process
/// all entities in the Zig arena at near-hardware speed.
///
/// Receives the raw pointer from Zig's linear arena via C-ABI.
/// No copies, no marshalling — reads/writes entity memory in place.
///
/// Build:
///   mojo build physics_core.mojo -o libphysics_core.a
///   # Produces a static archive linkable by Rust's build.rs

from memory.unsafe import UnsafePointer
from math import sin, sqrt
from algorithm import parallelize, vectorize
from sys import simd, info

# ── C-compatible entity struct (mirrors Zig exactly) ────────────────────

@value
@register_passable
struct SpatialEntity:
    """Must match `spatial_memory.zig:SpatialEntity` byte-for-byte.

    Memory layout (64 bytes):
      [0..7]   id  (UInt64)
      [8..11]  x   (Float32)
      [12..15] y   (Float32)
      [16..19] z   (Float32)
      [20..23] vx  (Float32)
      [24..27] vy  (Float32)
      [28..31] vz  (Float32)
      [32..63] pad (32 bytes of padding)
    """
    var id: UInt64
    var x: Float32
    var y: Float32
    var z: Float32
    var vx: Float32
    var vy: Float32
    var vz: Float32
    var _pad: SIMD[UInt8, 32]

# ── SIMD width determined at compile time from target hardware ─────────

alias simd_width = simd_width_of[Float32]()
alias simd_f32 = SIMD[Float32, simd_width]

# ── Chunk worker (called by parallelize) ────────────────────────────────

fn physics_chunk(
    start: Int,
    end: Int,
    ptr: UnsafePointer[SpatialEntity],
    dt: Float32,
    gravity: Float32,
    time: Float32,
):
    """Process entities [start, end) with SIMD-accelerated physics.

    Within each chunk, entities are processed in SIMD-width batches.
    """
    var g = simd_f32(gravity * dt)
    var damp = simd_f32(0.998)  # velocity damping per frame
    var dt_vec = simd_f32(dt)
    var time_vec = simd_f32(time)
    var freq_vec = simd_f32(0.5)
    var amp_vec = simd_f32(0.1 * dt * 60.0)
    var zero = simd_f32(0.0)

    # Process in SIMD-width batches
    var i = start
    while i + simd_width <= end:
        # Load 4 (or simd_width) entities' y, vx, vy, vz fields
        var xs = simd_f32(0.0)
        var ys = simd_f32(0.0)
        var zs = simd_f32(0.0)
        var vxs = simd_f32(0.0)
        var vys = simd_f32(0.0)
        var vzs = simd_f32(0.0)

        for k in range(simd_width):
            var ent = ptr.load(i + k)
            xs[k] = ent.x
            ys[k] = ent.y
            zs[k] = ent.z
            vxs[k] = ent.vx
            vys[k] = ent.vy
            vzs[k] = ent.vz

        # Apply gravity (y velocity)
        vys = vys - g

        # Apply sinusoidal wave oscillation
        var wave = (time_vec + xs * freq_vec).sin()
        ys = ys + wave * amp_vec

        # Velocity damping
        vxs = vxs * damp
        vys = vys * damp
        vzs = vzs * damp

        # Position integration
        xs = xs + vxs * dt_vec
        ys = ys + vys * dt_vec
        zs = zs + vzs * dt_vec

        # Store results back
        for k in range(simd_width):
            var ent = ptr.load(i + k)
            ent.x = xs[k]
            ent.y = ys[k]
            ent.z = zs[k]
            ent.vx = vxs[k]
            ent.vy = vys[k]
            ent.vz = vzs[k]
            ptr.store(i + k, ent)

        i += simd_width

    # Handle remaining entities (non-SIMD tail)
    while i < end:
        var ent = ptr.load(i)
        ent.vy -= gravity * dt
        ent.y += sin(time + ent.x * 0.5) * 0.1 * dt * 60.0
        ent.vx *= 0.998
        ent.vy *= 0.998
        ent.vz *= 0.998
        ent.x += ent.vx * dt
        ent.y += ent.vy * dt
        ent.z += ent.vz * dt
        ptr.store(i, ent)
        i += 1

# ── C-ABI exports ──────────────────────────────────────────────────────

@always_inline
fn physics_init() raises:
    """One-time initialisation (no-op for now, reserved for GPU context setup)."""
    pass

fn physics_update(
    ptr: UnsafePointer[SpatialEntity],
    count: Int,
    dt: Float32,
    gravity: Float32,
    time: Float32,
) raises -> Int:
    """Run one physics tick on all entities in the Zig arena.

    Args:
        ptr: Pointer to the first SpatialEntity in Zig's linear arena.
        count: Number of entities to process.
        dt: Delta time in seconds.
        gravity: Gravitational acceleration (units/s²).
        time: Current simulation time for wave offset.

    Returns:
        Number of entities processed.
    """
    # If count is small, run single-threaded (parallelize overhead > benefit)
    if count < 1024:
        physics_chunk(0, count, ptr, dt, gravity, time)
    else:
        # Split across all available cores
        parallelize[fn(start: Int, end: Int) raises -> None:
            physics_chunk(start, end, ptr, dt, gravity, time)
        ](count)

    return count

# ── Matrix operation: compute average position ─────────────────────────

fn physics_center_of_mass(
    ptr: UnsafePointer[SpatialEntity],
    count: Int,
) raises -> SIMD[Float32, 3]:
    """Compute the center of mass across all entities using SIMD reduction.

    Returns a 3-element SIMD vector [cx, cy, cz].
    """
    var sum_x = simd_f32(0.0)
    var sum_y = simd_f32(0.0)
    var sum_z = simd_f32(0.0)

    var i = 0
    while i + simd_width <= count:
        var xs = simd_f32(0.0)
        var ys = simd_f32(0.0)
        var zs = simd_f32(0.0)
        for k in range(simd_width):
            var ent = ptr.load(i + k)
            xs[k] = ent.x
            ys[k] = ent.y
            zs[k] = ent.z
        sum_x += xs
        sum_y += ys
        sum_z += zs
        i += simd_width

    var rem_x: Float32 = 0.0
    var rem_y: Float32 = 0.0
    var rem_z: Float32 = 0.0
    while i < count:
        var ent = ptr.load(i)
        rem_x += ent.x
        rem_y += ent.y
        rem_z += ent.z
        i += 1

    var total = Float32(count)
    return SIMD[Float32, 3](
        (sum_x.reduce_add() + rem_x) / total,
        (sum_y.reduce_add() + rem_y) / total,
        (sum_z.reduce_add() + rem_z) / total,
    )

# ── Collision detection (broad phase) ──────────────────────────────────

fn physics_detect_collisions(
    ptr: UnsafePointer[SpatialEntity],
    count: Int,
    radius: Float32,
) raises -> Int:
    """Simple broad-phase collision detection.

    For each pair of entities within `radius` distance, applies a
    repulsion impulse. This is O(n²) but using SIMD minimises the
    constant factor. For production, replace with spatial hash.

    Returns the number of collisions detected.
    """
    var collision_count: Int = 0
    var r2: Float32 = radius * radius

    for i in range(count):
        var ent_a = ptr.load(i)
        var ax = simd_f32(ent_a.x)
        var ay = simd_f32(ent_a.y)
        var az = simd_f32(ent_a.z)

        var j = i + 1
        while j + simd_width <= count:
            var bx = simd_f32(0.0)
            var by = simd_f32(0.0)
            var bz = simd_f32(0.0)
            for k in range(simd_width):
                var ent_b = ptr.load(j + k)
                bx[k] = ent_b.x
                by[k] = ent_b.y
                bz[k] = ent_b.z

            var dx = bx - ax
            var dy = by - ay
            var dz = bz - az
            var dist2 = dx * dx + dy * dy + dz * dz
            var collided = dist2 < simd_f32(r2)

            # Count collisions (SIMD mask reduction)
            for k in range(simd_width):
                if collided[k]:
                    collision_count += 1
                    # Simple repulsion: swap velocities
                    var ent_b = ptr.load(j + k)
                    var tmp_vx = ent_a.vx
                    var tmp_vy = ent_a.vy
                    var tmp_vz = ent_a.vz
                    ent_a.vx = ent_b.vx
                    ent_a.vy = ent_b.vy
                    ent_a.vz = ent_b.vz
                    ent_b.vx = tmp_vx
                    ent_b.vy = tmp_vy
                    ent_b.vz = tmp_vz
                    ptr.store(j + k, ent_b)

            j += simd_width

        # Tail
        while j < count:
            var ent_b = ptr.load(j)
            var dx = ent_a.x - ent_b.x
            var dy = ent_a.y - ent_b.y
            var dz = ent_a.z - ent_b.z
            if dx * dx + dy * dy + dz * dz < r2:
                collision_count += 1
                var tmp_vx = ent_a.vx; var tmp_vy = ent_a.vy; var tmp_vz = ent_a.vz
                ent_a.vx = ent_b.vx; ent_a.vy = ent_b.vy; ent_a.vz = ent_b.vz
                ent_b.vx = tmp_vx; ent_b.vy = tmp_vy; ent_b.vz = tmp_vz
                ptr.store(j, ent_b)
            j += 1

        ptr.store(i, ent_a)

    return collision_count
