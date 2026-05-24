// NIKTO Super Kernel — Unified cdylib exposing all 8 sectors via PyO3.

pub mod boot;
pub mod neural;
pub mod physics;
pub mod predictive;
pub mod finance;
pub mod vision;
pub mod audio;
pub mod terminal;
pub mod memory;
pub mod security;
pub mod swarm;
pub mod sync;
pub mod webforge;

use pyo3::prelude::*;

/// Top-level Python class wrapping all sectors.
#[pyclass]
pub struct SuperKernel {
    pub boot: boot::BootLoader,
    pub neural: neural::NeuralCore,
    pub physics: physics::PhysicsEngine,
    pub predictive_code: predictive::CodeAnalyzer,
    pub predictive_market: predictive::MarketEngine,
    pub predictive_archive: predictive::DiagnosticArchive,
    pub predictive_sports: predictive::SportsPredictionEngine,
    pub finance_ts: finance::TimeSeriesEngine,
    pub finance_exec: finance::OrderExecutor,
    pub swarm: swarm::SwarmOrchestrator,
    pub webforge: webforge::WebForge,
}

#[pymethods]
impl SuperKernel {
    #[new]
    pub fn new(gravity: f64, fill_latency_ms: u64) -> Self {
        Self {
            boot: boot::BootLoader::new(),
            neural: neural::NeuralCore::new(),
            physics: physics::PhysicsEngine::new(gravity),
            predictive_code: predictive::CodeAnalyzer::new(),
            predictive_market: predictive::MarketEngine::new(1000, 252),
            predictive_archive: predictive::DiagnosticArchive::new(""),
            predictive_sports: predictive::SportsPredictionEngine::new(10000),
            finance_ts: finance::TimeSeriesEngine,
            finance_exec: finance::OrderExecutor::new(fill_latency_ms),
            swarm: swarm::SwarmOrchestrator::new(),
            webforge: webforge::WebForge::new(),
        }
    }

    // ── Boot ──
    pub fn boot_register(&mut self, name: &str, version: &str) {
        self.boot.register(name, version);
    }
    pub fn boot_load(&mut self, name: &str) -> PyResult<String> {
        self.boot.load(name)
    }
    pub fn boot_health(&self) -> String { self.boot.health() }
    pub fn boot_resource_report(&self) -> String { self.boot.resource_report() }

    // ── Neural ──
    pub fn neural_ingest(&mut self, topic: &str, content: &str) {
        self.neural.ingest(topic, content);
    }
    pub fn neural_recall(&self, query: &str, top_k: usize) -> Vec<String> {
        self.neural.recall(query, top_k)
    }
    pub fn neural_count(&self) -> usize { self.neural.count() }

    // ── Physics ──
    pub fn physics_add_body(&mut self, x: f64, y: f64, z: f64, mass: f64, radius: f64) {
        self.physics.add_body(x, y, z, mass, radius);
    }
    pub fn physics_step(&mut self, dt: f64) { self.physics.step(dt); }
    pub fn physics_body_count(&self) -> usize { self.physics.body_count() }

    // ── Predictive: Code Analyzer ──
    pub fn code_analyze_project(&self, project_path: &str) -> predictive::DiagnosticReport {
        self.predictive_code.analyze_project(project_path, None)
    }
    pub fn code_vulnerability_count(&self) -> usize {
        self.predictive_code.vulnerability_count()
    }

    // ── Predictive: Market Engine ──
    pub fn market_predict(&self, candles: Vec<predictive::MarketOHLCV>, horizon_days: u32) -> predictive::PredictionMatrix {
        let engine = predictive::MarketEngine::new(self.predictive_market.simulation_count(), horizon_days);
        engine.predict(&candles)
    }

    // ── Predictive: Sports Engine ──
    pub fn sports_ingest_match(&mut self, team_a: &str, team_b: &str, score_a: u32, score_b: u32) {
        let result = predictive::MatchResult {
            team_a: team_a.into(),
            team_b: team_b.into(),
            score_a,
            score_b,
        };
        self.predictive_sports.ingest_match(&result, false);
    }
    pub fn sports_predict(&self, team_a: &str, team_b: &str, neutral: bool) -> predictive::SportsPrediction {
        self.predictive_sports.predict(team_a, team_b, neutral)
    }
    pub fn sports_team_count(&self) -> usize {
        self.predictive_sports.team_count()
    }

