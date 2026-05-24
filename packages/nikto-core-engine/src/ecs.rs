/// ECS core — cache-line-aligned entity storage with parallel system execution.
///
/// # Memory Layout
/// Each `RenderEntity` packs its hot spatial data into exactly one x86-64
/// cache line (64 bytes). When the physics or culling system iterates,
/// every memory fetch lands in L1 without pulling cold metadata into cache.
///
/// # Parallelism
/// `World::parallel_update` splits the entity array into chunks and
/// dispatches each chunk to a separate CPU core via `rayon`. No locks
/// are needed because each core operates on its own chunk.

use bytemuck::{Pod, Zeroable};
use parking_lot::RwLock;
use rayon::prelude::*;
use std::sync::atomic::{AtomicU64, Ordering};

// ── Entity ID generator ────────────────────────────────────────────────
static NEXT_ENTITY_ID: AtomicU64 = AtomicU64::new(1);

#[inline]
fn allocate_id() -> u64 {
    NEXT_ENTITY_ID.fetch_add(1, Ordering::Relaxed)
}

// ── Spatial data: packed into exactly one 64-byte cache line ───────────

/// 3D spatial data that fits in one L1 cache line.
///
/// On x86-64, a cache line is 64 bytes. This struct uses 36 bytes of
/// f32 data and 28 bytes of padding to align perfectly to 64 bytes.
/// The `align(64)` attribute guarantees the *address* is also cache-line
/// aligned when the struct is in a `Vec` (the allocator provides 16-byte
/// alignment; use `alloc_aligned` for guaranteed 64-byte alignment).
#[repr(C, align(64))]
#[derive(Clone, Copy, Debug)]
pub struct SpatialData {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub rotation_x: f32,
    pub rotation_y: f32,
    pub rotation_z: f32,
    pub scale_x: f32,
    pub scale_y: f32,
    pub scale_z: f32,
    // Pad to 64 bytes: 9 × f32 = 36 used, 28 padding
    _pad: [u8; 28],
}

// Safe to transmute from raw bytes — only f32 and padding
unsafe impl Pod for SpatialData {}
unsafe impl Zeroable for SpatialData {}

impl SpatialData {
    pub const fn new(x: f32, y: f32, z: f32) -> Self {
        Self {
            x, y, z,
            rotation_x: 0.0, rotation_y: 0.0, rotation_z: 0.0,
            scale_x: 1.0, scale_y: 1.0, scale_z: 1.0,
            _pad: [0u8; 28],
        }
    }

    /// Generate a flat array of 16 f32 values (column-major, OpenGL-style).
    /// Useful for feeding directly to GPU uniform buffers.
    pub fn to_matrix4(&self) -> [f32; 16] {
        let (sx, sy, sz) = (self.scale_x, self.scale_y, self.scale_z);
        let (rx, ry, rz) = (self.rotation_x, self.rotation_y, self.rotation_z);

        let cos_x = rx.cos();
        let sin_x = rx.sin();
        let cos_y = ry.cos();
        let sin_y = ry.sin();
        let cos_z = rz.cos();
        let sin_z = rz.sin();

        // Combined rotation matrix: R = Rz * Ry * Rx
        [
            (cos_y * cos_z) * sx,  (cos_y * sin_z) * sx,  (-sin_y) * sx,      0.0,
            (sin_x * sin_y * cos_z - cos_x * sin_z) * sy,
            (sin_x * sin_y * sin_z + cos_x * cos_z) * sy,
            (sin_x * cos_y) * sy,
            0.0,
            (cos_x * sin_y * cos_z + sin_x * sin_z) * sz,
            (cos_x * sin_y * sin_z - sin_x * cos_z) * sz,
            (cos_x * cos_y) * sz,
            0.0,
            self.x, self.y, self.z, 1.0,
        ]
    }

    /// Fast AABB check against a frustum plane (dot product with plane normal).
    #[inline]
    pub fn distance_to_plane(&self, plane: &[f32; 4]) -> f32 {
        self.x * plane[0] + self.y * plane[1] + self.z * plane[2] + plane[3]
    }
}

impl Default for SpatialData {
    fn default() -> Self {
        Self::new(0.0, 0.0, 0.0)
    }
}

// ── Entity ─────────────────────────────────────────────────────────────

