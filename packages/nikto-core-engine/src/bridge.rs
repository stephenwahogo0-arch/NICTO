/// PyO3 bridge — exports all engine layers to Python.
///
/// ECS (ecs.rs) → data
/// World gen (world_gen.rs) → procedural content
/// Scene (scene.rs) → scene graph + camera + lights
/// Renderer (renderer.rs) → wgpu GPU pipeline
use numpy::{PyArray1, PyReadonlyArray1, PyReadonlyArray3};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::ecs::{FloatUpSystem, WaveSystem, World};
use crate::renderer::{RenderCommand, RenderEngine};
use crate::scene::MeshData;
use crate::world_gen::{CoordinatePayload, VoxelPayload, WorldGenerator};

impl From<crate::world_gen::GenError> for PyErr {
    fn from(err: crate::world_gen::GenError) -> Self {
        PyValueError::new_err(err.to_string())
    }
}

#[pyclass(name = "NiktoEngine", unsendable)]
pub struct NiktoEngine {
    world: World,
    generator: WorldGenerator,
    renderer: RenderEngine,
}

#[pymethods]
impl NiktoEngine {
    #[new]
    pub fn new(chunk_size: Option<u32>, generate_mesh: Option<bool>) -> Self {
        Self {
            world: World::new(),
            generator: WorldGenerator {
                chunk_size: chunk_size.unwrap_or(16),
                generate_mesh: generate_mesh.unwrap_or(true),
            },
            renderer: RenderEngine::new(),
        }
    }

    // ── ECS entity management ──────────────────────────────────────

    pub fn spawn(&self, x: f32, y: f32, z: f32) -> u64 { self.world.spawn(x, y, z) }

    pub fn spawn_batch(&self, positions: Vec<Vec<f32>>) -> Vec<u64> {
        let tuples: Vec<(f32, f32, f32)> = positions.iter().map(|p| {
            (p.first().copied().unwrap_or(0.0), p.get(1).copied().unwrap_or(0.0), p.get(2).copied().unwrap_or(0.0))
        }).collect();
        self.world.spawn_batch(&tuples)
    }

    pub fn despawn(&self, id: u64) -> bool { self.world.despawn(id) }
    pub fn clear(&self) { self.world.clear(); }
    pub fn entity_count(&self) -> u64 { self.world.entity_count() }

    pub fn get_positions<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<f32>> {
        PyArray1::from_vec(py, &self.world.export_position_array())
    }

    pub fn get_matrices<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<f32>> {
        let flat: Vec<f32> = self.world.export_matrix_array().into_iter().flatten().collect();
        PyArray1::from_vec(py, &flat)
    }

    pub fn set_position(&self, id: u64, x: f32, y: f32, z: f32) -> bool { self.world.set_position(id, x, y, z) }

    // ── Procedural world generation ────────────────────────────────

    pub fn ingest_voxels(&mut self, voxels: PyReadonlyArray3<u32>) -> PyResult<(usize, usize, usize)> {
        let array = voxels.as_array();
        let dims = array.shape();
        let (height, depth, width) = (dims[0], dims[1], dims[2]);
        let flat: Vec<u32> = array.iter().copied().collect();
        let payload = VoxelPayload::new(width as u32, height as u32, depth as u32, flat)?;
        let (spawned, geo) = self.generator.ingest_voxels(&self.world, &payload)?;
        Ok((spawned, geo.vertex_buffer.len() / 8, geo.index_buffer.len()))
    }

    pub fn ingest_voxels_parallel(&mut self, voxels: PyReadonlyArray3<u32>) -> PyResult<(usize, usize, usize)> {
        let array = voxels.as_array();
        let dims = array.shape();
        let (height, depth, width) = (dims[0], dims[1], dims[2]);
        let flat: Vec<u32> = array.iter().copied().collect();
        let payload = VoxelPayload::new(width as u32, height as u32, depth as u32, flat)?;
        let (spawned, geo) = self.generator.ingest_voxels_parallel(&self.world, &payload)?;
        Ok((spawned, geo.vertex_buffer.len() / 8, geo.index_buffer.len()))
    }

    pub fn ingest_coordinates(&mut self, coords: PyReadonlyArray1<f32>) -> PyResult<Vec<u64>> {
        let raw: Vec<f32> = coords.as_array().iter().copied().collect();
        let payload = CoordinatePayload::new(raw)?;
        Ok(self.generator.ingest_coordinates(&self.world, &payload))
    }

    // ── Parallel systems ───────────────────────────────────────────

    pub fn apply_wave(&self, time: f32, amplitude: f32, frequency: f32) {
        self.world.parallel_update(&WaveSystem { time, amplitude, frequency });
    }

    pub fn apply_float(&self, speed: f32) -> u64 {
        self.world.parallel_update(&FloatUpSystem { speed })
    }

    // ── GPU Rendering ──────────────────────────────────────────────

    /// Open a 3D render window powered by wgpu (Vulkan/DX12/Metal).
    pub fn start_window(&mut self, width: u32, height: u32, title: String) {
        self.renderer.start(width, height, &title);
    }

    /// Close the render window.
    pub fn close_window(&mut self) {
        self.renderer.stop();
    }

    /// True if the render window is open.
    pub fn is_window_open(&self) -> bool {
        self.renderer.is_running()
    }

    /// Set the 3D camera position and target.
    pub fn set_camera(&self, x: f32, y: f32, z: f32, tx: f32, ty: f32, tz: f32) {
        self.renderer.send(RenderCommand::SetCamera { x, y, z, tx, ty, tz });
    }

    /// Add a mesh from vertex/interleaved data. Returns mesh index.
    pub fn add_mesh(&self, vertices: Vec<f32>, indices: Vec<u32>) {
        self.renderer.send(RenderCommand::AddMesh { vertices, indices });
    }

    /// Spawn a mesh instance in the 3D scene at (x, y, z).
    pub fn spawn_mesh(&self, mesh_idx: usize, x: f32, y: f32, z: f32) {
        self.renderer.send(RenderCommand::SpawnEntity { mesh_idx, x, y, z });
    }

    /// Update a spawned entity's position.
    pub fn update_entity_position(&self, index: usize, x: f32, y: f32, z: f32) {
        self.renderer.send(RenderCommand::UpdateEntityPosition { index, x, y, z });
    }

    /// Quick-start: spawn a cube grid directly from Python.
    pub fn demo_cubes(&self, count: u32, spacing: f32) {
        let mesh = MeshData::cube(0.0, 0.0, 0.0);
        self.renderer.send(RenderCommand::AddMesh { vertices: mesh.vertices, indices: mesh.indices });
        let half = (count / 2) as f32 * spacing;
        for z in 0..count {
            for y in 0..count {
                for x in 0..count {
                    let px = x as f32 * spacing - half;
                    let py = y as f32 * spacing - half;
                    let pz = z as f32 * spacing - half;
                    self.renderer.send(RenderCommand::SpawnEntity { mesh_idx: 0, x: px, y: py, z: pz });
                }
            }
        }
    }

    // ── Engine info ────────────────────────────────────────────────

    pub fn info(&self) -> PyResult<Vec<(String, String)>> {
        Ok(vec![
            ("engine".into(), "nikto-core-engine".into()),
            ("version".into(), env!("CARGO_PKG_VERSION").into()),
            ("entity_count".into(), self.world.entity_count().to_string()),
            ("parallel_workers".into(), rayon::current_num_threads().to_string()),
            ("renderer".into(), if self.renderer.is_running() { "wgpu" } else { "idle" }.into()),
        ])
    }

    pub fn reserve(&self, additional: usize) { self.world.reserve(additional); }
}
