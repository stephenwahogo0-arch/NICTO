/// NIKTO Triple-Engine — Spatial Memory Layer (Zig)
///
/// Owns all entity memory via a cache-line-aligned linear arena.
/// Exports C-ABI functions consumable by Rust and Mojo without
/// any intermediate marshalling layer.
///
/// Memory layout: 256 MB static arena, zero fragmentation.
/// Each entity is exactly 64 bytes — one x86-64 cache line.
///
/// Build:
///   zig build-lib -fPIC -dynamic -O ReleaseFast spatial_memory.zig
///   # Produces spatial_memory.so / spatial_memory.dll / spatial_memory.dylib

const std = @import("std");

// ── Constants ──────────────────────────────────────────────────────────

/// Maximum entities the arena can hold.
/// 256 MB ÷ 64 bytes per entity = 4,194,304 entities.
const ARENA_CAPACITY = 4 * 1024 * 1024;

/// Total arena size in bytes.
const ARENA_SIZE = ARENA_CAPACITY * @sizeOf(SpatialEntity);

// ── Spatial Entity (cache-line-packed) ─────────────────────────────────

/// A single entity in the NIKTO engine.
///
/// Memory layout (64 bytes = one x86-64 cache line):
///   [0..7]   id        (u64)
///   [8..11]  x         (f32)
///   [12..15] y         (f32)
///   [16..19] z         (f32)
///   [20..23] vx        (f32)
///   [24..27] vy        (f32)
///   [28..31] vz        (f32)
///   [32..63] _pad      (32 bytes of padding)
///
/// Aligned to 64 bytes so the *address* of every Nth entity in the
/// arena is also cache-line aligned (the arena base is 64-byte aligned).
pub const SpatialEntity = extern struct {
    id: u64,
    x: f32,
    y: f32,
    z: f32,
    vx: f32,
    vy: f32,
    vz: f32,
    _pad: [32]u8,

    /// Initialize at origin with zero velocity.
    pub fn init(id: u64) @This() {
        return .{
            .id = id,
            .x = 0.0,
            .y = 0.0,
            .z = 0.0,
            .vx = 0.0,
            .vy = 0.0,
            .vz = 0.0,
            ._pad = undefined,
        };
    }
};

comptime {
    if (@sizeOf(SpatialEntity) != 64) {
        @compileError("SpatialEntity must be exactly 64 bytes");
    }
}

// ── Linear arena ───────────────────────────────────────────────────────

/// The entire entity buffer sits in the BSS segment. The OS lazily
/// backs physical pages on first touch — zero cost at load time.
var arena: [ARENA_SIZE]u8 align(64) = undefined;

/// Number of entities currently allocated.
var entity_count: u64 = 0;

/// Monotonically increasing ID counter.
var next_id: u64 = 1;

/// Current write cursor offset into the arena.
var cursor: u64 = 0;

// ── C-ABI exports ─────────────────────────────────────────────────────

/// Initialise the memory subsystem.
/// Must be called once before any other function.
export fn spatial_init() callconv(.C) void {
    cursor = 0;
    entity_count = 0;
    next_id = 1;
    // Touch the first page to force OS commit.
    @memset(arena[0..@min(4096, arena.len)], 0);
}

/// Return the base pointer of the arena as a void*.
/// Mojo and Rust receive this pointer and cast it to SpatialEntity*.
export fn spatial_get_base() callconv(.C) ?*anyopaque {
    return &arena;
}

/// Spawn a new entity at (x, y, z) with default velocity.
/// Returns the entity ID, or 0 if the arena is full.
export fn spatial_spawn(x: f32, y: f32, z: f32) callconv(.C) u64 {
    if (entity_count >= ARENA_CAPACITY) return 0;

    const id = next_id;
    next_id += 1;

    const offset = cursor;
    const entity_slice = arena[offset .. offset + @sizeOf(SpatialEntity)];
    cursor += @sizeOf(SpatialEntity);
    entity_count += 1;

    // Write the entity directly into the arena.
    const entity_ptr = @as(*SpatialEntity, @ptrCast(&entity_slice[0]));
    entity_ptr.* = SpatialEntity.init(id);
    entity_ptr.x = x;
    entity_ptr.y = y;
    entity_ptr.z = z;

    return id;
}

