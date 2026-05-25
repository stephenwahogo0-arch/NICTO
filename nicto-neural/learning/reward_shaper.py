"""Reward shaper — shapes raw reward signals, prevents reward hacking."""


class RewardShaper:
    """R = α*correctness + β*elo_gain + γ*novelty + δ*consistency - ε*hacking_penalty."""

    def __init__(self):
        self.alpha = 10.0
        self.beta = 5.0
        self.gamma = 2.0
        self.delta = 1.0
        self.epsilon = 10.0

    def shape(
        self,
        correctness: float,
        elo_delta: float = 0.0,
        is_novel: bool = False,
        consistency_score: float = 0.5,
        hacking_detected: bool = False,
    ) -> dict:
        base = correctness * self.alpha
        elo_component = max(-1.0, min(1.0, elo_delta / 100.0)) * self.beta
        novelty = self.gamma if is_novel else 0.0
        consistency = consistency_score * self.delta
        creativity_bonus = 1.5 if correctness > 0.7 else 0.0
        hack_penalty = self.epsilon if hacking_detected else 0.0

        total = base + elo_component + novelty + consistency + creativity_bonus - hack_penalty

        return {
            "total": total,
            "base": base,
            "elo_component": elo_component,
            "novelty": novelty,
            "consistency": consistency,
            "creativity_bonus": creativity_bonus,
            "hack_penalty": hack_penalty,
            "correctness": correctness,
        }
