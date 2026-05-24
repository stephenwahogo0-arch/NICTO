use std::collections::HashMap;
use std::time::Instant;

use pyo3::prelude::*;

/// Sector 1 — Boot: kernel initialization, health checks, resource discovery.
#[pyclass]
pub struct BootLoader {
    start: Instant,
    modules: HashMap<String, ModuleStatus>,
}

#[derive(Clone, Debug)]
struct ModuleStatus {
    loaded: bool,
    version: String,
    load_time_ms: f64,
}

#[pymethods]
impl BootLoader {
    #[new]
    pub fn new() -> Self {
        Self { start: Instant::now(), modules: HashMap::new() }
    }

    pub fn register(&mut self, name: &str, version: &str) {
        self.modules.insert(name.into(), ModuleStatus {
            loaded: false, version: version.into(), load_time_ms: 0.0,
        });
    }

    pub fn load(&mut self, name: &str) -> PyResult<String> {
        let status = self.modules.get_mut(name)
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err(format!("unknown module: {}", name)))?;
        let t0 = Instant::now();
        status.loaded = true;
        status.load_time_ms = t0.elapsed().as_secs_f64() * 1000.0;
        Ok(format!("{} v{} loaded in {:.1}ms", name, status.version, status.load_time_ms))
    }

    pub fn health(&self) -> String {
        let total = self.modules.len();
        let loaded = self.modules.values().filter(|m| m.loaded).count();
        let elapsed = self.start.elapsed().as_secs_f64();
        format!("NIKTO kernel | {}/{} modules | uptime {:.1}s | {}",
                loaded, total, elapsed,
                if loaded == total { "ALL SYSTEMS NOMINAL" } else { "PARTIAL" })
    }

    pub fn resource_report(&self) -> String {
        let mut report = String::new();
        report.push_str(&format!("Uptime: {:.1}s\n", self.start.elapsed().as_secs_f64()));
        report.push_str(&format!("Modules: {}/{} loaded\n",
            self.modules.values().filter(|m| m.loaded).count(), self.modules.len()));
        for (name, status) in &self.modules {
            report.push_str(&format!("  {} v{}: {}\n", name, status.version,
                if status.loaded { "OK" } else { "PENDING" }));
        }
        report
    }

    pub fn modules_count(&self) -> usize { self.modules.len() }
    pub fn uptime_secs(&self) -> f64 { self.start.elapsed().as_secs_f64() }
}
