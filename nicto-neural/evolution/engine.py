"""Evolution engine — central coordinator for continuous improvement."""

from datetime import datetime


class EvolutionEngine:
    """Central coordinator for continuous improvement."""

    def __init__(self, config, consciousness, memory, curriculum, validator):
        self.config = config
        self.consciousness = consciousness
        self.memory = memory
        self.curriculum = curriculum
        self.validator = validator
        self._milestones: list[dict] = []
        self._generation = 0

    def evolve(self, n_cycles: int = 1) -> dict:
        """Run evolution cycles: evaluate -> improve -> validate."""
        results = []
        for cycle in range(n_cycles):
            self._generation += 1

            val_result = self.validator.evaluate(self.consciousness)
            accuracy = val_result.get("accuracy", 0.0)

            improvements = self._suggest_improvements(accuracy)

            if accuracy > 0.85:
                self._add_milestone(f"Generation {self._generation}: accuracy {accuracy:.2%}")

            results.append({
                "generation": self._generation,
                "accuracy": accuracy,
                "improvements": improvements,
                "milestones": len(self._milestones),
            })

        return {"cycles": len(results), "results": results}

    def _suggest_improvements(self, accuracy: float) -> list[str]:
        suggestions = []
        if accuracy < 0.5:
            suggestions.append("Increase training data volume")
            suggestions.append("Adjust learning rate")
        elif accuracy < 0.75:
            suggestions.append("Focus on weak domains")
            suggestions.append("Add domain-specific examples")
        else:
            suggestions.append("Fine-tune with LoRA on edge cases")
        return suggestions

    def _add_milestone(self, description: str) -> None:
        self._milestones.append({
            "description": description,
            "generation": self._generation,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_status(self) -> dict:
        return {
            "generation": self._generation,
            "milestones": len(self._milestones),
            "recent_milestones": self._milestones[-5:],
        }
