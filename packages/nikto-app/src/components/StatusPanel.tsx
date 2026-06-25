import React, { useState, useEffect } from "react";
import "./StatusPanel.css";

interface SystemInfo {
  version: string;
  architecture: string;
  n_heads: number;
  n_subnetworks: number;
  params: number;
  params_m: number;
  platform: string;
  python: string;
  memory_gb: number;
  uptime_hours: number;
  active_skills: number;
  knowledge_bases: number;
  active_heads: string[];
  initialized: boolean;
  api_connected: boolean;
}

function defaultInfo(): SystemInfo {
  return {
    version: "7.0.0",
    architecture: "7-Brain MoE+MLA",
    n_heads: 19,
    n_subnetworks: 70,
    params: 205470584,
    params_m: 205.5,
    platform: navigator.platform,
    python: "3.12",
    memory_gb: 16,
    uptime_hours: 0,
    active_skills: 100,
    knowledge_bases: 17,
    active_heads: [],
    initialized: false,
    api_connected: false,
  };
}

function StatusPanel() {
  const [info, setInfo] = useState<SystemInfo>(defaultInfo);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8765/status");
        if (res.ok) {
          const data = await res.json();
          setInfo((prev) => ({ ...prev, ...data, api_connected: true }));
        }
      } catch {
        setInfo((prev) => ({ ...prev, api_connected: false }));
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const entries = [
    { label: "Version", value: info.version },
    { label: "Architecture", value: info.architecture },
    { label: "Brain Heads", value: info.n_heads.toString() },
    { label: "Subnetworks", value: info.n_subnetworks.toString() },
    { label: "Total Parameters", value: `${(info.params / 1e6).toFixed(1)}M` },
    { label: "Platform", value: info.platform },
    { label: "Python", value: info.python },
    { label: "Memory", value: `${info.memory_gb} GB` },
    { label: "Uptime", value: `${info.uptime_hours.toFixed(1)}h` },
    { label: "Active Skills", value: info.active_skills.toString() },
    { label: "Knowledge Bases", value: info.knowledge_bases.toString() },
    { label: "Engine Status", value: info.initialized ? "Online" : "Standby" },
  ];

  const headCategories = [
    {
      group: "7 Brains (70 subnetworks)",
      heads: ["primary", "analytical", "creative", "strategic", "knowledge", "intuitive", "mathematical"],
    },
    {
      group: "Specialized Single Heads",
      heads: ["ethical", "linguistic", "temporal", "retrieval", "emotional", "executive", "spatial", "social", "cultural", "physical", "meta", "aesthetic"],
    },
  ];

  const nActive = info.active_heads.length;

  return (
    <div className="status-view">
      <div className="status-header">
        <h2>System Status</h2>
        <div className={`api-indicator ${info.api_connected ? "connected" : "offline"}`}>
          <span className="indicator-dot" />
          {info.api_connected ? `${nActive}/19 Heads Active` : "API Offline"}
        </div>
      </div>

      <div className="status-table">
        {entries.map(({ label, value }) => (
          <div key={label} className="status-row">
            <span className="status-label">{label}</span>
            <span className="status-value">{value}</span>
          </div>
        ))}
      </div>

      <div className="status-notes">
        <h3>7-Brain MoE+MLA Architecture</h3>
        <ul>
          <li>
            <strong>Backbone:</strong> SuperNeuralCore with Multi-Head Latent Attention (MLA)
            -- DeepSeek V3-style compressed KV latent for efficient inference.
          </li>
          <li>
            <strong>MoE:</strong> Enhanced Mixture of Experts with shared experts, fine-grained
            routing, and load balancing loss.
          </li>
          <li>
            <strong>19 Heads:</strong> 7 subnetwork-based brains (10 subnetworks each = 70 total)
            + 12 specialized single heads for domain-specific cognition.
          </li>
          <li>
            <strong>1.33B Total:</strong> Full-scale architecture reaches 1.33B parameters
            (102.8M backbone + 1.23B head ensemble). CPU-friendly variant: 205.5M.
          </li>
          <li>
            <strong>Recursive Learning:</strong> 8-phase compounding loop generates self-play
            data, evaluates on 12 axes, and retrains to compound quality.
          </li>
        </ul>
      </div>

      <div className="status-notes" style={{ marginTop: "12px" }}>
        <h3>Head Categories</h3>
        {headCategories.map(({ group, heads }) => (
          <div key={group} style={{ marginBottom: "10px" }}>
            <div style={{ color: "#00ff41", fontSize: "12px", fontFamily: "var(--font-mono)", marginBottom: "6px" }}>
              {group}
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
              {heads.map((h) => (
                <span
                  key={h}
                  style={{
                    background: "#111c11",
                    border: "1px solid #1a3a1a",
                    borderRadius: "12px",
                    padding: "3px 10px",
                    fontSize: "11px",
                    fontFamily: "var(--font-mono)",
                    color: "#7aa87a",
                  }}
                >
                  {h}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default StatusPanel;
