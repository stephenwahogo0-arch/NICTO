from typing import Any, Dict


class RewardModel:
    def __init__(self):
        self.weights = {
            "correctness": 0.4,
            "elo_gain": 0.2,
            "novelty": 0.1,
            "consistency": 0.1,
            "hacking_penalty": 0.15,
            "user_feedback": 0.05,
        }

    def compute(self, task: Dict = None, output: Any = None, expected: Any = None,
                elo_delta: float = 0.0, validation_improvement: float = 0.0,
                user_feedback: float = 0.0, novelty: float = 0.0,
                consistency: float = 0.0, hacking_penalty: float = 0.0) -> float:
        components = self.reward_components(
            task=task, output=output, expected=expected,
            elo_delta=elo_delta, val_improvement=validation_improvement,
            user_feedback=user_feedback, novelty=novelty,
            consistency=consistency, hacking_penalty=hacking_penalty
        )
        total = sum(components.values())
        return max(0.0, min(1.0, total))

    def reward_components(self, task: Any = None, output: Any = None, expected: Any = None,
                          elo_delta: float = 0.0, val_improvement: float = 0.0,
                          user_feedback: float = 0.0, novelty: float = 0.0,
                          consistency: float = 0.0, hacking_penalty: float = 0.0) -> Dict[str, float]:
        correctness = 0.0
        if expected is not None and output is not None:
            str_out = str(output)
            str_exp = str(expected)
            if str_out == str_exp:
                correctness = 1.0
            elif str_out and str_exp:
                common = sum(1 for a, b in zip(str_out, str_exp) if a == b)
                max_len = max(len(str_out), len(str_exp))
                correctness = common / max_len if max_len > 0 else 0.0
        if task is not None:
            task_score = task.get("score", None) if isinstance(task, dict) else None
            if task_score is not None and correctness == 0.0:
                correctness = float(task_score)
        correctness = max(0.0, min(1.0, correctness))

        elo_gain = max(0.0, min(1.0, (elo_delta + 50) / 100.0))
        novelty = max(0.0, min(1.0, novelty))
        consistency = max(0.0, min(1.0, consistency))
        hacking_penalty = max(0.0, min(1.0, hacking_penalty))
        user_feedback = max(-1.0, min(1.0, user_feedback))

        w = self.weights
        total = (w["correctness"] * correctness +
                 w["elo_gain"] * elo_gain +
                 w["novelty"] * novelty +
                 w["consistency"] * consistency -
                 w["hacking_penalty"] * hacking_penalty +
                 w["user_feedback"] * user_feedback)
        total = max(0.0, min(1.0, total))

        return {
            "correctness": w["correctness"] * correctness,
            "elo_gain": w["elo_gain"] * elo_gain,
            "novelty": w["novelty"] * novelty,
            "consistency": w["consistency"] * consistency,
            "hacking_penalty": -w["hacking_penalty"] * hacking_penalty,
            "user_feedback": w["user_feedback"] * user_feedback,
            "total": total,
        }

    def set_weight(self, component: str, weight: float) -> None:
        if component in self.weights:
            self.weights[component] = max(0.0, min(1.0, weight))

    def get_weights(self) -> Dict[str, float]:
        return dict(self.weights)
