"""Feedback loop — continuous improvement from user and system feedback."""


class FeedbackLoop:
    """Captures feedback signals and routes them to appropriate learning subsystems."""

    def __init__(self):
        self._feedback_queue: list[dict] = []
        self._processed: list[dict] = []

    def add_feedback(
        self,
        task: str,
        quality: float,
        source: str = "system",
        correction: str = None,
    ) -> dict:
        """Add feedback entry to the queue."""
        entry = {
            "task": task[:200],
            "quality": quality,
            "source": source,
            "correction": correction,
            "processed": False,
        }
        self._feedback_queue.append(entry)
        return entry

    def process_batch(self, batch_size: int = 10) -> list[dict]:
        """Process pending feedback entries."""
        unprocessed = [f for f in self._feedback_queue if not f["processed"]]
        batch = unprocessed[:batch_size]

        results = []
        for entry in batch:
            entry["processed"] = True
            result = {
                "task": entry["task"],
                "action": self._determine_action(entry),
                "quality": entry["quality"],
            }
            results.append(result)
            self._processed.append(result)

        return results

    def _determine_action(self, entry: dict) -> str:
        if entry["quality"] < 0.3:
            return "retrain_domain"
        if entry["quality"] < 0.6:
            return "add_training_example"
        if entry.get("correction"):
            return "correct_and_learn"
        return "reinforce_positive"

    def get_stats(self) -> dict:
        return {
            "pending": sum(1 for f in self._feedback_queue if not f["processed"]),
            "processed": len(self._processed),
            "total": len(self._feedback_queue),
        }
