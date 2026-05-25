"""Model selector — chooses inference path based on dataset size."""


class ModelSelector:
    """Selects inference path to prevent overfitting on small datasets."""

    THRESHOLDS = {
        "small": 100,
        "medium": 10000,
        "large": 10000,
    }

    def select(
        self,
        dataset_size: int,
        domain: str = "general",
        complexity: float = 0.5,
    ) -> str:
        if dataset_size < self.THRESHOLDS["small"]:
            return "brainboost_fixed"
        elif dataset_size < self.THRESHOLDS["medium"]:
            return "brainboost_trained"
        else:
            return "transformer_rl"

    def get_path_info(self, path: str) -> dict:
        paths = {
            "brainboost_fixed": {
                "description": "Fixed ensemble weights, interpretable",
                "speed": "fast",
                "accuracy": "moderate",
                "compute": "low",
            },
            "brainboost_trained": {
                "description": "Learned ensemble weights, gradient descent",
                "speed": "medium",
                "accuracy": "good",
                "compute": "medium",
            },
            "transformer_rl": {
                "description": "Full transformer + PPO RL",
                "speed": "slow",
                "accuracy": "best",
                "compute": "high",
            },
        }
        return paths.get(path, {})
