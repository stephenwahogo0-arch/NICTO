import time
from typing import Any, Dict, List, Optional


class FeedbackLoop:
    def __init__(self, trainer=None, dataset_builder=None, reward_model=None,
                 evaluator=None, reflection_engine=None, curriculum=None,
                 memory_manager=None):
        self.trainer = trainer
        self.dataset_builder = dataset_builder
        self.reward_model = reward_model
        self.evaluator = evaluator
        self.reflection_engine = reflection_engine
        self.curriculum = curriculum
        self.memory = memory_manager

    def run_once(self) -> Dict:
        dataset = self.collect()
        evaluation = self.evaluate(dataset)
        self.store(evaluation)
        improvement_triggered = self.improve(evaluation)
        curriculum_unlocked = self.curriculum_step()
        return {
            "collected": len(dataset),
            "accuracy": evaluation.get("accuracy", 0.0),
            "improvement_triggered": improvement_triggered,
            "curriculum_unlocked": curriculum_unlocked,
            "timestamp": time.time(),
        }

    def collect(self) -> List[Dict]:
        if self.dataset_builder:
            return self.dataset_builder.build()
        return []

    def evaluate(self, dataset: List[Dict]) -> Dict:
        if not dataset:
            return {"accuracy": 0.0, "count": 0, "by_domain": {}, "by_brain": {}}
        correct = 0
        by_domain: Dict[str, List[float]] = {}
        by_brain: Dict[str, List[float]] = {}
        for example in dataset:
            domain = example.get("domain", "general")
            brain = example.get("brain_used", "default")
            output = example.get("output", "")
            expected = example.get("expected", "")
            score = 0.0
            if self.evaluator:
                result = self.evaluator.score(example, output, expected)
                score = result.get("total", 0.0)
            else:
                score = example.get("score", 0.0)
                if expected and output and str(output) == str(expected):
                    score = 1.0
            if score >= 0.7:
                correct += 1
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(score)
            if brain not in by_brain:
                by_brain[brain] = []
            by_brain[brain].append(score)

        accuracy = correct / len(dataset)
        return {
            "accuracy": accuracy,
            "count": len(dataset),
            "correct": correct,
            "by_domain": {d: sum(s) / len(s) for d, s in by_domain.items()},
            "by_brain": {b: sum(s) / len(s) for b, s in by_brain.items()},
        }

    def store(self, results: Dict) -> None:
        if self.memory:
            self.memory.store_performance({
                "type": "feedback_cycle",
                "accuracy": results.get("accuracy", 0.0),
                "count": results.get("count", 0),
                "by_domain": results.get("by_domain", {}),
                "by_brain": results.get("by_brain", {}),
                "timestamp": time.time(),
            })
        if self.reflection_engine and results.get("count", 0) > 0:
            for domain, acc in results.get("by_domain", {}).items():
                self.reflection_engine.reflect(
                    {"input": f"Feedback cycle evaluation for {domain}", "domain": domain},
                    {"total": acc, "accuracy": acc},
                )

    def improve(self, evaluation: Dict) -> bool:
        accuracy = evaluation.get("accuracy", 0.0)
        if accuracy < 0.7 and self.memory:
            self.memory.store_reflection({
                "type": "improvement_trigger",
                "reason": f"Accuracy {accuracy:.3f} below threshold 0.7",
                "evaluation": evaluation,
                "timestamp": time.time(),
            })
            return True
        return False

    def full_cycle(self) -> Dict:
        cycle_start = time.time()
        result = self.run_once()
        result["cycle_time"] = time.time() - cycle_start
        return result

    def curriculum_step(self) -> bool:
        if not self.curriculum or not self.memory:
            return False
        unlocked_any = False
        brains = set()
        domains = set()
        for perf in self.memory.performance:
            b = perf.get("brain", "default")
            d = perf.get("domain", "general")
            brains.add(b)
            domains.add(d)
        for brain in brains:
            for domain in domains:
                history = self.memory.get_accuracy_history(brain, domain)
                if self.curriculum.should_unlock(brain, domain, history):
                    new_level = self.curriculum.unlock_next(brain, domain)
                    self.memory.store_reflection({
                        "type": "curriculum_unlock",
                        "brain": brain,
                        "domain": domain,
                        "new_level": new_level,
                        "timestamp": time.time(),
                    })
                    unlocked_any = True
        return unlocked_any
