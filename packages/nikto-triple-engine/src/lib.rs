/// NIKTO Triple-Engine — Master System Orchestrator & Python Bridge (Rust)
///
/// Orchestrates the Zig memory layer and Mojo physics kernel into a single
/// PyO3-native binary module. Connects Python's multi-processed brains to
/// the C-ABI cluster via extern "C" linkage.
///
/// Memory ownership chain:
///   Zig owns the linear arena         (spatial_memory.zig)
///   Mojo reads/writes entities in situ (physics_core.mojo)
///   Rust orchestrates + bridges to Py  (this file)
///   Python receives numpy arrays       (no-copy via pointer)
///
/// Build:
///   cargo build --release  (build.rs handles Zig + Mojo compilation)

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyList;

use std::ffi::{c_double, c_float, c_int, c_uint, c_ulonglong, c_void, c_uchar};

// ── SpatialEntity (mirrors Zig layout exactly) ─────────────────────────

/// Must be byte-for-byte identical to `spatial_memory.zig:SpatialEntity`.
#[repr(C, align(64))]
#[derive(Clone, Debug)]
pub struct SpatialEntity {
    pub id: u64,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub vx: f32,
    pub vy: f32,
    pub vz: f32,
    _pad: [u8; 32],
}

const _: () = assert!(std::mem::size_of::<SpatialEntity>() == 64);

// ── Zig C-ABI bindings (spatial_memory.zig) ────────────────────────────

#[link(name = "spatial_memory")]
extern "C" {
    fn spatial_init();
    fn spatial_get_base() -> *mut c_void;
    fn spatial_spawn(x: c_float, y: c_float, z: c_float) -> c_ulonglong;
    fn spatial_spawn_batch(coords: *const c_float, count: c_ulonglong) -> c_ulonglong;
    fn spatial_count() -> c_ulonglong;
    fn spatial_capacity() -> c_ulonglong;
    fn spatial_get_id(index: c_ulonglong) -> c_ulonglong;
    fn spatial_get_position(index: c_ulonglong, out: *mut c_float) -> c_uchar;
    fn spatial_set_position(index: c_ulonglong, x: c_float, y: c_float, z: c_float) -> c_uchar;
    fn spatial_set_velocity(index: c_ulonglong, vx: c_float, vy: c_float, vz: c_float) -> c_uchar;
    fn spatial_reset();
    fn spatial_export_positions(out: *mut c_float) -> c_ulonglong;
}

// ── Mojo C-ABI bindings (physics_core.mojo) ────────────────────────────

#[link(name = "physics_core")]
extern "C" {
    fn physics_init();
    fn physics_update(
        ptr: *mut SpatialEntity,
        count: usize,
        dt: c_float,
        gravity: c_float,
        time: c_float,
    ) -> usize;
    fn physics_center_of_mass(ptr: *mut SpatialEntity, count: usize, out: *mut c_float);
    fn physics_detect_collisions(
        ptr: *mut SpatialEntity,
        count: usize,
        radius: c_float,
    ) -> usize;
}

// ── NiktoTripleEngine PyClass ──────────────────────────────────────────

/// High-performance 3D engine bridging Zig (memory) + Mojo (physics) + Rust (orchestration).
///
/// Instantiate from Python:
/// ```python
/// from nikto_triple_engine import NiktoTripleEngine
/// engine = NiktoTripleEngine()
/// engine.spawn_batch([[0,0,0], [10,0,0]])
/// engine.update_physics(dt=0.016)
/// positions = engine.get_positions()
/// ```
#[pyclass(name = "NiktoTripleEngine")]
pub struct NiktoTripleEngine {
    initialized: bool,
}

#[pymethods]
impl NiktoTripleEngine {
    #[new]
    pub fn new() -> PyResult<Self> {
        let engine = Self { initialized: false };
        engine.init_native()?;
        Ok(engine)
    }

    fn init_native(&self) -> PyResult<()> {
        if self.initialized {
            return Ok(());
        }
        unsafe {
            spatial_init();
            physics_init();
        }
        Ok(())
    }

    // ── Entity lifecycle ───────────────────────────────────────────

    /// Spawn a single entity at (x, y, z). Returns its unique ID.
    pub fn spawn(&self, x: f32, y: f32, z: f32) -> PyResult<u64> {
        let id = unsafe { spatial_spawn(x, y, z) };
        if id == 0 {
            return Err(PyRuntimeError::new_err("Entity arena full"));
        }
        Ok(id)
    }

    /// Spawn multiple entities from a list of [x, y, z] triples.
    pub fn spawn_batch(&self, positions: Vec<Vec<f32>>) -> PyResult<Vec<u64>> {
        if positions.is_empty() {
            return Ok(Vec::new());
        }
        let mut flat = Vec::with_capacity(positions.len() * 3);
        for p in &positions {
            flat.push(p.first().copied().unwrap_or(0.0));
            flat.push(p.get(1).copied().unwrap_or(0.0));
            flat.push(p.get(2).copied().unwrap_or(0.0));
        }
        let spawned = unsafe { spatial_spawn_batch(flat.as_ptr(), flat.len() as u64 / 3) };
        if spawned == 0 {
            return Err(PyRuntimeError::new_err("Failed to spawn batch"));
        }
        // Retrieve IDs of spawned entities
        let count = unsafe { spatial_count() };
        let mut ids = Vec::with_capacity(spawned as usize);
        for i in (count - spawned)..count {
            ids.push(unsafe { spatial_get_id(i) });
        }
        Ok(ids)
    }

