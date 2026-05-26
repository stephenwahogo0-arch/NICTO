"""Dataset builder — builds training.jsonl from all memory sources."""

import json


class DatasetBuilder:
    """Builds training data from episodic memory, reflections, task history."""

    def __init__(self, memory_manager):
        self.memory = memory_manager

    def build(
        self,
        output_path: str = "/tmp/nicto_training.jsonl",
        max_samples: int = 10000,
    ) -> dict:
        samples = []
        seen_hashes: set[int] = set()

        episodes = self.memory.episodic.recall("all", max_samples)
        for ep in episodes:
            sample = self._episode_to_sample(ep)
            if sample:
                h = hash(str(sample.get("input", "")))
                if h not in seen_hashes:
                    samples.append(sample)
                    seen_hashes.add(h)

        with open(output_path, "w") as f:
            for sample in samples:
                f.write(json.dumps(sample) + "\n")

        return {
            "total_samples": len(samples),
            "output_path": output_path,
            "deduplicated": True,
        }

    def _episode_to_sample(self, episode) -> dict:
        content = episode.content
        if not content:
            return None
        if not isinstance(content, dict):
            return {"input": str(content), "domain": "general", "brains_used": [], "importance": episode.importance}
        return {
            "input": content.get("input", ""),
            "domain": content.get("domain", "general"),
            "brains_used": content.get("brains_used", []),
            "importance": episode.importance,
        }
