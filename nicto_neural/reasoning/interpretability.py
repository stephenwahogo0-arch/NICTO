import numpy as np
import re
from typing import Any, Dict, List, Optional, Tuple


class NeuralConfig:
    def __init__(self, d_model: int = 512, device: str = "cpu"):
        self.d_model = d_model
        self.device = device


class InterpretabilityReporter:
    def __init__(self, config: Optional[NeuralConfig] = None):
        self.config = config if config is not None else NeuralConfig()
        self._brain_complexity: Dict[str, float] = {
            "linear_regression": 0.9,
            "decision_tree": 0.85,
            "random_forest": 0.7,
            "logistic_regression": 0.9,
            "knn": 0.8,
            "naive_bayes": 0.85,
            "svm_linear": 0.75,
            "svm_rbf": 0.4,
            "mlp": 0.4,
            "transformer": 0.25,
            "lstm": 0.3,
            "cnn": 0.45,
            "reasoning_core": 0.35,
            "ensemble_router": 0.5,
            "code_llm": 0.3,
            "language_model": 0.3,
            "creative_llm": 0.25,
            "security_llm": 0.3,
            "research_llm": 0.3,
            "fallback_brain": 0.5,
        }
        self._default_complexity = 0.5

    def score(self, brain: str, task: Dict, output: Any) -> float:
        complexity = self._brain_complexity.get(brain, self._default_complexity)

        task_complexity = len(str(task.get("description", task.get("task", ""))))
        task_penalty = min(0.3, task_complexity / 2000)

        output_len = len(str(output)) if output is not None else 0
        output_penalty = min(0.2, output_len / 5000)

        chain = task.get("chain", task.get("reasoning_chain", []))
        steps = len(chain)
        steps_bonus = min(0.2, steps / 20)

        interpretability = complexity - task_penalty - output_penalty + steps_bonus
        return max(0.0, min(1.0, interpretability))

    def report(self, task: Dict, output: Any, chain: List[str], brain_weights: Dict[str, float]) -> str:
        lines = []
        task_desc = task.get("description", task.get("task", "Unknown task"))

        lines.append("=" * 60)
        lines.append(f"INTERPRETABILITY REPORT")
        lines.append("=" * 60)
        lines.append(f"Task: {task_desc[:100]}{'...' if len(task_desc) > 100 else ''}")
        lines.append("")

        sorted_brains = sorted(brain_weights.items(), key=lambda x: x[1], reverse=True)
        lines.append("Brains Contributing to Decision:")
        for brain_name, weight in sorted_brains:
            bar_len = int(weight * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"  {brain_name:<25s} |{bar}| {weight:.3f}")
        lines.append("")

        lines.append("Reasoning Chain:")
        if chain:
            for i, step in enumerate(chain):
                lines.append(f"  Step {i + 1}: {step[:150]}{'...' if len(step) > 150 else ''}")
        else:
            lines.append("  (No reasoning chain available)")
        lines.append("")

        lines.append("Interpretability Scores:")
        for brain_name in brain_weights:
            brain_score = self.score(brain_name, task, output)
            level = self._score_to_level(brain_score)
            lines.append(f"  {brain_name:<25s} -> {brain_score:.3f} ({level})")
        lines.append("")

        overall = sum(
            self.score(brain, task, output) * weight
            for brain, weight in brain_weights.items()
        ) / max(1, sum(brain_weights.values()))
        lines.append(f"Overall Interpretability: {overall:.3f} ({self._score_to_level(overall)})")
        lines.append("")

        lines.append("Decision Explanation:")
        lines.append(self._generate_explanation(task, output, chain, sorted_brains))
        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _score_to_level(self, score: float) -> str:
        if score >= 0.8:
            return "Fully Transparent"
        if score >= 0.6:
            return "Mostly Transparent"
        if score >= 0.4:
            return "Partially Transparent"
        if score >= 0.2:
            return "Mostly Opaque"
        return "Black Box"

    def _generate_explanation(self, task: Dict, output: Any, chain: List[str], brain_weights: List[Tuple[str, float]]) -> str:
        primary_brain = brain_weights[0][0] if brain_weights else "unknown"
        primary_weight = brain_weights[0][1] if brain_weights else 0.0

        parts = []
        parts.append(f"The primary contributor was '{primary_brain}' with {primary_weight:.1%} influence.")

        if chain:
            first_step = chain[0][:80] if chain[0] else ""
            last_step = chain[-1][:80] if chain[-1] else ""
            steps_count = len(chain)
            parts.append(f"The reasoning process took {steps_count} steps.")
            parts.append(f"It started by: {first_step}")
            parts.append(f"It concluded with: {last_step}")

        output_preview = str(output)[:200] if output is not None else "No output"
        parts.append(f"The final output was: {output_preview}")

        if len(brain_weights) > 1:
            secondary = brain_weights[1][0]
            sec_weight = brain_weights[1][1]
            parts.append(f"A secondary contribution came from '{secondary}' ({sec_weight:.1%} influence).")

        return " ".join(parts)

    def feature_attribution(self, feature_vector: np.ndarray, output: Any) -> Dict[str, float]:
        if feature_vector is None or feature_vector.size == 0:
            return {}

        if isinstance(output, (int, float)):
            target = float(output)
        elif isinstance(output, np.ndarray) and output.size == 1:
            target = float(output.item())
        elif isinstance(output, np.ndarray):
            target = float(np.mean(output))
        else:
            try:
                target = float(str(output).__hash__() % 10000) / 10000.0
            except Exception:
                target = 0.5

        if np.all(feature_vector == 0):
            n = feature_vector.shape[0]
            return {f"feature_{i}": 1.0 / n for i in range(n)}

        contributions = {}
        for i in range(feature_vector.shape[0]):
            val = feature_vector[i]
            if abs(target) > 1e-10:
                contribution = abs(val) / (abs(target) + 1e-10)
            else:
                contribution = abs(val)
            contributions[f"feature_{i}"] = abs(float(contribution))

        total = sum(contributions.values())
        if total > 0:
            for key in contributions:
                contributions[key] /= total

        sorted_contrib = dict(sorted(contributions.items(), key=lambda x: x[1], reverse=True))
        top_n = min(10, len(sorted_contrib))
        return dict(list(sorted_contrib.items())[:top_n])

    def decision_path(self, brain: str, task: Dict) -> List[str]:
        path = []
        task_desc = task.get("description", task.get("task", "Unknown task"))

        complexity = self._brain_complexity.get(brain, self._default_complexity)

        path.append(f"Input: Received task '{task_desc[:60]}...'")

        if complexity > 0.7:
            path.append(f"Stage 1: Direct rule lookup in {brain}")
            path.append(f"Stage 2: Match input features to known patterns")
            path.append(f"Stage 3: Apply decision rule with highest confidence")
            path.append(f"Stage 4: Return output based on matched rule")
        elif complexity > 0.4:
            path.append(f"Stage 1: Embed input into feature space using {brain}")
            path.append(f"Stage 2: Compute weighted combination of features")
            path.append(f"Stage 3: Apply activation function to produce logits")
            path.append(f"Stage 4: Select maximum probability class or generate output")
        else:
            path.append(f"Stage 1: Tokenize and encode input for {brain}")
            path.append(f"Stage 2: Forward through multiple transformer layers with self-attention")
            path.append(f"Stage 3: Apply attention masking and residual connections")
            path.append(f"Stage 4: Decode final hidden state to output space")
            path.append(f"Stage 5: Apply softmax/sampling to generate output distribution")

        path_count = len(task.get("chain", task.get("reasoning_chain", [])))
        if path_count > 0:
            path.append(f"Interleaved with {path_count} explicit reasoning steps")

        path.append(f"Final: Produce output from {brain}")
        return path