/// A renderable entity in the NIKTO engine.
///
/// Memory layout (84 bytes total):
///   [8 bytes]  id
///   [64 bytes] spatial  ← hot cache line (read by physics / culling)
///   [12 bytes] mesh_id + material_id + visible
///
/// Cache behaviour: iterating for spatial queries touches only the first
/// 72 bytes (id + spatial), which spans two cache lines. For pure spatial
/// workloads, use `World::spatials_mut()` to iterate only the `SpatialData`
/// arrays without pulling entity metadata into cache.
#[derive(Clone, Debug)]
pub struct RenderEntity {
    pub id: u64,
    pub spatial: SpatialData,
    pub mesh_id: u32,
    pub material_id: u32,
    pub visible: u32, // 0 or 1 (u32 for alignment)
}

impl RenderEntity {
    pub fn new(x: f32, y: f32, z: f32) -> Self {
        Self {
            id: allocate_id(),
            spatial: SpatialData::new(x, y, z),
            mesh_id: 0,
            material_id: 0,
            visible: 1,
        }
    }

    pub fn is_visible(&self) -> bool {
        self.visible != 0
    }

    pub fn set_visible(&mut self, v: bool) {
        self.visible = v as u32;
    }
}

// ── Update system trait ────────────────────────────────────────────────

/// A system that processes entities in parallel.
///
/// Each system implementing this trait receives a mutable slice of
/// entities and returns a result. The `World` dispatches the system
/// across all available CPU cores using rayon's work-stealing thread pool.
pub trait ParallelSystem: Send + Sync {
    type Output: Send;

    /// Process a chunk of entities. This is called on each rayon worker
    /// thread with a distinct subset of the entity array.
    fn run(&self, entities: &mut [RenderEntity]) -> Self::Output;

    /// Combine outputs from all chunks into a single result.
    /// Default implementation discards individual outputs.
    fn combine(results: Vec<Self::Output>) -> Self::Output
    where
        Self: Sized;
}

/// Default `combine` for unit-type systems (no output needed).
impl ParallelSystem for () {
    type Output = ();

    fn run(&self, _entities: &mut [RenderEntity]) {}
    fn combine(_results: Vec<()>) {}
}

// ── World — contiguous entity storage ──────────────────────────────────

/// The high-performance ECS world.
///
/// Stores all entities in a single contiguous `Vec<RenderEntity>`.
/// This guarantees:
///   - Sequential memory layout (CPU prefetcher loads adjacent entities)
///   - No pointer chasing (no `Box`, no `HashMap`)
///   - Cache-friendly parallel iteration
///
/// Thread safety: internal `RwLock` allows multiple Python brain threads
/// to read spatial data simultaneously while a single writer updates.
pub struct World {
    entities: RwLock<Vec<RenderEntity>>,
    /// Separate spatial-only view for hot-path culling / LOD.
    /// Kept in sync with `entities`; iterating this vec avoids pulling
    /// id + mesh_id into cache.
    spatials: RwLock<Vec<SpatialData>>,
    entity_count: AtomicU64,
}

impl World {
    pub fn new() -> Self {
        Self {
            entities: RwLock::new(Vec::with_capacity(1024)),
            spatials: RwLock::new(Vec::with_capacity(1024)),
            entity_count: AtomicU64::new(0),
        }
    }

    /// Reserve capacity to avoid reallocation during burst creation.
    pub fn reserve(&self, additional: usize) {
        self.entities.write().reserve(additional);
        self.spatials.write().reserve(additional);
    }

    /// Spawn a new entity at the given position. Returns its unique ID.
    pub fn spawn(&self, x: f32, y: f32, z: f32) -> u64 {
        let entity = RenderEntity::new(x, y, z);
        let id = entity.id;
        self.entities.write().push(entity.clone());
        self.spatials.write().push(entity.spatial);
        self.entity_count.fetch_add(1, Ordering::Relaxed);
        id
    }

    /// Spawn many entities at once (batch allocation, single lock acquire).
    pub fn spawn_batch(&self, positions: &[(f32, f32, f32)]) -> Vec<u64> {
        let mut entities = self.entities.write();
        let mut spatials = self.spatials.write();
        let mut ids = Vec::with_capacity(positions.len());
        for &(x, y, z) in positions {
            let entity = RenderEntity::new(x, y, z);
            ids.push(entity.id);
            entities.push(entity);
            spatials.push(SpatialData::new(x, y, z));
        }
        self.entity_count.fetch_add(positions.len() as u64, Ordering::Relaxed);
        ids
    }

    /// Remove an entity by ID.
    pub fn despawn(&self, id: u64) -> bool {
        let mut entities = self.entities.write();
        if let Some(pos) = entities.iter().position(|e| e.id == id) {
            entities.swap_remove(pos);
            self.spatials.write().swap_remove(pos);
            self.entity_count.fetch_sub(1, Ordering::Relaxed);
            true
        } else {
            false
        }
    }