/// Spawn a batch of entities from flat [x, y, z, ...] array.
/// Returns the number of entities actually spawned.
export fn spatial_spawn_batch(
    coords: [*]const f32,
    count: u64,
) callconv(.C) u64 {
    const available = ARENA_CAPACITY - entity_count;
    const to_spawn = @min(count, available);
    if (to_spawn == 0) return 0;

    var spawned: u64 = 0;
    while (spawned < to_spawn) : (spawned += 1) {
        const ix = spawned * 3;
        _ = spatial_spawn(coords[ix], coords[ix + 1], coords[ix + 2]);
    }
    return spawned;
}

/// Return the current entity count.
export fn spatial_count() callconv(.C) u64 {
    return entity_count;
}

/// Return the arena capacity (max entities).
export fn spatial_capacity() callconv(.C) u64 {
    return ARENA_CAPACITY;
}

/// Get a pointer to the entity at `index` (0-based).
/// Returns null if the index is out of range.
export fn spatial_get(index: u64) callconv(.C) ?*SpatialEntity {
    if (index >= entity_count) return null;
    const offset = index * @sizeOf(SpatialEntity);
    return @as(*SpatialEntity, @ptrCast(&arena[offset]));
}

/// Get the entity ID at `index`. Returns 0 if out of range.
export fn spatial_get_id(index: u64) callconv(.C) u64 {
    const ent = spatial_get(index) orelse return 0;
    return ent.id;
}

/// Read the position of entity at `index` into the output array [x, y, z].
/// Returns 1 on success, 0 if index out of range.
export fn spatial_get_position(index: u64, out: [*]f32) callconv(.C) u8 {
    const ent = spatial_get(index) orelse return 0;
    out[0] = ent.x;
    out[1] = ent.y;
    out[2] = ent.z;
    return 1;
}

/// Set the position of entity at `index`.
/// Returns 1 on success, 0 if index out of range.
export fn spatial_set_position(index: u64, x: f32, y: f32, z: f32) callconv(.C) u8 {
    const ent = spatial_get(index) orelse return 0;
    ent.x = x;
    ent.y = y;
    ent.z = z;
    return 1;
}

/// Set the velocity of entity at `index`.
/// Returns 1 on success, 0 if index out of range.
export fn spatial_set_velocity(index: u64, vx: f32, vy: f32, vz: f32) callconv(.C) u8 {
    const ent = spatial_get(index) orelse return 0;
    ent.vx = vx;
    ent.vy = vy;
    ent.vz = vz;
    return 1;
}

/// Reset the arena — all entities are destroyed, IDs restart.
export fn spatial_reset() callconv(.C) void {
    cursor = 0;
    entity_count = 0;
    next_id = 1;
}

/// Bulk-copy all positions into a flat f32 array.
/// `out` must have room for count * 3 floats.
/// Returns the number of positions written.
export fn spatial_export_positions(out: [*]f32) callconv(.C) u64 {
    const count = entity_count;
    var i: u64 = 0;
    while (i < count) : (i += 1) {
        const ent = spatial_get(i) orelse break;
        out[i * 3 + 0] = ent.x;
        out[i * 3 + 1] = ent.y;
        out[i * 3 + 2] = ent.z;
    }
    return i;
}

// ── Test ───────────────────────────────────────────────────────────────

test "spatial memory basics" {
    spatial_init();

    const id = spatial_spawn(1.0, 2.0, 3.0);
    try std.testing.expect(id > 0);
    try std.testing.expectEqual(@as(u64, 1), spatial_count());

    var pos: [3]f32 = undefined;
    _ = spatial_get_position(0, &pos);
    try std.testing.expectApproxEqAbs(1.0, pos[0], 0.001);
    try std.testing.expectApproxEqAbs(2.0, pos[1], 0.001);
    try std.testing.expectApproxEqAbs(3.0, pos[2], 0.001);

    try std.testing.expect(spatial_get_id(0) == id);

    spatial_reset();
    try std.testing.expectEqual(@as(u64, 0), spatial_count());
}

test "batch spawn" {
    spatial_init();
    const coords = [_]f32{ 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0 };
    const spawned = spatial_spawn_batch(&coords, 3);
    try std.testing.expectEqual(@as(u64, 3), spawned);
    try std.testing.expectEqual(@as(u64, 3), spatial_count());
}

test "entity struct size" {
    try std.testing.expectEqual(@as(usize, 64), @sizeOf(SpatialEntity));
}
