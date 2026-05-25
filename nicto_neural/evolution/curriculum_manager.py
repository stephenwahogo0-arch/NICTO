import time
from typing import Any, Dict, List, Optional


class CurriculumManager:
    def __init__(self, curriculum=None, memory_manager=None):
        self.curriculum = curriculum
        self.memory = memory_manager
        self.milestones: Dict[str, Dict[str, List[float]]] = {}

    def get_level(self, brain: str, domain: str) -> int:
        if self.curriculum:
            return self.curriculum.get_level(brain, domain)
        return 0

    def update_level(self, brain: str, domain: str) -> None:
        if not self.curriculum or not self.memory:
            return
        history = self.memory.get_accuracy_history(brain, domain)
        if self.curriculum.should_unlock(brain, domain, history):
            new_level = self.curriculum.unlock_next(brain, domain)
            if self.memory:
                self.memory.store_reflection({
                    "type": "level_up",
                    "brain": brain,
                    "domain": domain,
                    "new_level": new_level,
                    "accuracy_history": history,
                    "timestamp": time.time(),
                })
                self.memory.store_performance({
                    "type": "curriculum_level_up",
                    "brain": brain,
                    "domain": domain,
                    "level": new_level,
                })

    def get_available_tasks(self, brain: str, domain: str, pool: List[Dict]) -> List[Dict]:
        level = self.get_level(brain, domain)
        return [t for t in pool if t.get("difficulty", 0) <= level]

    def next_milestone(self, brain: str, domain: str) -> Dict:
        current_level = self.get_level(brain, domain)
        if brain not in self.milestones:
            self.milestones[brain] = {}
        if domain not in self.milestones[brain]:
            self.milestones[brain][domain] = []

        milestones = {
            0: "Understand basic terminology and simple tasks",
            1: "Solve straightforward problems with guidance",
            2: "Independently solve medium-complexity problems",
            3: "Handle complex multi-step problems",
            4: "Expert-level problem solving across the domain",
            5: "Mastery: teach others and innovate in the domain",
        }
        next_level = min(current_level + 1, 5)
        history = []
        if self.memory:
            history = self.memory.get_accuracy_history(brain, domain)
        plateau = False
        if self.curriculum:
            plateau = self.curriculum.plateau_detected(history)
        return {
            "brain": brain,
            "domain": domain,
            "current_level": current_level,
            "next_level": next_level if next_level > current_level else None,
            "next_milestone_description": milestones.get(next_level, "Completed all levels"),
            "accuracy_history": history[-10:] if history else [],
            "plateau_detected": plateau,
            "should_unlock": self.curriculum.should_unlock(brain, domain, history) if self.curriculum else False,
        }

    def progress_report(self) -> Dict:
        brains = set()
        domains = set()
        if self.memory:
            for p in self.memory.performance:
                b = p.get("brain", "default")
                d = p.get("domain", "general")
                brains.add(b)
                domains.add(d)
        if not brains:
            brains = {"default"}
        if not domains:
            domains = {"general"}
        report = {}
        for brain in brains:
            report[brain] = {}
            for domain in domains:
                report[brain][domain] = self.next_milestone(brain, domain)
        summary = {"total_brains": len(brains), "total_domains": len(domains)}
        avg_levels = []
        for brain, domains_dict in report.items():
            for domain, info in domains_dict.items():
                avg_levels.append(info["current_level"])
        summary["average_level"] = sum(avg_levels) / len(avg_levels) if avg_levels else 0.0
        summary["milestones"] = report
        return summary