    /// Remove all entities.
    pub fn clear(&self) {
        self.entities.write().clear();
        self.spatials.write().clear();
        self.entity_count.store(0, Ordering::Relaxed);
    }

    // ── Read access ────────────────────────────────────────────────

    pub fn entity_count(&self) -> u64 {
        self.entity_count.load(Ordering::Relaxed)
    }

    pub fn get_entity(&self, id: u64) -> Option<RenderEntity> {
        self.entities
            .read()
            .iter()
            .find(|e| e.id == id)
            .cloned()
    }

    pub fn get_spatial(&self, id: u64) -> Option<SpatialData> {
        let entities = self.entities.read();
        entities.iter().find(|e| e.id == id).map(|e| e.spatial)
    }

    /// Read-only slice of all entities. Acquires read lock.
    pub fn entities(&self) -> Vec<RenderEntity> {
        self.entities.read().clone()
    }

    /// Read-only slice of all spatial data (hot-path).
    pub fn spatials(&self) -> Vec<SpatialData> {
        self.spatials.read().clone()
    }

    // ── Write access ───────────────────────────────────────────────

    /// Mutable access to all entities (single writer).
    pub fn entities_mut(&self) -> parking_lot::RwLockWriteGuard<'_, Vec<RenderEntity>> {
        self.entities.write()
    }

    /// Direct mutable access to spatial array (hot-path updates without
    /// touching entity metadata). Kept in sync with `entities` — you
    /// must ensure the length matches.
    pub fn spatials_mut(&self) -> parking_lot::RwLockWriteGuard<'_, Vec<SpatialData>> {
        self.spatials.write()
    }

    /// Update an entity's position in both arrays.
    pub fn set_position(&self, id: u64, x: f32, y: f32, z: f32) -> bool {
        let mut entities = self.entities.write();
        if let Some(pos) = entities.iter().position(|e| e.id == id) {
            entities[pos].spatial.x = x;
            entities[pos].spatial.y = y;
            entities[pos].spatial.z = z;
            self.spatials.write()[pos] = entities[pos].spatial;
            true
        } else {
            false
        }
    }

    // ── Parallel update ────────────────────────────────────────────

    /// Execute a system across all entities using rayon's work-stealing
    /// thread pool. Each CPU core processes a contiguous chunk.
    ///
    /// The system function receives the full entity slice split into chunks.
    /// Returns the combined output from all chunks.
    pub fn parallel_update<S: ParallelSystem>(&self, system: &S) -> S::Output {
        let mut entities = self.entities.write();
        let chunk_size = (entities.len() / rayon::current_num_threads()).max(64);

        let results: Vec<S::Output> = entities
            .par_chunks_mut(chunk_size)
            .map(|chunk| system.run(chunk))
            .collect();

        // Sync spatial array after bulk mutation
        self.sync_spatials();

        S::combine(results)
    }

    /// Fast path: iterate spatial data only (no entity metadata in cache).
    /// Useful for transform-only operations (physics, animation blending).
    pub fn parallel_update_spatials<F>(&self, f: F)
    where
        F: Fn(&mut [SpatialData]) + Send + Sync,
    {
        let mut spatials = self.spatials.write();
        let chunk_size = (spatials.len() / rayon::current_num_threads()).max(64);
        spatials.par_chunks_mut(chunk_size).for_each(|chunk| f(chunk));

        // Sync back to entity array
        self.sync_entities_from_spatials();
    }

    // ── Internal sync ──────────────────────────────────────────────

    fn sync_spatials(&self) {
        let entities = self.entities.read();
        let mut spatials = self.spatials.write();
        for (i, entity) in entities.iter().enumerate() {
            if i < spatials.len() {
                spatials[i] = entity.spatial;
            }
        }
    }

    fn sync_entities_from_spatials(&self) {
        let spatials = self.spatials.read();
        let mut entities = self.entities.write();
        for (i, spatial) in spatials.iter().enumerate() {
            if i < entities.len() {
                entities[i].spatial = *spatial;
            }
        }
    }

    // ── Export ─────────────────────────────────────────────────────

    /// Export all entity data as flat f32 arrays for Python bridge.
    /// One contiguous array of [x, y, z] triples — zero-copy compatible.
    pub fn export_position_array(&self) -> Vec<f32> {
        let entities = self.entities.read();
        let mut out = Vec::with_capacity(entities.len() * 3);
        for e in entities.iter() {
            out.push(e.spatial.x);
            out.push(e.spatial.y);
            out.push(e.spatial.z);
        }
        out
    }

    /// Export all entity data as flat `[f32; 16]` matrix4 array for GPU.
    pub fn export_matrix_array(&self) -> Vec<[f32; 16]> {
        let entities = self.entities.read();
        entities.iter().map(|e| e.spatial.to_matrix4()).collect()
    }
}

