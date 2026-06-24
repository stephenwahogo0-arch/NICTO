import React, { useState, useEffect } from "react";
import "./StatusPanel.css";

interface SystemInfo {
  version: string;
  platform: string;
  python: string;
  torch: string;
  memory_gb: number;
  uptime_hours: number;
  active_skills: number;
  knowledge_bases: number;
  total_params_m: number;
  recursive_cycles: number;
  youtube_fetched: number;
  selfplay_generated: number;
  api_connected: boolean;
}

function defaultInfo(): SystemInfo {
  return {
    version: "5.3.0",
    platform: navigator.platform,
    python: "3.12",
    torch: "2.x",
    memory_gb: 16,
    uptime_hours: 0,
    active_skills: 100,
    knowledge_bases: 17,
    total_params_m: 17.2,
    recursive_cycles: 2,
    youtube_fetched: 212,
    selfplay_generated: 165,
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
    { label: "Platform", value: info.platform },
    { label: "Python", value: info.python },
    { label: "PyTorch", value: info.torch },
    { label: "Memory", value: `${info.memory_gb} GB` },
    { label: "Uptime", value: `${info.uptime_hours.toFixed(1)}h` },
    { label: "Active Skills", value: info.active_skills.toString() },
    { label: "Knowledge Bases", value: info.knowledge_bases.toString() },
    { label: "Total Parameters", value: `${info.total_params_m}M` },
    { label: "Recursive Cycles", value: info.recursive_cycles.toString() },
    { label: "YouTube Fetched", value: info.youtube_fetched.toString() },
    { label: "Self-Play Generated", value: info.selfplay_generated.toString() },
  ];

  return (
    <div className="status-view">
      <div className="status-header">
        <h2>System Status</h2>
        <div className={`api-indicator ${info.api_connected ? "connected" : "offline"}`}>
          <span className="indicator-dot" />
          {info.api_connected ? "API Connected" : "API Offline"}
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
        <h3>System Notes</h3>
        <ul>
          <li>
            <strong>Creative Brain:</strong> 17.2M parameter SuperiorCreativeBrain with
            knowledge graph attention over 5 domains.
          </li>
          <li>
            <strong>Recursive Learning:</strong> 8-phase loop compounds creative quality
            each cycle. Current: {info.recursive_cycles} cycles.
          </li>
          <li>
            <strong>Autonomous Data:</strong> NICTO fetches cinematography data via YouTube API
            ({info.youtube_fetched} videos), generates self-play pairs ({info.selfplay_generated}).
          </li>
          <li>
            <strong>Output Heads:</strong> 8 specialized — visual_describe, critique,
            compose, light, grade, direct, storyboard, innovate.
          </li>
          <li>
            <strong>12-Axis Quality:</strong> technical_accuracy, visual_clarity,
            specificity, novelty, emotional_impact, actionability, genre_alignment,
            sensorimotor_detail, narrative_coherence, cross_domain_integration,
            subtext_depth, economy.
          </li>
        </ul>
      </div>
    </div>
  );
}

export default StatusPanel;
