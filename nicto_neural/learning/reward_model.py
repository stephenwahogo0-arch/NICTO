from typing import Any, Optional


class RewardModel:
    WEIGHTS = {
        "correctness": 0.25,
        "elo_gain": 0.15,
        "novelty": 0.10,
        "consistency": 0.10,
        "hacking_penalty": 0.10,
        "user_feedback": 0.10,
        "challenge_completion": 0.08,
        "truth_preservation": 0.05,
        "learning_progress": 0.05,
        "efficiency": 0.02,
    }

    COMPONENT_DESCRIPTIONS = {
        "correctness": "Accuracy of output vs expected or ground truth",
        "elo_gain": "Competitive rating improvement",
        "novelty": "Creative or unexpected elements in output",
        "consistency": "Internal logical coherence and self-consistency",
        "hacking_penalty": "Penalty for exploiting reward function loopholes",
        "user_feedback": "Explicit approval or rating from human evaluator",
        "challenge_completion": "Task difficulty multiplier for completing hard tasks",
        "truth_preservation": "Staying truthful under pressure (adversarial QA)",
        "learning_progress": "Measurable improvement over own prior performance",
        "efficiency": "Token efficiency — concise but complete answers",
    }

    def __init__(self):
        self._history = []

    def compute(self, task: Any = None, output: Any = None, expected: Any = None,
                elo_delta: float = 0.0, validation_improvement: float = 0.0,
                user_feedback: float = 0.0, novelty: float = 0.0,
                consistency: float = 0.0, hacking_penalty: float = 0.0,
                challenge_completion: float = 0.0, truth_preservation: float = 0.0,
                learning_progress: float = 0.0, efficiency: float = 0.0) -> float:
        components = self.reward_components(
            task=task, output=output, expected=expected,
            elo_delta=elo_delta, val_improvement=validation_improvement,
            user_feedback=user_feedback, novelty=novelty,
            consistency=consistency, hacking_penalty=hacking_penalty,
            challenge_completion=challenge_completion,
            truth_preservation=truth_preservation,
            learning_progress=learning_progress, efficiency=efficiency,
        )
        total = components.get("total", 0.0)
        self._history.append({"total": total, "components": dict(components)})
        if len(self._history) > 1000:
            self._history = self._history[-500:]
        return max(0.0, min(1.0, total))

    def reward_components(self, task: Any = None, output: Any = None, expected: Any = None,
                          elo_delta: float = 0.0, val_improvement: float = 0.0,
                          user_feedback: float = 0.0, novelty: float = 0.0,
                          consistency: float = 0.0, hacking_penalty: float = 0.0,
                          challenge_completion: float = 0.0, truth_preservation: float = 0.0,
                          learning_progress: float = 0.0, efficiency: float = 0.0) -> dict:
        raw = {
            "correctness": self._compute_correctness(task, output, expected),
            "elo_gain": self._compute_elo_gain(elo_delta),
            "novelty": max(0.0, min(1.0, novelty)),
            "consistency": max(0.0, min(1.0, consistency)),
            "hacking_penalty": max(0.0, min(1.0, hacking_penalty)),
            "user_feedback": max(0.0, min(1.0, user_feedback)),
            "challenge_completion": max(0.0, min(1.0, challenge_completion)),
            "truth_preservation": max(0.0, min(1.0, truth_preservation)),
            "learning_progress": max(0.0, min(1.0, learning_progress)),
            "efficiency": max(0.0, min(1.0, efficiency)),
        }
        w = self.WEIGHTS
        weighted = {}
        for comp, raw_val in raw.items():
            weight = w.get(comp, 0.0)
            is_penalty = comp == "hacking_penalty"
            weighted[comp] = (-weight if is_penalty else weight) * raw_val
        weighted["total"] = sum(weighted.values())
        weighted["total"] = max(0.0, min(1.0, weighted["total"]))
        return weighted

    def _compute_correctness(self, task: Any, output: Any, expected: Any) -> float:
        if expected is not None and output is not None:
            str_out = str(output).strip()
            str_exp = str(expected).strip()
            if str_out == str_exp:
                return 1.0
            if str_out and str_exp:
                common = sum(1 for a, b in zip(str_out, str_exp) if a == b)
                max_len = max(len(str_out), len(str_exp))
                return max(0.0, min(1.0, common / max_len))
        if isinstance(task, dict) and "score" in task:
            return float(task["score"])
        return 0.0

    def _compute_elo_gain(self, elo_delta: float) -> float:
        return max(0.0, min(1.0, (elo_delta + 50) / 100.0))

    def explain_reward(self, task: Any = None, output: Any = None, expected: Any = None,
                       **kwargs) -> str:
        components = self.reward_components(task=task, output=output, expected=expected, **kwargs)
        lines = [f"Total reward: {components.get('total', 0.0):.3f}"]
        w = self.WEIGHTS
        for comp, desc in self.COMPONENT_DESCRIPTIONS.items():
            raw_key = comp
            raw = kwargs.get(comp, 0.0)
            contrib = components.get(comp, 0.0)
            weight = w.get(comp, 0.0)
            bar_len = max(1, int(abs(contrib) * 20))
            bar = "#" * bar_len + "." * (20 - bar_len)
            sign = "+" if contrib >= 0 else ""
            lines.append(f"  {comp:25s} {sign}{contrib:.3f}  [{bar}]  raw={raw:.2f} w={weight:.2f}  {desc}")
        return "\n".join(lines)

    def get_component_breakdown(self, task: Any = None, output: Any = None, expected: Any = None,
                                **kwargs) -> dict:
        components = self.reward_components(task=task, output=output, expected=expected, **kwargs)
        breakdown = {"total_reward": components.get("total", 0.0), "components": {}}
        for comp in self.WEIGHTS:
            raw_val = kwargs.get(comp, 0.0)
            breakdown["components"][comp] = {
                "raw_value": raw_val,
                "weight": self.WEIGHTS[comp],
                "weighted_contribution": components.get(comp, 0.0),
                "description": self.COMPONENT_DESCRIPTIONS.get(comp, ""),
            }
        return breakdown

    def get_history_stats(self) -> dict:
        if not self._history:
            return {"total_episodes": 0}
        totals = [h["total"] for h in self._history]
        return {
            "total_episodes": len(self._history),
            "mean": sum(totals) / len(totals),
            "min": min(totals),
            "max": max(totals),
            "recent_mean": sum(totals[-100:]) / min(100, len(totals)),
        }

    def get_weights(self) -> dict:
        return dict(self.WEIGHTS)

    def set_weight(self, component: str, weight: float) -> None:
        if component in self.WEIGHTS:
            self.WEIGHTS[component] = max(0.0, min(1.0, weight))
        else:
            raise ValueError(f"Unknown reward component: {component}")

    def get_component_descriptions(self) -> dict:
        return dict(self.COMPONENT_DESCRIPTIONS)
