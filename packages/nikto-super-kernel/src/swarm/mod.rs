use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;

use pyo3::prelude::*;

/// Sector 6 — Swarm: distributed agent orchestration, task dispatch, heartbeat tracking.
#[pyclass]
pub struct SwarmOrchestrator {
    agents: HashMap<String, AgentHandle>,
    task_counter: Arc<AtomicU64>,
}

#[derive(Clone, Debug)]
struct AgentHandle {
    id: String,
    role: String,
    last_heartbeat: u64,
    pending_tasks: Vec<TaskSpec>,
}

#[derive(Clone, Debug)]
struct TaskSpec {
    id: u64,
    command: String,
    payload: Vec<u8>,
    status: String,
}

#[pymethods]
impl SwarmOrchestrator {
    #[new]
    pub fn new() -> Self {
        Self { agents: HashMap::new(), task_counter: Arc::new(AtomicU64::new(0)) }
    }

    pub fn register_agent(&mut self, agent_id: &str, role: &str) {
        self.agents.insert(agent_id.into(), AgentHandle {
            id: agent_id.into(),
            role: role.into(),
            last_heartbeat: now_secs(),
            pending_tasks: Vec::new(),
        });
    }

    pub fn dispatch(&mut self, target: &str, command: &str, payload: Vec<u8>) -> PyResult<u64> {
        let agent = self.agents.get_mut(target)
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err(format!("unknown agent: {}", target)))?;
        let task_id = self.task_counter.fetch_add(1, Ordering::SeqCst);
        agent.pending_tasks.push(TaskSpec {
            id: task_id, command: command.into(), payload, status: "PENDING".into(),
        });
        Ok(task_id)
    }

    pub fn heartbeat(&mut self, agent_id: &str) -> PyResult<()> {
        let agent = self.agents.get_mut(agent_id)
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err(format!("unknown agent: {}", agent_id)))?;
        agent.last_heartbeat = now_secs();
        Ok(())
    }

    pub fn status(&self) -> String {
        let mut out = format!("Swarm: {} agents\n", self.agents.len());
        for (id, agent) in &self.agents {
            let age = now_secs().saturating_sub(agent.last_heartbeat);
            let alive = if age < 30 { "ALIVE" } else { "STALE" };
            out.push_str(&format!("  {} ({}) [{}] tasks={} last_hb={}s ago\n",
                id, agent.role, alive, agent.pending_tasks.len(), age));
        }
        out
    }

    pub fn agent_count(&self) -> usize { self.agents.len() }
    pub fn live_agents(&self) -> usize {
        let now = now_secs();
        self.agents.values().filter(|a| now.saturating_sub(a.last_heartbeat) < 30).count()
    }
}

fn now_secs() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH).unwrap().as_secs()
}
