//! # NIKTO Core Engine — AI-Native Generative Engine in Rust
//!
//! Three layers:
//!   1. **ECS** (ecs.rs) — cache-line-aligned entity storage, parallel systems
//!   2. **World gen** (world_gen.rs) — procedural voxel/mesh ingestion from Python brains
//!   3. **Scene + Renderer** (scene.rs + renderer.rs) — octree scene graph + wgpu GPU pipeline
//!
//! All exposed to Python via bridge.rs + `#[pymodule]`.

pub mod bridge;
pub mod ecs;
pub mod renderer;
pub mod scene;
pub mod world_gen;

use pyo3::prelude::*;

#[pymodule]
fn nikto_core_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<bridge::NiktoEngine>()?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;

    let info = format!(
        "NIKTO Core Engine v{} | Rust ECS + wgpu GPU | {} workers | cache-line: 64B",
        env!("CARGO_PKG_VERSION"),
        rayon::current_num_threads(),
    );
    m.add("__build_info__", info)?;

    Ok(())
}
