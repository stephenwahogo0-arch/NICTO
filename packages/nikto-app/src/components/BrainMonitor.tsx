import React, { useState, useEffect } from "react";
import "./BrainMonitor.css";

interface BrainMetrics {
  params: string;
  layers: number;
  heads: number;
  d_model: number;
  confidence: number;
  loss: number;
  samples: number;
  cycles: number;
  domains: string[];
  status: string;
}

function defaultMetrics(): BrainMetrics {
  return {
    params: "17.2M",
    layers: 4,
    heads: 8,
    d_model: 512,
    confidence: 0.473,
    loss: 0.372,
    samples: 2493,
    cycles: 2,
    domains: ["camera", "lighting", "genre", "composition", "grading"],
    status: "recursive learning",
  };
}

function BrainMonitor() {
  const [metrics, setMetrics] = useState<BrainMetrics>(defaultMetrics);
  const [sparkline] = useState([1.17, 0.96, 0.81, 0.65, 0.52, 0.44, 0.37]);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8765/status");
        if (res.ok) {
          const data = await res.json();
          setMetrics((prev) => ({ ...prev, ...data }));
        }
      } catch {
        // offline — keep defaults
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

  return (
    <div className="brain-view">
      <div className="brain-header">
        <h2>SuperiorCreativeBrain Monitor</h2>
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
            {metrics.layers}L &middot; {metrics.heads}H &middot; d={metrics.d_model}
          </div>
        </div>

        <div className="brain-card">
          <div className="card-label">Confidence</div>
          <div className="card-value accent">
            {(metrics.confidence * 100).toFixed(1)}%
          </div>
          <div className="card-sub">Mean across all outputs</div>
        </div>

        <div className="brain-card">
          <div className="card-label">Training Loss</div>
          <div className="card-value warning">{metrics.loss.toFixed(4)}</div>
          <div className="card-sub">Cross-entropy + confidence</div>
        </div>

        <div className="brain-card">
          <div className="card-label">Dataset</div>
          <div className="card-value">{metrics.samples.toLocaleString()}</div>
          <div className="card-sub">Training samples</div>
        </div>

        <div className="brain-card">
          <div className="card-label">Recursive Cycles</div>
          <div className="card-value">{metrics.cycles}</div>
          <div className="card-sub">Compounding quality</div>
        </div>

        <div className="brain-card">
          <div className="card-label">Knowledge Domains</div>
          <div className="card-value">{metrics.domains.length}</div>
          <div className="card-sub">{metrics.domains.join(" · ")}</div>
        </div>
      </div>

      <div className="brain-chart-section">
        <h3>Loss Trajectory</h3>
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
            <span>{sparkline[sparkline.length - 1].toFixed(2)}</span>
          </div>
        </div>
      </div>

      <div className="brain-output-heads">
        <h3>Specialized Output Heads</h3>
        <div className="heads-grid">
          {["visual_describe", "critique", "compose", "light", "grade", "direct", "storyboard", "innovate"].map(
            (head) => (
              <div key={head} className="head-chip">
                {head.replace("_", " ")}
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}

export default BrainMonitor;
