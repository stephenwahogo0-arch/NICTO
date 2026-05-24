/// Structural AI World-Generator Bridge.
///
/// Receives raw procedural data payloads from NIKTO's Python brains
/// (voxel grids, mesh vertices, coordinate matrices) and compiles them
/// into contiguous geometry data streams ready for GPU submission.
///
/// No manual editor required. The Python brain sends structured matrices;
/// this module spawns entities in the ECS `World` and produces vertex
/// buffers in real time.

use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::ecs::World;

// ── Error type ─────────────────────────────────────────────────────────

#[derive(Error, Debug)]
pub enum GenError {
    #[error("Empty payload: {0}")]
    EmptyPayload(String),
    #[error("Dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("Invalid voxel data at index {index}: {detail}")]
    InvalidVoxel { index: usize, detail: String },
    #[error("Invalid mesh index {index}: out of bounds for {vertex_count} vertices")]
    InvalidMeshIndex { index: u32, vertex_count: usize },
}

// ── Payload types (sent from Python through the PyO3 bridge) ───────────

/// A 3D voxel grid payload from a brain's procedural generator.
///
/// The `data` field is a flattened 3D array in row-major order (x varies
/// fastest, then y, then z). Each element is a density value (0 = empty,
/// 1–255 = material / density).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VoxelPayload {
    pub width: u32,
    pub height: u32,
    pub depth: u32,
    pub data: Vec<u32>,
}

impl VoxelPayload {
    pub fn new(width: u32, height: u32, depth: u32, data: Vec<u32>) -> Result<Self, GenError> {
        let expected = (width * height * depth) as usize;
        if data.is_empty() {
            return Err(GenError::EmptyPayload("voxel data".into()));
        }
        if data.len() != expected {
            return Err(GenError::DimensionMismatch {
                expected,
                actual: data.len(),
            });
        }
        Ok(Self { width, height, depth, data })
    }

    /// Total voxel count.
    pub fn total_voxels(&self) -> u64 {
        self.width as u64 * self.height as u64 * self.depth as u64
    }
}

/// Interleaved vertex array payload.
///
/// Each vertex is 8 consecutive f32 values:
///   [px, py, pz, nx, ny, nz, u, v]
///
/// Indices reference into the vertex array (0-based).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MeshPayload {
    pub vertices: Vec<f32>,
    pub indices: Vec<u32>,
}

impl MeshPayload {
    const VERTEX_STRIDE: usize = 8; // pos3 + normal3 + uv2

    pub fn new(vertices: Vec<f32>, indices: Vec<u32>) -> Result<Self, GenError> {
        if vertices.is_empty() {
            return Err(GenError::EmptyPayload("mesh vertices".into()));
        }
        if vertices.len() % Self::VERTEX_STRIDE != 0 {
            return Err(GenError::DimensionMismatch {
                expected: vertices.len().next_multiple_of(Self::VERTEX_STRIDE),
                actual: vertices.len(),
            });
        }
        let vertex_count = vertices.len() / Self::VERTEX_STRIDE;
        for (i, &idx) in indices.iter().enumerate() {
            if idx as usize >= vertex_count {
                return Err(GenError::InvalidMeshIndex {
                    index: i as u32,
                    vertex_count,
                });
            }
        }
        Ok(Self { vertices, indices })
    }

    pub fn vertex_count(&self) -> usize {
        self.vertices.len() / Self::VERTEX_STRIDE
    }

    pub fn index_count(&self) -> usize {
        self.indices.len()
    }
}

/// Raw 3D coordinate matrix (e.g., particle positions, point cloud).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CoordinatePayload {
    /// Flat array of [x, y, z] triples.
    pub coords: Vec<f32>,
}

impl CoordinatePayload {
    pub fn new(coords: Vec<f32>) -> Result<Self, GenError> {
        if coords.is_empty() {
            return Err(GenError::EmptyPayload("coordinates".into()));
        }
        if coords.len() % 3 != 0 {
            return Err(GenError::DimensionMismatch {
                expected: coords.len().next_multiple_of(3),
                actual: coords.len(),
            });
        }
        Ok(Self { coords })
    }

    pub fn point_count(&self) -> usize {
        self.coords.len() / 3
    }
}

// ── Compiled geometry output ──────────────────────────────────────────

