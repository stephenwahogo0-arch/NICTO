"""Task feature engine — converts raw task input into 15-dim state vector."""

import torch


class TaskFeatureEngine:
    """Converts raw task input into a 15-dimensional state vector for routing."""

    TASK_TYPES = {
        "code": 0, "question": 1, "creative": 2,
        "plan": 3, "retrieve": 4, "analyze": 5,
    }

    DOMAINS = {
        "math": 0, "language": 1, "logic": 2,
        "design": 3, "strategy": 4, "knowledge": 5,
        "cybersecurity": 6, "general": 7, "code": 8, "creative": 9,
    }

    def extract(self, task: str, context: dict = None) -> torch.Tensor:
        """Extract 15-dim feature vector from task."""
        ctx = context or {}

        task_type = self._detect_task_type(task)
        domain = self._detect_domain(task)
        complexity = self._estimate_complexity(task)

        features = [
            float(self.TASK_TYPES.get(task_type, 7)),
            float(self.DOMAINS.get(domain, 7)),
            complexity,
            float(ctx.get("reasoning_depth", 0)),
            float(ctx.get("confidence_trajectory", 0.0)),
            float(ctx.get("memory_recall_count", 0)),
            min(float(ctx.get("recency_hours", 24.0)), 168.0),
            float(ctx.get("brain_activation_count", 0)),
            min(float(ctx.get("time_elapsed_ms", 0.0)), 10000.0),
            float(ctx.get("tool_call_frequency", 0)),
            float(ctx.get("coherence_score", 0.5)),
            float(ctx.get("exploration_rate", 0.1)),
            float(ctx.get("curriculum_level", 0)),
            float(ctx.get("reward_trajectory", 0.0)),
            float(ctx.get("hacking_flag", 0)),
        ]
        return torch.tensor(features, dtype=torch.float32)

    def _detect_task_type(self, task: str) -> str:
        t = task.lower()
        if any(k in t for k in ["def ", "function", "code", "script", "implement"]):
            return "code"
        if any(k in t for k in ["plan", "strategy", "design", "architect"]):
            return "plan"
        if any(k in t for k in ["create", "write", "generate", "compose"]):
            return "creative"
        if any(k in t for k in ["find", "search", "lookup", "retrieve"]):
            return "retrieve"
        if any(k in t for k in ["analyze", "explain", "why", "how"]):
            return "analyze"
        return "question"

    def _detect_domain(self, task: str) -> str:
        t = task.lower()
        if any(k in t for k in ["hack", "pentest", "vulnerability", "exploit"]):
            return "cybersecurity"
        if any(k in t for k in ["math", "calculate", "equation", "number"]):
            return "math"
        if any(k in t for k in ["code", "python", "javascript", "function"]):
            return "code"
        if any(k in t for k in ["strategy", "plan", "goal", "objective"]):
            return "strategy"
        if any(k in t for k in ["design", "create", "art", "style"]):
            return "design"
        return "general"

    def _estimate_complexity(self, task: str) -> float:
        words = len(task.split())
        complexity = min(1.0, words / 100.0)
        if any(k in task.lower() for k in ["multi-step", "complex", "advanced"]):
            complexity = min(1.0, complexity + 0.3)
        return complexity
