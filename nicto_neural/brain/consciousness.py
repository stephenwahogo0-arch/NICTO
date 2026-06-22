import torch
import torch.nn as nn
import numpy as np
import time
import json
import os
from typing import Any, Dict, List, Optional, Tuple
from ..neural.config import NeuralConfig
from ..neural.elo_system import ELOEstimator
from ..neural.exploration import ExplorationEngine
from ..perception.feature_engine import FeatureEngine
from .orchestrator import BrainRouter
from .primary import PrimaryBrain
from .analytical import AnalyticalBrain
from .creative import CreativeBrain
from .strategic import StrategicBrain
from .knowledge import KnowledgeBrain
from .intuitive import IntuitiveBrain

BRAIN_NAMES = ["primary", "analytical", "creative", "strategic", "knowledge", "intuitive"]
DOMAINS = ["general", "code", "math", "creative", "strategic", "knowledge", "intuitive"]


class NeuralConsciousness:
    def __init__(
        self,
        config: NeuralConfig,
        router: BrainRouter,
        brains: Dict[str, nn.Module],
        elo_system: ELOEstimator,
        memory_manager=None,
        exploration: Optional[ExplorationEngine] = None,
    ):
        self.config = config
        self.router = router
        self.brains = brains
        self.elo = elo_system
        self.memory_manager = memory_manager
        self.exploration = exploration or ExplorationEngine()
        self.feature_engine = FeatureEngine()

        self._awake = False
        self._start_time = 0.0
        self._think_count = 0
        self._active_brains: List[str] = []
        self._thought_history: List[Dict] = []
        self._max_history = 500

    def think(self, task: Dict, domain: str = "general") -> Dict:
        if not self._awake:
            self.awake()

        result = self.process(task)
        return result

    def process(self, task: Dict) -> Dict:
        start_time = time.time()
        task.setdefault("domain", "general")
        task.setdefault("task_type", "analyze")
        task.setdefault("curriculum_level", 1)

        feature_vector = self.feature_engine.extract(task)
        domain = task.get("domain", "general")
        curriculum_level = task.get("curriculum_level", 1)

        route_weights = self.router.route(feature_vector, domain, curriculum_level)

        active_brains = [
            brain for brain, weight in route_weights.items()
            if weight > 0.05 and brain in self.brains
        ]
        self._active_brains = active_brains if active_brains else ["primary"]

        brain_outputs = {}
        brain_confidences = {}

        for name in active_brains:
            brain = self.brains[name]
            brain = brain.to(self.config.device)
            brain.eval()
            with torch.no_grad():
                dummy_input = torch.randn(
                    1, self.config.max_seq_len // 128, self.config.d_model,
                    device=self.config.device
                )
                if name == "creative":
                    temp = task.get("temperature", 0.8)
                    out, conf = brain(dummy_input, temperature=temp)
                else:
                    out, conf = brain(dummy_input)
                brain_outputs[name] = out
                brain_confidences[name] = conf

        merged = self.router.merge(brain_outputs, brain_confidences, strategy="weighted")

        intuitive_brain = self.brains.get("intuitive")
        pattern_result = {}
        if intuitive_brain is not None:
            intuitive_brain = intuitive_brain.to(self.config.device)
            with torch.no_grad():
                try:
                    brain_logits = merged
                    pattern_result = intuitive_brain.detect_pattern(brain_logits)
                except Exception:
                    pattern_result = {
                        "recommended_brain": "primary",
                        "confidence": 0.5,
                    }

        confidence_score = float(np.mean([
            float(c.mean().item()) for c in brain_confidences.values()
        ])) if brain_confidences else 0.5

        for name in active_brains:
            if name in brain_confidences:
                outcome = float(brain_confidences[name].mean().item())
                expected = route_weights.get(name, 0.5)
                self.router.update_elo(name, domain, outcome, expected)

        self._think_count += 1

        thought = {
            "task": task,
            "domain": domain,
            "active_brains": active_brains,
            "route_weights": route_weights,
            "confidence": confidence_score,
            "pattern": pattern_result,
            "latency_ms": (time.time() - start_time) * 1000,
            "timestamp": time.time(),
        }

        self._thought_history.append(thought)
        if len(self._thought_history) > self._max_history:
            self._thought_history = self._thought_history[-self._max_history:]

        self.exploration.step()
        self._update_curricula(active_brains, brain_confidences)

        return {
            "thought_id": self._think_count,
            "active_brains": active_brains,
            "route_weights": route_weights,
            "confidence": confidence_score,
            "pattern": pattern_result,
            "latency_ms": thought["latency_ms"],
            "merged_output_shape": list(merged.shape),
        }

    def _update_curricula(self, active_brains: List[str], confidences: Dict[str, torch.Tensor]):
        for name in active_brains:
            if name in confidences:
                avg_conf = float(confidences[name].mean().item())
                success = avg_conf > 0.6
                self.router.update_curriculum(name, success)

    def awake(self, restore: bool = True) -> None:
        if self._awake:
            return
        self._awake = True
        self._start_time = time.time()
        self._think_count = 0

        for name, brain in self.brains.items():
            brain.to(self.config.device)
            brain.train(False)

        if restore:
            state_path = os.path.expanduser("~/.nicto/neural/consciousness_state.json")
            if os.path.exists(state_path):
                try:
                    self.load(state_path)
                except Exception:
                    pass

    def sleep(self, save: bool = True) -> None:
        if not self._awake:
            return

        for name, brain in self.brains.items():
            brain.to("cpu")

        if save:
            state_path = os.path.expanduser("~/.nicto/neural/consciousness_state.json")
            try:
                self.save(state_path)
            except Exception:
                pass

        self._awake = False

    def state_dict(self) -> Dict:
        brain_states = {}
        for name, brain in self.brains.items():
            try:
                brain_states[name] = {k: v.cpu().tolist() for k, v in brain.state_dict().items()}
            except Exception:
                brain_states[name] = {}

        return {
            "version": "1.0.0",
            "timestamp": time.time(),
            "think_count": self._think_count,
            "uptime": time.time() - self._start_time if self._start_time > 0 else 0,
            "active_brains": list(self._active_brains),
            "brain_states": brain_states,
            "routing_history": self.router.routing_history[-100:] if hasattr(self.router, 'routing_history') else [],
        }

    def load_state_dict(self, state: Dict) -> None:
        self._think_count = state.get("think_count", 0)
        self._active_brains = state.get("active_brains", [])

        brain_states = state.get("brain_states", {})
        for name, params in brain_states.items():
            if name in self.brains:
                try:
                    state_dict = {
                        k: torch.tensor(v) for k, v in params.items()
                    }
                    self.brains[name].load_state_dict(state_dict, strict=False)
                except Exception:
                    pass

        routing_history = state.get("routing_history", [])
        if hasattr(self.router, 'routing_history'):
            self.router.routing_history = routing_history

    def status(self) -> Dict:
        uptime = time.time() - self._start_time if self._start_time > 0 else 0.0
        elo_summary = {}
        for domain in DOMAINS:
            rankings = self.elo.brain_rankings(domain)
            elo_summary[domain] = {b: r for b, r in rankings}

        memory_usage = 0
        if self.memory_manager is not None:
            try:
                mem_status = self.memory_manager.status()
                memory_usage = sum(
                    s.get("entry_count", 0) for s in mem_status.values()
                )
            except Exception:
                memory_usage = -1

        return {
            "awake": self._awake,
            "uptime_seconds": uptime,
            "think_count": self._think_count,
            "active_brains": list(self._active_brains),
            "elo_summary": elo_summary,
            "memory_usage": memory_usage,
            "brains_loaded": list(self.brains.keys()),
            "device": str(self.config.device),
            "exploration_steps": self.exploration.step_count,
        }

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        state = self.state_dict()
        with open(path, "w") as f:
            json.dump(state, f, indent=2)

    def load(self, path: str) -> None:
        if not os.path.exists(path):
            return
        with open(path) as f:
            state = json.load(f)
        self.load_state_dict(state)

    def reflect(self) -> Dict:
        if len(self._thought_history) < 2:
            return {"insight": "Not enough thoughts to reflect on."}

        recent = self._thought_history[-20:]
        domains = {}
        for t in recent:
            d = t.get("domain", "unknown")
            if d not in domains:
                domains[d] = {"count": 0, "total_conf": 0.0, "latencies": []}
            domains[d]["count"] += 1
            domains[d]["total_conf"] += t.get("confidence", 0)
            domains[d]["latencies"].append(t.get("latency_ms", 0))

        insights = []
        for d, stats in domains.items():
            avg_conf = stats["total_conf"] / max(1, stats["count"])
            avg_lat = np.mean(stats["latencies"]) if stats["latencies"] else 0
            insights.append({
                "domain": d,
                "thoughts": stats["count"],
                "avg_confidence": round(avg_conf, 3),
                "avg_latency_ms": round(avg_lat, 1),
            })

        return {
            "total_thoughts": self._think_count,
            "domain_breakdown": insights,
            "top_domain": max(insights, key=lambda x: x["thoughts"]) if insights else None,
        }
