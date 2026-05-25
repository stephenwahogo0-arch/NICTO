"""Curriculum manager — per-domain, per-brain difficulty levels."""


class CurriculumManager:
    """Manages curriculum levels across all brain-domain pairs."""

    def __init__(self, config, curriculum_scheduler):
        self.config = config
        self.scheduler = curriculum_scheduler

    def get_all_levels(self) -> dict:
        """Get levels for all brain-domain pairs."""
        levels = {}
        for brain in self.config.brain_names:
            levels[brain] = {}
            for domain in self.config.elo_domains:
                levels[brain][domain] = {
                    "level": self.scheduler.get_level(brain, domain),
                    "name": self.scheduler.get_level_name(brain, domain),
                }
        return levels

    def advance_if_ready(self, brain: str, domain: str, accuracy: float) -> dict:
        return self.scheduler.record_accuracy(brain, domain, accuracy)

    def get_global_progress(self) -> dict:
        """Calculate global curriculum progress."""
        total = 0
        current = 0
        max_level = self.scheduler.MAX_LEVEL

        for brain in self.config.brain_names:
            for domain in self.config.elo_domains:
                total += max_level
                current += self.scheduler.get_level(brain, domain)

        return {
            "total_possible": total,
            "current_total": current,
            "progress_pct": (current / max(total, 1)) * 100,
        }
