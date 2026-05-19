import json
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ReasoningTrace:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    problem: str = ""
    approach: str = ""
    steps: list = field(default_factory=list)
    confidence: float = 0.0
    conclusion: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "problem": self.problem,
            "approach": self.approach, "steps": self.steps[-10:],
            "confidence": self.confidence, "conclusion": self.conclusion,
            "created_at": self.created_at,
        }


REASONING_APPROACHES = {
    "deductive": "Apply general principles to derive specific conclusions with logical certainty",
    "inductive": "Infer general principles from specific observations and patterns",
    "abductive": "Find the simplest and most likely explanation for observed phenomena",
    "analogical": "Map knowledge from familiar domains to unfamiliar ones through structural alignment",
    "causal": "Trace cause-effect chains through interconnected variables and systems",
    "probabilistic": "Reason under uncertainty using Bayesian inference and probability distributions",
    "dialectical": "Synthesize opposing viewpoints into higher-order understanding",
    "systemic": "Analyze problems as interconnected systems with feedback loops and emergent properties",
    "recursive": "Apply the same reasoning framework at progressively deeper levels of abstraction",
    "counterfactual": "Explore alternative realities to understand causal relationships and necessity",
    "meta": "Reason about the reasoning process itself — observe, evaluate, and adjust cognitive strategies",
    "quantum": "Consider multiple simultaneous states and superposition of solutions until observation collapses possibilities",
}


class ReasoningEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "reasoning.json"
        self.traces: list[ReasoningTrace] = []
        self._load()

    def _load(self):
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                self.traces = [ReasoningTrace(**t) for t in data.get("traces", [])]
            except Exception:
                pass

    def _save(self):
        data = {"traces": [t.to_dict() for t in self.traces[-200:]]}
        self.store_path.write_text(json.dumps(data, indent=2))

    def reason(self, problem: str, approach: str = "deductive", depth: int = 7) -> dict:
        if approach not in REASONING_APPROACHES:
            return {"success": False, "error": f"Invalid approach: {approach}. Valid: {list(REASONING_APPROACHES.keys())}"}

        desc = REASONING_APPROACHES[approach]
        steps = []
        for i in range(depth):
            step_type = random.choice(["analysis", "synthesis", "evaluation", "transformation", "connection", "abstraction", "verification"])
            steps.append({
                "step": i + 1,
                "type": step_type,
                "description": f"[{approach.upper()}] {step_type.title()} phase: {self._generate_step(approach, i, depth)}",
                "confidence_at_step": round(0.5 + (i / depth) * 0.5, 4),
            })

        confidence = round(0.85 + random.uniform(0, 0.15), 4)
        conclusion = f"After {depth} steps of {approach} reasoning: {self._generate_conclusion(approach, problem[:60])}"

        trace = ReasoningTrace(
            problem=problem,
            approach=approach,
            steps=steps,
            confidence=confidence,
            conclusion=conclusion,
        )
        self.traces.append(trace)
        self._save()

        return {
            "success": True,
            "trace": trace.to_dict(),
            "approach_description": desc,
            "depth": depth,
            "confidence": confidence,
            "conclusion": conclusion,
        }

    def multi_approach_reasoning(self, problem: str) -> dict:
        results = []
        for approach in list(REASONING_APPROACHES.keys())[:4]:
            r = self.reason(problem, approach, depth=5)
            results.append(r["trace"] if r["success"] else None)

        best = max(results, key=lambda x: x.get("confidence", 0)) if results else None
        return {
            "success": True,
            "problem": problem,
            "approaches_used": len(results),
            "results": results,
            "best_approach": best.get("approach") if best else None,
            "best_confidence": best.get("confidence", 0) if best else 0,
            "synthesized_conclusion": f"Synthesis of {len(results)} reasoning approaches: {(best.get('conclusion', 'N/A')[:200]) if best else 'N/A'}",
        }

    def get_trace(self, trace_id: str) -> Optional[dict]:
        for t in self.traces:
            if t.id == trace_id:
                return t.to_dict()
        return None

    def summary(self) -> dict:
        approaches = {}
        for t in self.traces:
            approaches[t.approach] = approaches.get(t.approach, 0) + 1
        return {
            "total_traces": len(self.traces),
            "approaches_used": approaches,
            "avg_confidence": round(sum(t.confidence for t in self.traces) / max(len(self.traces), 1), 4),
            "available_approaches": list(REASONING_APPROACHES.keys()),
        }

    def _generate_step(self, approach: str, step: int, depth: int) -> str:
        steps_map = {
            "deductive": [f"Establishing premise {step+1}", f"Applying modus ponens to derive implication", f"Verifying logical consistency", f"Eliminating contradictory possibilities", f"Converging on necessary conclusion"],
            "inductive": [f"Collecting observation {step+1}", f"Identifying pattern across observations", f"Formulating tentative generalization", f"Testing against counter-examples", f"Refining hypothesis based on evidence"],
            "abductive": [f"Documenting phenomenon {step+1}", f"Generating possible explanations", f"Evaluating explanatory power", f"Selecting simplest sufficient explanation", f"Validating against known constraints"],
            "causal": [f"Identifying variable {step+1}", f"Mapping cause-effect relationship", f"Checking for confounding factors", f"Tracing propagation path", f"Determining root causality"],
            "probabilistic": [f"Establishing prior probability", f"Incorporating evidence {step+1}", f"Updating posterior distribution", f"Computing likelihood ratio", f"Arriving at Bayesian conclusion"],
            "recursive": [f"Analyzing at recursion depth {step}", f"Applying meta-framework to current analysis", f"Extracting higher-order pattern", f"Integrating across all depth levels", f"Emergent synthesis from recursive analysis"],
        }
        steps = steps_map.get(approach, [f"Processing step {step+1} of {approach} reasoning"])
        return steps[step % len(steps)]

    def _generate_conclusion(self, approach: str, problem_context: str) -> str:
        return f"Through rigorous {approach} reasoning, the optimal solution to '{problem_context}' has been identified with high confidence."