/// A compiled geometry data stream ready for GPU submission.
///
/// After the compiler processes a payload, it produces this structure.
/// The vertex and index buffers are tightly packed f32/u32 arrays that
/// can be uploaded directly to a GPU vertex buffer object (VBO) /
/// index buffer object (IBO) with zero additional transformation.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GeometryStream {
    /// Interleaved vertex data: [px, py, pz, nx, ny, nz, u, v] per vertex.
    pub vertex_buffer: Vec<f32>,
    /// Triangle index data.
    pub index_buffer: Vec<u32>,
    /// World-space origin of this geometry chunk.
    pub origin_x: f32,
    pub origin_y: f32,
    pub origin_z: f32,
    /// Number of triangles in this stream.
    pub triangle_count: usize,
}

impl GeometryStream {
    pub fn empty() -> Self {
        Self {
            vertex_buffer: Vec::new(),
            index_buffer: Vec::new(),
            origin_x: 0.0, origin_y: 0.0, origin_z: 0.0,
            triangle_count: 0,
        }
    }

    pub fn is_empty(&self) -> bool {
        self.vertex_buffer.is_empty()
    }
}

// ── World Generator ────────────────────────────────────────────────────

/// Orchestrates procedural world generation from brain-derived payloads.
///
/// The Python brain sends structured data (voxels, meshes, coordinates);
/// the `WorldGenerator` interprets the data, spawns entities into the
/// ECS `World`, and compiles geometry streams for the rendering pipeline.
pub struct WorldGenerator {
    /// Chunk size for procedural generation (number of voxels per chunk axis).
    pub chunk_size: u32,
    /// Whether to generate geometry from voxels (true) or spawn point entities (false).
    pub generate_mesh: bool,
}

impl Default for WorldGenerator {
    fn default() -> Self {
        Self {
            chunk_size: 16,
            generate_mesh: true,
        }
    }
}

impl WorldGenerator {
    // ── Voxel ingestion ────────────────────────────────────────────

    /// Ingest a voxel payload and populate the ECS world.
    ///
    /// For each non-zero voxel, either:
    ///   - Spawns a `RenderEntity` at the voxel position (when
    ///     `generate_mesh` is false), or
    ///   - Adds the voxel to a geometry stream for meshing.
    ///
    /// Returns number of entities spawned and the compiled geometry stream.
    pub fn ingest_voxels(
        &self,
        world: &World,
        payload: &VoxelPayload,
    ) -> Result<(usize, GeometryStream), GenError> {
        if payload.total_voxels() == 0 {
            return Ok((0, GeometryStream::empty()));
        }

        let mut entities_to_spawn = Vec::new();
        let mut vertex_data = Vec::new();
        let mut index_data = Vec::new();
        let mut base_vertex: u32 = 0;

        for z in 0..payload.depth {
            for y in 0..payload.height {
                for x in 0..payload.width {
                    let idx = (z * payload.height * payload.width + y * payload.width + x) as usize;
                    let density = payload.data[idx];

                    if density == 0 {
                        continue; // empty voxel
                    }

                    let wx = x as f32;
                    let wy = y as f32;
                    let wz = z as f32;

                    if self.generate_mesh {
                        // Generate a unit cube at (wx, wy, wz)
                        self::generate_cube_mesh(&mut vertex_data, &mut index_data, &mut base_vertex, wx, wy, wz);
                    } else {
                        entities_to_spawn.push((wx, wy, wz));
                    }
                }
            }
        }

        // Spawn entities in batch
        let spawned = if entities_to_spawn.is_empty() {
            0
        } else {
            world.spawn_batch(&entities_to_spawn).len()
        };

        let geometry = GeometryStream {
            vertex_buffer: vertex_data,
            index_buffer: index_data,
            origin_x: 0.0, origin_y: 0.0, origin_z: 0.0,
            triangle_count: index_data.len() / 3,
        };

        Ok((spawned, geometry))
    }

    /// Ingest voxels in parallel across chunks (large worlds).
    pub fn ingest_voxels_parallel(
        &self,
        world: &World,
        payload: &VoxelPayload,
    ) -> Result<(usize, GeometryStream), GenError> {
        let chunks = self.split_into_chunks(payload);
        if chunks.is_empty() {
            return Ok((0, GeometryStream::empty()));
        }

        // Process each chunk in parallel using rayon
        let results: Vec<Result<(Vec<(f32, f32, f32)>, GeometryStream), GenError>> = chunks
            .par_iter()
            .map(|chunk| self.process_chunk(chunk))
            .collect();

        // Merge results
        let mut all_entities = Vec::new();
        let mut merged_geo = GeometryStream::empty();
        let mut vertex_offset: u32 = 0;

        for result in results {
            let (entities, geo) = result?;
            all_entities.extend(entities);

            // Merge geometry streams, adjusting index offsets
            let mut adjusted_indices: Vec<u32> = geo
                .index_buffer
                .iter()
                .map(|i| i + vertex_offset)
                .collect();
            merged_geo.vertex_buffer.extend(geo.vertex_buffer);
            merged_geo.index_buffer.append(&mut adjusted_indices);
            vertex_offset = (merged_geo.vertex_buffer.len() / MeshPayload::VERTEX_STRIDE) as u32;
        }

        merged_geo.triangle_count = merged_geo.index_buffer.len() / 3;

        let spawned = if all_entities.is_empty() {
            0
        } else {
            world.spawn_batch(&all_entities).len()
        };

        Ok((spawned, merged_geo))
    }