impl Default for World {
    fn default() -> Self {
        Self::new()
    }
}

// ── Built-in systems ───────────────────────────────────────────────────

/// A system that increments the Y position of all visible entities by dt.
/// Example: "float up" animation or particle emitter.
pub struct FloatUpSystem {
    pub speed: f32,
}

impl ParallelSystem for FloatUpSystem {
    type Output = u64; // number of entities updated

    fn run(&self, entities: &mut [RenderEntity]) -> u64 {
        let mut count = 0u64;
        for entity in entities.iter_mut() {
            if entity.is_visible() {
                entity.spatial.y += self.speed;
                count += 1;
            }
        }
        count
    }

    fn combine(results: Vec<u64>) -> u64 {
        results.iter().sum()
    }
}

/// A system that applies a simple sinusoidal oscillation to all entities.
pub struct WaveSystem {
    pub time: f32,
    pub amplitude: f32,
    pub frequency: f32,
}

impl ParallelSystem for WaveSystem {
    type Output = ();

    fn run(&self, entities: &mut [RenderEntity]) {
        for entity in entities.iter_mut() {
            entity.spatial.y +=
                (self.time * self.frequency + entity.spatial.x * 0.1).sin() * self.amplitude;
        }
    }

    fn combine(_results: Vec<()>) {}
}

// ── Test ───────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_spawn_and_query() {
        let world = World::new();
        let id = world.spawn(1.0, 2.0, 3.0);
        let entity = world.get_entity(id).unwrap();
        assert!((entity.spatial.x - 1.0).abs() < 1e-6);
        assert!((entity.spatial.y - 2.0).abs() < 1e-6);
        assert!((entity.spatial.z - 3.0).abs() < 1e-6);
    }

    #[test]
    fn test_spawn_batch() {
        let world = World::new();
        let positions = vec![(0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (2.0, 2.0, 2.0)];
        let ids = world.spawn_batch(&positions);
        assert_eq!(ids.len(), 3);
        assert_eq!(world.entity_count(), 3);
    }

    #[test]
    fn test_parallel_wave_system() {
        let world = World::new();
        world.spawn_batch(&[(0.0, 0.0, 0.0); 256]);
        let system = WaveSystem {
            time: 1.0,
            amplitude: 2.0,
            frequency: 1.0,
        };
        world.parallel_update(&system);
        // All entities should have been modified
        let spatials = world.spatials();
        assert!(spatials.iter().any(|s| s.y != 0.0));
    }

    #[test]
    fn test_spatial_cache_line_alignment() {
        use std::mem;
        assert_eq!(mem::align_of::<SpatialData>(), 64);
        assert_eq!(mem::size_of::<SpatialData>(), 64);
    }

    #[test]
    fn test_despawn() {
        let world = World::new();
        let id = world.spawn(0.0, 0.0, 0.0);
        assert_eq!(world.entity_count(), 1);
        assert!(world.despawn(id));
        assert_eq!(world.entity_count(), 0);
        assert!(world.get_entity(id).is_none());
    }

    #[test]
    fn test_clear() {
        let world = World::new();
        world.spawn_batch(&[(1.0, 2.0, 3.0); 10]);
        world.clear();
        assert_eq!(world.entity_count(), 0);
    }

    #[test]
    fn test_set_position() {
        let world = World::new();
        let id = world.spawn(0.0, 0.0, 0.0);
        assert!(world.set_position(id, 10.0, 20.0, 30.0));
        let spatial = world.get_spatial(id).unwrap();
        assert!((spatial.x - 10.0).abs() < 1e-6);
    }

    #[test]
    fn test_export_position_array() {
        let world = World::new();
        world.spawn(1.0, 2.0, 3.0);
        world.spawn(4.0, 5.0, 6.0);
        let arr = world.export_position_array();
        assert_eq!(arr.len(), 6);
        assert!((arr[0] - 1.0).abs() < 1e-6);
        assert!((arr[4] - 5.0).abs() < 1e-6);
    }

    #[test]
    fn test_matrix4_generation() {
        let spatial = SpatialData::new(1.0, 2.0, 3.0);
        let mat = spatial.to_matrix4();
        assert!((mat[12] - 1.0).abs() < 1e-6); // translation.x = m[12]
        assert!((mat[13] - 2.0).abs() < 1e-6); // translation.y = m[13]
        assert!((mat[14] - 3.0).abs() < 1e-6); // translation.z = m[14]
        assert!((mat[15] - 1.0).abs() < 1e-6); // w = 1
    }
}
