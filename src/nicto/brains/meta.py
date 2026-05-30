"""Meta Cognition Brain — self-monitoring and improvement."""
from __future__ import annotations

import time
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .base import Brain, BrainConfig, BrainResponse


@dataclass
class ExecutionRecord:
    """Record of a single execution for meta-cognitive analysis."""
    timestamp: float = field(default_factory=time.time)
    task_category: str = ""
    brain_used: str = ""
    latency_ms: float = 0.0
    confidence: float = 0.0
    query_hash: str = ""
    resources: Dict[str, Any] = field(default_factory=dict)
    feedback: Optional[float] = None


@dataclass
class ImprovementHypothesis:
    """A hypothesis for improving the system."""
    id: str
    description: str
    status: str = "proposed"  # proposed, testing, validated, rejected
    success_criteria: List[str] = field(default_factory=list)


class PerformanceMetrics:
    """Container for performance metrics (stub for Phase 1)."""
    def __init__(self):
        self.data: Dict[str, Any] = {}

    def update(self, key: str, value: Any):
        self.data[key] = value

    def get(self, key: str, default: Any = None):
        return self.data.get(key, default)


class MetaCognitionBrain(Brain):
    """Meta brain for logging and self-improvement."""

    def __init__(self, config: Optional[BrainConfig] = None):
        if config is None:
            config = BrainConfig(
                model_name="meta-cognitor",
                model_size_gb=0.1,
                quantization_bits=32,
                max_latency_ms=50.0,
                timeout_seconds=5.0
            )
        super().__init__(config)
        self.execution_log: List[ExecutionRecord] = []
        self.performance_metrics = PerformanceMetrics()
        self.improvement_hypotheses: List[ImprovementHypothesis] = []
        self._log_file = os.path.join(".nicto", "meta_log.jsonl")
        os.makedirs(os.path.dirname(self._log_file), exist_ok=True)

    def _load_model(self) -> Any:
        """Load the meta brain's model. For Phase 1, we return a dummy object."""
        return object()

    def _process_internal(self, prompt: str, **kwargs) -> str:
        """Process a prompt by returning it unchanged (pass-through)."""
        return prompt

    def log_execution(self, task_category: str, response: BrainResponse, confidence: float) -> None:
        """Log an execution for meta-cognitive analysis."""
        # Create a hash of the query for privacy (we don't store the full query in logs)
        query_hash = hashlib.sha256(str(response.content).encode()).hexdigest()[:16]
        
        record = ExecutionRecord(
            timestamp=time.time(),
            task_category=task_category,
            brain_used=response.metadata.get("brain_type", "unknown"),
            latency_ms=response.latency_ms,
            confidence=response.confidence,
            query_hash=query_hash,
            resources=response.metadata.get("resources", {}),
            feedback=None  # Feedback would come from user or external system
        )
        self.execution_log.append(record)
        
        # Keep only the last 1000 records in memory
        if len(self.execution_log) > 1000:
            self.execution_log = self.execution_log[-1000:]
        
        # Append to disk log (optional, for persistence)
        try:
            with open(self._log_file, "a") as f:
                f.write(json.dumps(record.__dict__) + "\n")
        except Exception:
            # In production, we'd want to log this error
            pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get meta-cognition metrics."""
        if not self.execution_log:
            return {"status": "no_data"}
        
        latencies = [r.latency_ms for r in self.execution_log]
        confidences = [r.confidence for r in self.execution_log]
        
        return {
            "total_executions": len(self.execution_log),
            "avg_latency_ms": sum(latencies) / len(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "performance_metrics": self.performance_metrics.data
        }

    def _detect_anomaly(self) -> List[str]:
        """Detect anomalies in recent performance (stub)."""
        # In a full implementation, we would use statistical methods
        return []

    def _generate_improvement_hypotheses(self) -> List[ImprovementHypothesis]:
        """Generate improvement hypotheses based on recent data (stub)."""
        return []

    def _test_hypothesis(self, hypothesis: ImprovementHypothesis) -> bool:
        """Test an improvement hypothesis (stub)."""
        return False