"""Improvement engine — generates improvement tasks from weaknesses."""


class ImprovementEngine:
    """Generates improvement tasks based on performance analysis."""

    def __init__(self):
        self._tasks: list[dict] = []

    def analyze_weaknesses(self, elo_system, config) -> list[dict]:
        """Identify weak brain-domain pairs and generate improvement tasks."""
        improvements = []
        for brain in config.brain_names:
            for domain in config.elo_domains:
                rating = elo_system.get_rating(brain, domain)
                if rating < config.elo_base:
                    gap = config.elo_base - rating
                    improvements.append({
                        "brain": brain,
                        "domain": domain,
                        "rating": rating,
                        "gap": gap,
                        "priority": min(1.0, gap / 200.0),
                        "task": f"Train {brain} on {domain} tasks",
                    })

        improvements.sort(key=lambda x: x["priority"], reverse=True)
        self._tasks.extend(improvements)
        return improvements

    def generate_training_tasks(
        self,
        weak_pairs: list[dict],
        n_tasks: int = 10,
    ) -> list[dict]:
        """Generate specific training tasks for weak brain-domain pairs."""
        tasks = []
        for pair in weak_pairs[:n_tasks]:
            tasks.append({
                "brain": pair["brain"],
                "domain": pair["domain"],
                "type": "focused_training",
                "priority": pair["priority"],
                "description": f"Practice {pair['domain']} tasks with {pair['brain']} brain",
            })
        return tasks

    def get_improvement_history(self) -> list[dict]:
        return self._tasks[-20:]
