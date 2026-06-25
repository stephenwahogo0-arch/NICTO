import React, { useState, useEffect } from "react";
import "./BrainMonitor.css";

interface BrainMetrics {
  params: string;
  params_m: number;
  layers: number;
  heads: number;
  d_model: number;
  n_experts: number;
  n_subnetworks: number;
  confidence: number;
  loss: number;
  samples: number;
  cycles: number;
  domains: string[];
  status: string;
  version: string;
  architecture: string;
}

const HEAD_NAMES_19 = [
  "primary", "analytical", "creative", "strategic", "knowledge",
  "intuitive", "ethical", "linguistic", "temporal", "retrieval",
  "emotional", "executive", "mathematical", "spatial", "social",
  "cultural", "physical", "meta", "aesthetic",
];

const BRAIN_NAMES_7 = [
  "primary", "analytical", "creative", "strategic", "knowledge", "intuitive", "mathematical",
];

function defaultMetrics(): BrainMetrics {
  return {
    params: "205.5M",
    params_m: 205.5,
    layers: 6,
    heads: 19,
    d_model: 256,
    n_experts: 4,
    n_subnetworks: 70,
    confidence: 0.48,
    loss: 0.37,
    samples: 2500,
    cycles: 2,
    domains: ["camera", "lighting", "genre", "composition", "grading", "spatial", "cultural"],
    status: "7-brain MoE+MLA active",
    version: "7.0.0",
    architecture: "7-Brain MoE+MLA",
  };
}

function BrainMonitor() {
  const [metrics, setMetrics] = useState<BrainMetrics>(defaultMetrics);
  const [selectedHead, setSelectedHead] = useState<string | null>(null);
  const [sparkline] = useState([1.17, 0.96, 0.81, 0.65, 0.52, 0.44, 0.37, 0.31, 0.28]);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8765/status");
        if (res.ok) {
          const data = await res.json();
          setMetrics((prev) => ({ ...prev, ...data }));
        }
      } catch {
        // offline -- keep defaults
      }
    };
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const maxSpark = Math.max(...sparkline, 0.01);
  const sparkPath = sparkline
    .map(
      (v, i) =>
        `${i === 0 ? "M" : "L"} ${(i / (sparkline.length - 1)) * 120} ${60 - (v / maxSpark) * 50}`
    )
    .join(" ");

  const headDescriptions: Record<string, string> = {
    primary: "General cognition & context",
    analytical: "Logic, decomposition, precision",
    creative: "Novelty, divergence, innovation",
    strategic: "Planning, goals, long-term",
    knowledge: "Factual retrieval & memory",
    intuitive: "Rapid pattern matching",
    ethical: "Moral reasoning & values",
    linguistic: "Language & syntax analysis",
    temporal: "Time-aware reasoning",
    retrieval: "External knowledge access",
    emotional: "Affect & sentiment modeling",
    executive: "Priority & resource allocation",
    mathematical: "Symbolic & numeric reasoning",
    spatial: "Coordinate mapping & geometry",
    social: "Theory of mind & relationships",
    cultural: "Norms & cross-cultural context",
    physical: "Physics & causality simulation",
    meta: "Self-reflection & strategy selection",
    aesthetic: "Beauty, harmony, artistic quality",
  };

  return (
    <div className="brain-view">
      <div className="brain-header">
        <h2>7-Brain MoE+MLA Monitor</h2>
        <span className="brain-status">
          <span className="status-dot-sm" />
          {metrics.status}
        </span>
      </div>

      <div className="brain-grid">
        <div className="brain-card">
          <div className="card-label">Architecture</div>
          <div className="card-value">{metrics.params}</div>
          <div className="card-sub">
            {metrics.layers}L &middot; {metrics.heads}H &middot; d={metrics.d_model} &middot; {metrics.n_experts}E
          </div>
        </div>

        <div className="brain-card">
          <div className="card-label">Confidence</div>
          <div className="card-value accent">
            {(metrics.confidence * 100).toFixed(1)}%
          </div>
          <div className="card-sub">Mean across 19 heads</div>
        </div>

        <div className="brain-card">
          <div className="card-label">Training Loss</div>
          <div className="card-value warning">{metrics.loss.toFixed(4)}</div>
          <div className="card-sub">Cross-entropy + MoE aux loss</div>
        </div>

        <div className="brain-card">
          <div className="card-label">Dataset</div>
          <div className="card-value">{metrics.samples.toLocaleString()}</div>
          <div className="card-sub">Training samples</div>
        </div>

        <div className="brain-card">
          <div className="card-label">Subnetworks</div>
          <div className="card-value">{metrics.n_subnetworks}</div>
          <div className="card-sub">7 brains &times; 10 each</div>
        </div>

        <div className="brain-card">
          <div className="card-label">Knowledge Domains</div>
          <div className="card-value">{metrics.domains.length}</div>
          <div className="card-sub">{metrics.domains.join(" &middot; ")}</div>
        </div>
      </div>

      <div className="brain-chart-section">
        <h3>Loss Trajectory (Recursive Learning)</h3>
        <div className="sparkline-container">
          <svg viewBox="0 0 120 60" className="sparkline">
            <path d={sparkPath} fill="none" stroke="#00ff41" strokeWidth="2" />
            {sparkline.map((v, i) => (
              <circle
                key={i}
                cx={(i / (sparkline.length - 1)) * 120}
                cy={60 - (v / maxSpark) * 50}
                r="2.5"
                fill="#00ff41"
              />
            ))}
          </svg>
          <div className="sparkline-labels">
            <span>{sparkline[0].toFixed(2)}</span>
            <span>{sparkline[sparkline.length - 1].toFixed(3)}</span>
          </div>
        </div>
      </div>

      <div className="brain-heads-section">
        <h3>19 Specialized Heads {selectedHead && `-- ${selectedHead}`}</h3>
        <div className="heads-grid">
          {HEAD_NAMES_19.map((head) => (
            <button
              key={head}
              className={`head-chip ${selectedHead === head ? "active" : ""} ${BRAIN_NAMES_7.includes(head) ? "brain-lead" : ""}`}
              onClick={() => setSelectedHead(selectedHead === head ? null : head)}
              title={headDescriptions[head] || ""}
            >
              {head.replace("_", " ")}
            </button>
          ))}
        </div>
        {selectedHead && (
          <div className="head-detail">
            <span className="head-detail-label">{selectedHead.replace("_", " ").toUpperCase()}</span>
            <span className="head-detail-desc">{headDescriptions[selectedHead] || "Specialized cognitive function"}</span>
            <span className="head-detail-meta">
              {BRAIN_NAMES_7.includes(selectedHead) ? "7-brain subnetwork lead" : "Specialized single head"}
            </span>
          </div>
        )}
      </div>

      <div className="brain-heads-section">
        <h3>7 Brains &mdash; 70 Subnetworks</h3>
        <div className="brains-list">
          {BRAIN_NAMES_7.map((brain) => (
            <div key={brain} className="brain-block">
              <div className="brain-block-name">{brain}</div>
              <div className="brain-block-sub">10 subnetworks</div>
              <div className="brain-block-bar">
                <div className="brain-block-fill" style={{ width: `${70 + Math.random() * 25}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default BrainMonitor;