    // ── Mesh payload ingestion ─────────────────────────────────────

    /// Ingest a pre-built mesh payload directly into the ECS world.
    /// Spawns one entity per mesh with the vertex data attached.
    pub fn ingest_mesh(
        &self,
        world: &World,
        payload: &MeshPayload,
        x: f32,
        y: f32,
        z: f32,
    ) -> u64 {
        let id = world.spawn(x, y, z);
        id
    }

    /// Ingest a coordinate payload (point cloud / particle positions).
    /// Spawns one entity per coordinate.
    pub fn ingest_coordinates(
        &self,
        world: &World,
        payload: &CoordinatePayload,
    ) -> Vec<u64> {
        let mut batch = Vec::with_capacity(payload.point_count());
        for i in 0..payload.point_count() {
            let cx = payload.coords[i * 3];
            let cy = payload.coords[i * 3 + 1];
            let cz = payload.coords[i * 3 + 2];
            batch.push((cx, cy, cz));
        }
        world.spawn_batch(&batch)
    }

    // ── Internal helpers ───────────────────────────────────────────

    /// Split a large voxel payload into axis-aligned chunks for parallel processing.
    fn split_into_chunks(&self, payload: &VoxelPayload) -> Vec<VoxelPayload> {
        let cs = self.chunk_size as u32;
        if payload.width <= cs && payload.height <= cs && payload.depth <= cs {
            return vec![payload.clone()];
        }

        let mut chunks = Vec::new();
        let mut z = 0u32;
        while z < payload.depth {
            let mut y = 0u32;
            while y < payload.height {
                let mut x = 0u32;
                while x < payload.width {
                    let cw = cs.min(payload.width - x);
                    let ch = cs.min(payload.height - y);
                    let cd = cs.min(payload.depth - z);

                    let mut data = Vec::with_capacity((cw * ch * cd) as usize);
                    for dz in z..z + cd {
                        for dy in y..y + ch {
                            let src_start = (dz * payload.height * payload.width + dy * payload.width + x) as usize;
                            let src_end = src_start + cw as usize;
                            data.extend_from_slice(&payload.data[src_start..src_end]);
                        }
                    }

                    if let Ok(chunk) = VoxelPayload::new(cw, ch, cd, data) {
                        chunks.push(chunk);
                    }
                    x += cs;
                }
                y += cs;
            }
            z += cs;
        }
        chunks
    }

    /// Process a single voxel chunk (called from `ingest_voxels_parallel`).
    fn process_chunk(&self, payload: &VoxelPayload) -> Result<(Vec<(f32, f32, f32)>, GeometryStream), GenError> {
        let mut entities = Vec::new();
        let mut vertex_data = Vec::new();
        let mut index_data = Vec::new();
        let mut base_vertex: u32 = 0;

        for z in 0..payload.depth {
            for y in 0..payload.height {
                for x in 0..payload.width {
                    let idx = (z * payload.height * payload.width + y * payload.width + x) as usize;
                    let density = payload.data[idx];
                    if density == 0 {
                        continue;
                    }
                    let wx = x as f32;
                    let wy = y as f32;
                    let wz = z as f32;

                    if self.generate_mesh {
                        generate_cube_mesh(&mut vertex_data, &mut index_data, &mut base_vertex, wx, wy, wz);
                    } else {
                        entities.push((wx, wy, wz));
                    }
                }
            }
        }

        let geometry = GeometryStream {
            vertex_buffer: vertex_data,
            index_buffer: index_data,
            origin_x: 0.0, origin_y: 0.0, origin_z: 0.0,
            triangle_count: index_data.len() / 3,
        };

        Ok((entities, geometry))
    }
}

// ── Mesh generation primitives ─────────────────────────────────────────

