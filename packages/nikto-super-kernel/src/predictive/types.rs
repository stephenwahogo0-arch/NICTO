use pyo3::prelude::*;
use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
#[pyclass]
pub struct CodeLocation {
    #[pyo3(get)]
    pub file: String,
    #[pyo3(get)]
    pub line: u32,
    #[pyo3(get)]
    pub column: u32,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum VulnerabilityKind {
    MemoryLeak,
    DataRace,
    UnhandledException,
    BufferOverflow,
    UnsafeCode,
    PanicRisk,
    StackOverflow,
    Deadlock,
    NullPointer,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum Severity {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[pyclass]
pub struct Vulnerability {
    #[pyo3(get)]
    pub kind: String,
    #[pyo3(get)]
    pub location: CodeLocation,
    #[pyo3(get)]
    pub severity: String,
    #[pyo3(get)]
    pub description: String,
    #[pyo3(get)]
    pub suggestion: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[pyclass]
pub struct DiagnosticReport {
    #[pyo3(get)]
    pub project: String,
    #[pyo3(get)]
    pub files_scanned: u32,
    #[pyo3(get)]
    pub vulnerabilities: Vec<Vulnerability>,
    #[pyo3(get)]
    pub root_cause: Option<String>,
    #[pyo3(get)]
    pub optimization_hints: Vec<String>,
    #[pyo3(get)]
    pub scan_duration_ms: f64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[pyclass]
pub struct MarketOHLCV {
    #[pyo3(get, set)]
    pub timestamp: u64,
    #[pyo3(get, set)]
    pub open: f64,
    #[pyo3(get, set)]
    pub high: f64,
    #[pyo3(get, set)]
    pub low: f64,
    #[pyo3(get, set)]
    pub close: f64,
    #[pyo3(get, set)]
    pub volume: f64,
}

#[pymethods]
impl MarketOHLCV {
    #[new]
    pub fn new() -> Self {
        Self { timestamp: 0, open: 0.0, high: 0.0, low: 0.0, close: 0.0, volume: 0.0 }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[pyclass]
pub struct PricePath {
    #[pyo3(get)]
    pub probabilities: Vec<f64>,
    #[pyo3(get)]
    pub confidence_upper: Vec<f64>,
    #[pyo3(get)]
    pub confidence_lower: Vec<f64>,
    #[pyo3(get)]
    pub expected: Vec<f64>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[pyclass]
pub struct PredictionMatrix {
    #[pyo3(get)]
    pub horizon_days: u32,
    #[pyo3(get)]
    pub simulations: u32,
    #[pyo3(get)]
    pub price_paths: Vec<PricePath>,
    #[pyo3(get)]
    pub overall_probability: f64,
    #[pyo3(get)]
    pub value_at_risk_95: f64,
    #[pyo3(get)]
    pub expected_return: f64,
    #[pyo3(get)]
    pub volatility: f64,
}

#[pymethods]
impl DiagnosticReport {
    fn __repr__(&self) -> String {
        format!("DiagnosticReport(project={}, files={}, vulns={}, duration={}ms)",
                self.project, self.files_scanned, self.vulnerabilities.len(), self.scan_duration_ms)
    }
}

#[pymethods]
impl PredictionMatrix {
    fn __repr__(&self) -> String {
        format!("PredictionMatrix(horizon={}d, sims={}, expected={:.2}%, VaR95={:.2}%)",
                self.horizon_days, self.simulations, self.expected_return * 100.0, self.value_at_risk_95 * 100.0)
    }
}
