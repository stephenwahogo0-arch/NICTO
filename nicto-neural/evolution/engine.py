import json
import os
import time
from typing import Any, Dict, List, Optional


class EvolutionEngine:
    def __init__(self, memory_manager=None, elo_system=None, trainer=None,
                 feedback_loop=None, curriculum=None, evaluator=None):
        self.memory = memory_manager
        self.elo = elo_system
        self.trainer = trainer
        self.feedback_loop = feedback_loop
        self.curriculum = curriculum
        self.evaluator = evaluator
        self.generation = 0
        self.best_score = 0.0
        self.current_score = 0.0
        self.scores: List[float] = []
        self.training_threshold = 0.6
        self.training_count = 0
        self.last_improvement = 0.0

    def improve(self, task_history: List[Dict]) -> Dict:
        if not task_history:
            return {"generation": self.generation, "score": self.current_score, "improved": False}
        scores = []
        for task in task_history:
            if self.evaluator:
                result = self.evaluator.score(task, task.get("output", ""), task.get("expected", ""))
                scores.append(result.get("total", 0.0))
            else:
                scores.append(task.get("score", 0.0))
        self.current_score = sum(scores) / len(scores) if scores else 0.0
        self.scores.append(self.current_score)
        improved = self.current_score > self.best_score
        if improved:
            self.best_score = self.current_score
            self.last_improvement = time.time()
        self.generation += 1
        if self.memory:
            self.memory.store_performance({
                "type": "evolution_generation",
                "generation": self.generation,
                "score": self.current_score,
                "best_score": self.best_score,
                "improved": improved,
                "timestamp": time.time(),
            })
        if self.current_score < self.training_threshold:
            self.trigger_training(f"Score {self.current_score:.3f} below threshold {self.training_threshold}")
        return {
            "generation": self.generation,
            "score": self.current_score,
            "best_score": self.best_score,
            "improved": improved,
        }

    def evaluate_cycle(self, n_tasks: int = 100) -> Dict:
        if not self.memory:
            return {"accuracy": 0.0, "tasks_evaluated": 0}
        tasks = self.memory.get_task_history(n_tasks)
        if not tasks:
            return {"accuracy": 0.0, "tasks_evaluated": 0}
        correct = 0
        by_domain: Dict[str, List[float]] = {}
        for task in tasks[:n_tasks]:
            domain = task.get("domain", "general")
            score = task.get("score", 0.0)
            if self.evaluator:
                result = self.evaluator.score(task, task.get("output", ""), task.get("expected", ""))
                score = result.get("total", 0.0)
            if score >= 0.7:
                correct += 1
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(score)
        avg_domain = {d: sum(s) / len(s) for d, s in by_domain.items()}
        accuracy = correct / len(tasks)
        self.current_score = accuracy
        self.scores.append(accuracy)
        return {
            "accuracy": accuracy,
            "tasks_evaluated": len(tasks),
            "correct": correct,
            "by_domain": avg_domain,
        }

    def score_current(self) -> float:
        return self.current_score

    def trigger_training(self, reason: str) -> str:
        self.training_count += 1
        training_id = f"train_gen{self.generation}_run{self.training_count}"
        if self.memory:
            self.memory.store_reflection({
                "type": "training_trigger",
                "reason": reason,
                "training_id": training_id,
                "generation": self.generation,
                "timestamp": time.time(),
            })
        if self.trainer:
            if self.memory:
                dataset = self.memory.get_task_history(1000)
                if dataset:
                    self.trainer.train(dataset, mode="supervised", epochs=5)
        return training_id

    def state(self) -> Dict:
        return {
            "generation": self.generation,
            "best_score": self.best_score,
            "current_score": self.current_score,
            "scores": self.scores[-100:] if len(self.scores) > 100 else self.scores,
            "training_count": self.training_count,
            "training_threshold": self.training_threshold,
            "last_improvement": self.last_improvement,
        }

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.state(), f, indent=2)

    def load(self, path: str) -> None:
        if not os.path.exists(path):
            return
        with open(path, "r") as f:
            data = json.load(f)
        self.generation = data.get("generation", 0)
        self.best_score = data.get("best_score", 0.0)
        self.current_score = data.get("current_score", 0.0)
        self.scores = data.get("scores", [])
        self.training_count = data.get("training_count", 0)
        self.training_threshold = data.get("training_threshold", 0.6)
        self.last_improvement = data.get("last_improvement", 0.0)