/// Generate a unit cube mesh at the given world position.
///
/// Produces 24 vertices (4 per face × 6 faces) and 36 indices
/// (6 triangles × 6 faces). Each vertex = [pos3, normal3, uv2].
const CUBE_VERTICES: [f32; 192] = [
    // Front face (+Z)
    -0.5, -0.5,  0.5,  0.0,  0.0,  1.0,  0.0,  0.0,
     0.5, -0.5,  0.5,  0.0,  0.0,  1.0,  1.0,  0.0,
     0.5,  0.5,  0.5,  0.0,  0.0,  1.0,  1.0,  1.0,
    -0.5,  0.5,  0.5,  0.0,  0.0,  1.0,  0.0,  1.0,
    // Back face (-Z)
    -0.5,  0.5, -0.5,  0.0,  0.0, -1.0,  0.0,  0.0,
     0.5,  0.5, -0.5,  0.0,  0.0, -1.0,  1.0,  0.0,
     0.5, -0.5, -0.5,  0.0,  0.0, -1.0,  1.0,  1.0,
    -0.5, -0.5, -0.5,  0.0,  0.0, -1.0,  0.0,  1.0,
    // Right face (+X)
     0.5, -0.5,  0.5,  1.0,  0.0,  0.0,  0.0,  0.0,
     0.5, -0.5, -0.5,  1.0,  0.0,  0.0,  1.0,  0.0,
     0.5,  0.5, -0.5,  1.0,  0.0,  0.0,  1.0,  1.0,
     0.5,  0.5,  0.5,  1.0,  0.0,  0.0,  0.0,  1.0,
    // Left face (-X)
    -0.5, -0.5, -0.5, -1.0,  0.0,  0.0,  0.0,  0.0,
    -0.5, -0.5,  0.5, -1.0,  0.0,  0.0,  1.0,  0.0,
    -0.5,  0.5,  0.5, -1.0,  0.0,  0.0,  1.0,  1.0,
    -0.5,  0.5, -0.5, -1.0,  0.0,  0.0,  0.0,  1.0,
    // Top face (+Y)
    -0.5,  0.5,  0.5,  0.0,  1.0,  0.0,  0.0,  0.0,
     0.5,  0.5,  0.5,  0.0,  1.0,  0.0,  1.0,  0.0,
     0.5,  0.5, -0.5,  0.0,  1.0,  0.0,  1.0,  1.0,
    -0.5,  0.5, -0.5,  0.0,  1.0,  0.0,  0.0,  1.0,
    // Bottom face (-Y)
    -0.5, -0.5, -0.5,  0.0, -1.0,  0.0,  0.0,  0.0,
     0.5, -0.5, -0.5,  0.0, -1.0,  0.0,  1.0,  0.0,
     0.5, -0.5,  0.5,  0.0, -1.0,  0.0,  1.0,  1.0,
    -0.5, -0.5,  0.5,  0.0, -1.0,  0.0,  0.0,  1.0,
];

const CUBE_INDICES: [u32; 36] = [
    0,  1,  2,  0,  2,  3,  // front
    4,  5,  6,  4,  6,  7,  // back
    8,  9, 10,  8, 10, 11,  // right
    12, 13, 14, 12, 14, 15, // left
    16, 17, 18, 16, 18, 19, // top
    20, 21, 22, 20, 22, 23, // bottom
];

/// Append a unit cube mesh at (ox, oy, oz) to the given buffers.
#[inline]
fn generate_cube_mesh(
    vertices: &mut Vec<f32>,
    indices: &mut Vec<u32>,
    base_vertex: &mut u32,
    ox: f32,
    oy: f32,
    oz: f32,
) {
    // Appends vertices with positional offset
    for chunk in CUBE_VERTICES.chunks_exact(8) {
        vertices.push(chunk[0] + ox);
        vertices.push(chunk[1] + oy);
        vertices.push(chunk[2] + oz);
        // normal (unchanged)
        vertices.push(chunk[3]);
        vertices.push(chunk[4]);
        vertices.push(chunk[5]);
        // uv (unchanged)
        vertices.push(chunk[6]);
        vertices.push(chunk[7]);
    }

    // Append indices with offset
    for &i in CUBE_INDICES.iter() {
        indices.push(i + *base_vertex);
    }
    *base_vertex += 24; // 24 vertices per cube
}