    /// Remove all entities.
    pub fn clear(&self) {
        unsafe { spatial_reset(); }
    }

    /// Current entity count.
    #[getter]
    pub fn entity_count(&self) -> u64 {
        unsafe { spatial_count() }
    }

    /// Maximum entity capacity.
    #[getter]
    pub fn capacity(&self) -> u64 {
        unsafe { spatial_capacity() }
    }

    // ── Physics ────────────────────────────────────────────────────

    /// Run one physics simulation tick on all entities.
    ///
    /// Args:
    ///     dt: Delta time in seconds (default 0.016 ≈ 60 FPS).
    ///     gravity: Gravitational acceleration (default 9.81).
    ///     time: Current simulation time for wave offset.
    pub fn update_physics(
        &self,
        dt: Option<f32>,
        gravity: Option<f32>,
        time: Option<f32>,
    ) -> PyResult<usize> {
        let count = unsafe { spatial_count() } as usize;
        if count == 0 {
            return Ok(0);
        }
        let ptr = unsafe { spatial_get_base() as *mut SpatialEntity };
        let processed = unsafe {
            physics_update(
                ptr,
                count,
                dt.unwrap_or(0.016),
                gravity.unwrap_or(9.81),
                time.unwrap_or(0.0),
            )
        };
        Ok(processed)
    }

    /// Detect and resolve collisions between entities within `radius`.
    pub fn detect_collisions(&self, radius: f32) -> PyResult<usize> {
        let count = unsafe { spatial_count() } as usize;
        if count == 0 {
            return Ok(0);
        }
        let ptr = unsafe { spatial_get_base() as *mut SpatialEntity };
        Ok(unsafe { physics_detect_collisions(ptr, count, radius) })
    }

    // ── Position queries ───────────────────────────────────────────

    /// Export all entity positions as flat f32 Vec for Python conversion.
    pub fn get_positions_native(&self) -> PyResult<Vec<f32>> {
        let count = unsafe { spatial_count() } as usize;
        if count == 0 {
            return Ok(Vec::new());
        }
        let mut out = vec![0.0f32; count * 3];
        let written = unsafe { spatial_export_positions(out.as_mut_ptr()) };
        out.truncate((written as usize) * 3);
        Ok(out)
    }

    /// Get positions as a list of [x, y, z] triples (for Python without numpy).
    pub fn get_positions_list(&self) -> PyResult<Vec<Vec<f32>>> {
        let flat = self.get_positions_native()?;
        let mut list = Vec::with_capacity(flat.len() / 3);
        for chunk in flat.chunks_exact(3) {
            list.push(vec![chunk[0], chunk[1], chunk[2]]);
        }
        Ok(list)
    }

    /// Get the position of a single entity by index.
    /// Returns None if index out of range.
    pub fn get_position(&self, index: u64) -> Option<[f32; 3]> {
        let mut out = [0.0f32; 3];
        let ok = unsafe { spatial_get_position(index, out.as_mut_ptr()) };
        if ok == 0 { None } else { Some(out) }
    }

    /// Set the position of a single entity by index.
    pub fn set_position(&self, index: u64, x: f32, y: f32, z: f32) -> PyResult<bool> {
        let ok = unsafe { spatial_set_position(index, x, y, z) };
        Ok(ok != 0)
    }

    /// Set the velocity of a single entity by index.
    pub fn set_velocity(&self, index: u64, vx: f32, vy: f32, vz: f32) -> PyResult<bool> {
        let ok = unsafe { spatial_set_velocity(index, vx, vy, vz) };
        Ok(ok != 0)
    }

    // ── Analysis ───────────────────────────────────────────────────

    /// Compute the center of mass across all entities.
    /// Returns [cx, cy, cz].
    pub fn center_of_mass(&self) -> PyResult<[f32; 3]> {
        let count = unsafe { spatial_count() } as usize;
        if count == 0 {
            return Ok([0.0; 3]);
        }
        let ptr = unsafe { spatial_get_base() as *mut SpatialEntity };
        let mut out = [0.0f32; 3];
        unsafe { physics_center_of_mass(ptr, count, out.as_mut_ptr()); }
        Ok(out)
    }

    // ── Engine info ────────────────────────────────────────────────

    pub fn __repr__(&self) -> String {
        let count = unsafe { spatial_count() };
        format!(
            "<NiktoTripleEngine entities={} capacity={} layers=[Zig/Mojo/Rust]>",
            count,
            unsafe { spatial_capacity() },
        )
    }
}
