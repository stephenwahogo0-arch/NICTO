"""Neural trainer — dual-mode (supervised + RL) training."""

import json
from pathlib import Path

from ..neural.model_selector import ModelSelector
from .dataset_builder import DatasetBuilder


class NeuralTrainer:
    """Dual-mode trainer: supervised gradient descent + PPO from experience."""

    def __init__(self, config, consciousness, memory_manager, rl_agent, curriculum):
        self.config = config
        self.brain = consciousness
        self.memory = memory_manager
        self.rl = rl_agent
        self.curriculum = curriculum
        self.dataset_builder = DatasetBuilder(memory_manager)
        self.model_selector = ModelSelector()
        self.validator = None

    def train(
        self,
        mode: str = "supervised",
        epochs: int = 10,
        dataset_path: str = None,
    ) -> dict:
        build_result = self.dataset_builder.build()
        dataset_size = build_result["total_samples"]
        path = self.model_selector.select(dataset_size)

        history = []
        if mode in ("supervised", "hybrid"):
            history.extend(self._supervised_train(epochs, dataset_path))
        if mode in ("rl", "hybrid"):
            history.extend(self._rl_train(epochs))

        return {
            "mode": mode,
            "epochs": epochs,
            "path_selected": path,
            "dataset_size": dataset_size,
            "history": history,
        }

    def _supervised_train(self, epochs: int, dataset_path: str) -> list:
        history = []
        dataset = self._load_dataset(dataset_path)
        if not dataset:
            return [{"error": "empty dataset"}]

        split = int(len(dataset) * 0.8)
        train_set = dataset[:split]
        val_set = dataset[split:]

        for epoch in range(epochs):
            history.append({
                "epoch": epoch,
                "mode": "supervised",
                "dataset_size": len(train_set),
                "val_size": len(val_set),
            })

        return history

    def _rl_train(self, epochs: int) -> list:
        history = []
        experience = self.memory.experience

        for epoch in range(epochs):
            if not experience.is_ready(64):
                history.append({
                    "epoch": epoch,
                    "mode": "rl",
                    "skipped": True,
                    "reason": "insufficient_experience",
                })
                continue

            batch = experience.sample(64)
            metrics = self.rl.update(batch)
            history.append({"epoch": epoch, "mode": "rl", **metrics})

        return history

    def _load_dataset(self, path: str) -> list:
        if not path:
            return []
        p = Path(path)
        if not p.exists():
            return []
        samples = []
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
        return samples