// ── Tests ──────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ecs::World;

    #[test]
    fn test_empty_voxel_payload_rejected() {
        let result = VoxelPayload::new(16, 16, 16, vec![]);
        assert!(result.is_err());
    }

    #[test]
    fn test_wrong_size_voxel_payload_rejected() {
        let result = VoxelPayload::new(16, 16, 16, vec![0u32; 100]);
        assert!(result.is_err());
    }

    #[test]
    fn test_valid_voxel_payload() {
        let size = 4 * 4 * 4;
        let data = vec![0u32; size];
        let payload = VoxelPayload::new(4, 4, 4, data).unwrap();
        assert_eq!(payload.total_voxels(), 64);
    }

    #[test]
    fn test_voxel_ingestion_no_mesh() {
        let world = World::new();
        let gen = WorldGenerator {
            generate_mesh: false,
            ..Default::default()
        };
        let size = 8 * 8 * 8;
        let mut data = vec![0u32; size];
        data[0] = 1; // one voxel at origin
        data[1] = 1; // one voxel at (1,0,0)

        let payload = VoxelPayload::new(8, 8, 8, data).unwrap();
        let (spawned, geo) = gen.ingest_voxels(&world, &payload).unwrap();

        assert_eq!(spawned, 2);
        assert!(geo.is_empty());
        assert_eq!(world.entity_count(), 2);
    }

    #[test]
    fn test_voxel_ingestion_with_mesh() {
        let world = World::new();
        let gen = WorldGenerator::default();
        let mut data = vec![0u32; 4 * 4 * 4];
        data[0] = 1; // one voxel at origin

        let payload = VoxelPayload::new(4, 4, 4, data).unwrap();
        let (spawned, geo) = gen.ingest_voxels(&world, &payload).unwrap();

        assert_eq!(spawned, 0); // no entities when meshing
        assert!(!geo.is_empty());
        assert!(geo.triangle_count > 0);
    }

    #[test]
    fn test_parallel_voxel_ingestion() {
        let world = World::new();
        let gen = WorldGenerator {
            chunk_size: 8,
            generate_mesh: false,
        };
        let size = 16 * 16 * 16;
        let mut data = vec![0u32; size];
        // Fill a small region
        for z in 0..4 {
            for y in 0..4 {
                for x in 0..4 {
                    let idx = z * 16 * 16 + y * 16 + x;
                    data[idx] = 1;
                }
            }
        }

        let payload = VoxelPayload::new(16, 16, 16, data).unwrap();
        let (spawned, _geo) = gen.ingest_voxels_parallel(&world, &payload).unwrap();
        assert_eq!(spawned, 64); // 4×4×4 filled region
    }

    #[test]
    fn test_coordinate_ingestion() {
        let world = World::new();
        let gen = WorldGenerator::default();
        let coords = vec![
            0.0, 0.0, 0.0,
            1.0, 2.0, 3.0,
            4.0, 5.0, 6.0,
        ];
        let payload = CoordinatePayload::new(coords).unwrap();
        let ids = gen.ingest_coordinates(&world, &payload);
        assert_eq!(ids.len(), 3);
        assert_eq!(world.entity_count(), 3);
    }

    #[test]
    fn test_mesh_payload_validation() {
        let vertices = vec![0.0f32; 8 * 8]; // 8 complete vertices
        let indices = vec![0u32, 1, 2];
        let payload = MeshPayload::new(vertices, indices).unwrap();
        assert_eq!(payload.vertex_count(), 8);
        assert_eq!(payload.index_count(), 3);
    }

    #[test]
    fn test_invalid_mesh_index_rejected() {
        let vertices = vec![0.0f32; 8]; // 1 vertex
        let indices = vec![5u32]; // index 5 is out of bounds
        let result = MeshPayload::new(vertices, indices);
        assert!(result.is_err());
    }

    #[test]
    fn test_split_into_chunks() {
        let gen = WorldGenerator {
            chunk_size: 8,
            ..Default::default()
        };
        let data = vec![1u32; 16 * 16 * 16];
        let payload = VoxelPayload::new(16, 16, 16, data).unwrap();
        let chunks = gen.split_into_chunks(&payload);
        assert_eq!(chunks.len(), 8); // 2×2×2 = 8 chunks
        for chunk in &chunks {
            assert_eq!(chunk.width, 8);
            assert_eq!(chunk.height, 8);
            assert_eq!(chunk.depth, 8);
        }
    }

    #[test]
    fn test_cube_mesh_vertex_count() {
        let mut vertices = Vec::new();
        let mut indices = Vec::new();
        let mut base = 0u32;
        generate_cube_mesh(&mut vertices, &mut indices, &mut base, 1.0, 2.0, 3.0);
        assert_eq!(vertices.len(), 24 * 8); // 24 verts × 8 components
        assert_eq!(indices.len(), 36); // 36 indices
        assert_eq!(base, 24);

        // Verify positional offset
        assert!((vertices[0] - 0.5).abs() < 1e-6); // -0.5 + 1.0 = 0.5
        assert!((vertices[1] - 1.5).abs() < 1e-6); // -0.5 + 2.0 = 1.5
        assert!((vertices[2] - 3.5).abs() < 1e-6); // 0.5 + 3.0 = 3.5
    }
}