    // ── Predictive: Diagnostic Archive ──
    pub fn archive_write_diag(&self, report: &predictive::DiagnosticReport) -> PyResult<String> {
        self.predictive_archive.write_diag(report).map(|_| "diagnostic written".into())
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e))
    }
    pub fn archive_read_diag(&self, index: usize) -> PyResult<predictive::DiagnosticReport> {
        self.predictive_archive.read_diag(index)
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e))
    }

    // ── Finance: Time Series ──
    pub fn finance_analyze(&self, ohlcv: Vec<predictive::MarketOHLCV>) -> finance::TimeSeriesAnalysis {
        finance::TimeSeriesEngine::analyze(&ohlcv)
    }

    // ── Finance: Order Executor ──
    pub fn finance_submit(&mut self, proposal: finance::TradeProposal,
                          equity: f64, daily_pnl: f64,
                          daily_loss_limit: f64, max_drawdown_pct: f64) -> PyResult<(finance::RiskVerdict, Option<finance::OrderResult>)> {
        let state = finance::PortfolioState {
            total_equity: equity, daily_pnl,
            daily_loss_limit, max_drawdown_pct,
        };
        Ok(self.finance_exec.submit(proposal, &state))
    }
    pub fn finance_fill_next(&mut self) -> Option<finance::OrderResult> {
        self.finance_exec.fill_next()
    }

    // ── Swarm ──
    pub fn swarm_register_agent(&mut self, agent_id: &str, role: &str) {
        self.swarm.register_agent(agent_id, role);
    }
    pub fn swarm_dispatch(&mut self, target: &str, command: &str,
                          payload: Vec<u8>) -> PyResult<u64> {
        self.swarm.dispatch(target, command, payload)
    }
    pub fn swarm_heartbeat(&mut self, agent_id: &str) -> PyResult<()> {
        self.swarm.heartbeat(agent_id)
    }
    pub fn swarm_status(&self) -> String { self.swarm.status() }

    // ── WebForge ──
    pub fn webforge_add_template(&mut self, name: &str, content: &str) {
        self.webforge.add_template(name, content);
    }
    pub fn webforge_add_site(&mut self, name: &str, domain: &str,
                             template: &str, output_dir: &str,
                             variables: std::collections::HashMap<String, String>) -> PyResult<()> {
        self.webforge.add_site(name, domain, template, output_dir, variables)
    }
    pub fn webforge_render(&self, site_name: &str) -> PyResult<String> {
        self.webforge.render(site_name)
    }

    /// Report total system state.
    pub fn status(&self) -> String {
        format!(
            "NIKTO v1.0 | Boot: {} | Neural: {} | Physics: {} | Code: {} vulns | Market: {} sims | Swarm: {} agents | Audits: {}",
            self.boot.modules_count(),
            self.neural.count(),
            self.physics.body_count(),
            self.predictive_code.vulnerability_count(),
            self.predictive_market.simulation_count(),
            self.swarm.agent_count(),
            self.finance_exec.audit_count(),
        )
    }
}

/// PyO3 module entry point.
#[pymodule]
fn nikto_super_kernel(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<SuperKernel>()?;

    // Register sector types
    m.add_class::<predictive::DiagnosticReport>()?;
    m.add_class::<predictive::Vulnerability>()?;
    m.add_class::<predictive::PredictionMatrix>()?;
    m.add_class::<predictive::MarketOHLCV>()?;
    m.add_class::<finance::TradeProposal>()?;
    m.add_class::<finance::PortfolioState>()?;
    m.add_class::<finance::RiskVerdict>()?;
    m.add_class::<finance::OrderResult>()?;
    m.add_class::<finance::TimeSeriesAnalysis>()?;
    m.add_class::<finance::BacktestResult>()?;
    m.add_class::<neural::NeuralCore>()?;
    m.add_class::<boot::BootLoader>()?;
    m.add_class::<physics::PhysicsEngine>()?;
    m.add_class::<swarm::SwarmOrchestrator>()?;
    m.add_class::<webforge::WebForge>()?;
    m.add_class::<predictive::SportsPrediction>()?;
    m.add_class::<predictive::MatchResult>()?;
    m.add_class::<predictive::TeamRecord>()?;

    Ok(())
}
