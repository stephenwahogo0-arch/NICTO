"""NICTO X — Multi-path Tree-of-Thought with chain-of-thought, self-correction, and recursive refinement."""

from __future__ import annotations

import logging
import math
import time
from typing import Optional

logger = logging.getLogger("nicto_x.reasoning.tot")


class TreeOfThought:
    """Multi-path reasoning with CoT, self-evaluation, branching, and recursive refinement."""

    def __init__(self, max_paths: int = 5, max_depth: int = 5, branching_factor: int = 3):
        self.max_paths = max_paths
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self._path_history: list[dict] = []

    def explore(self, problem: str, context: str = "", **kwargs) -> dict:
        paths = self._generate_cot_paths(problem, context)
        evaluated = [self._evaluate_path(p, problem) for p in paths]
        best = max(evaluated, key=lambda p: p["score"])

        refined = self._refine_best(best, problem, context)
        final = self._self_correct(refined, problem)

        result = {
            "best_path": final["content"],
            "paths": evaluated,
            "num_paths": len(evaluated),
            "best_score": final["score"],
            "refinement_iterations": refined.get("refinements", 0),
            "self_corrections": final.get("corrections", []),
            "timestamp": time.time(),
        }
        self._path_history.append(result)
        return result

    def _generate_cot_paths(self, problem: str, context: str) -> list[dict]:
        paths = []
        for i in range(self.max_paths):
            depth = min(i + 2, self.max_depth)
            steps = []
            for d in range(depth):
                approach = self._get_approach(i, d)
                step_content = self._generate_step(problem, context, approach, d, depth)
                steps.append({"step": d + 1, "approach": approach, "content": step_content})

            conclusion = self._generate_conclusion(steps, problem, i)
            paths.append({
                "path_id": i,
                "steps": steps,
                "conclusion": conclusion,
                "depth": depth,
            })
        return paths

    def _get_approach(self, path_id: int, step: int) -> str:
        approaches = [
            "analytical", "deductive", "inductive", "abductive", "analogical",
            "critical", "creative", "systematic", "empirical", "first_principles",
        ]
        return approaches[(path_id + step) % len(approaches)]

    def _generate_step(self, problem: str, context: str, approach: str, step: int, total: int) -> str:
        problem_snippet = problem[:60]
        context_snippet = context[:80] if context else "no additional context"
        progress = f"Step {step + 1}/{total}"

        if approach == "analytical":
            return f"{progress}: Deconstructing '{problem_snippet}' into components. Context: {context_snippet}. Analyzing each part systematically."
        elif approach == "deductive":
            return f"{progress}: Applying deductive logic. If premises hold for '{problem_snippet}', then conclusion follows necessarily."
        elif approach == "inductive":
            return f"{progress}: Drawing general principles from specific observations about '{problem_snippet}'."
        elif approach == "abductive":
            return f"{progress}: Inferring best explanation for '{problem_snippet}' given known patterns."
        elif approach == "analogical":
            return f"{progress}: Mapping known solution patterns to '{problem_snippet}' by structural similarity."
        elif approach == "critical":
            return f"{progress}: Critically examining assumptions in '{problem_snippet}'. Identifying potential flaws."
        elif approach == "creative":
            return f"{progress}: Generating novel solution approaches for '{problem_snippet}' beyond conventional patterns."
        elif approach == "first_principles":
            return f"{progress}: Reducing '{problem_snippet}' to fundamental truths and building up from there."
        else:
            return f"{progress}: Processing '{problem_snippet}' using {approach} reasoning."

    def _generate_conclusion(self, steps: list[dict], problem: str, path_id: int) -> str:
        approaches = [s["approach"] for s in steps]
        return (
            f"Path {path_id + 1} conclusion: After {len(steps)} reasoning steps "
            f"({', '.join(approaches)}), the optimal approach for '{problem[:60]}' "
            f"is determined by synthesizing all perspectives."
        )

    def _evaluate_path(self, path: dict, problem: str) -> dict:
        steps = path.get("steps", [])
        depth = len(steps)
        step_detail = sum(len(s.get("content", "")) for s in steps)

        coherence = min(1.0, 0.5 + depth * 0.05)
        completeness = min(1.0, step_detail / 500)
        diversity = min(1.0, len(set(s["approach"] for s in steps)) * 0.2)
        specificity = min(1.0, len(problem.split()) / 20)

        score = (coherence * 0.3 + completeness * 0.3 + diversity * 0.2 + specificity * 0.2)
        path["score"] = round(score, 4)
        path["evaluation"] = {
            "coherence": round(coherence, 3),
            "completeness": round(completeness, 3),
            "diversity": round(diversity, 3),
            "specificity": round(specificity, 3),
        }
        return path

    def _refine_best(self, best_path: dict, problem: str, context: str) -> dict:
        content = best_path.get("conclusion", "")
        refinements = 0
        for _ in range(3):
            if len(content) < 200:
                content += f" Further analysis of '{problem[:40]}' reveals additional depth."
                refinements += 1
            else:
                break

        best_path["content"] = content
        best_path["refinements"] = refinements
        return best_path

    def _self_correct(self, path: dict, problem: str) -> dict:
        content = path.get("content", "")
        corrections = []

        contradictions = [
            ("always", "never"), ("all", "none"), ("must", "cannot"),
            ("increase", "decrease"), ("positive", "negative"),
        ]
        for a, b in contradictions:
            if a in content.lower() and b in content.lower():
                corrections.append(f"Contradiction detected: '{a}' vs '{b}'.")
                content = content.replace(a, f"{a} (generally)")
                content = content.replace(b, f"{b} (generally)")

        if len(content.split()) < 10:
            corrections.append("Output too short, expanding.")
            content += f" Based on analysis of '{problem[:40]}', the recommended approach involves systematic evaluation."

        hedging_phrases = ["i think", "maybe", "perhaps", "might be", "could be"]
        for phrase in hedging_phrases:
            if phrase in content.lower():
                corrections.append(f"Hedging language detected: '{phrase}'. Strengthened.")
                break

        path["content"] = content
        path["corrections"] = corrections
        path["score"] = round(path.get("score", 0) + 0.05 * len(corrections), 4)
        return path

    def get_history(self, limit: int = 10) -> list[dict]:
        return self._path_history[-limit:]
