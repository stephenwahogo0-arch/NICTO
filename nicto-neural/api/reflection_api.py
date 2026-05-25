"""Reflection API — ReflectionEngine.reflect() wrapper."""


class ReflectionAPI:
    """Public API for reflection and self-improvement."""

    def __init__(self, reflection_engine):
        self.engine = reflection_engine

    def reflect(
        self,
        task: str,
        output: str,
        confidence: float,
        brains_used: list,
        domain: str,
        quality: float = 0.5,
    ) -> dict:
        return self.engine.reflect(task, output, confidence, brains_used, domain, quality)

    def get_suggestions(self, n: int = 10) -> list[str]:
        return self.engine.get_improvement_suggestions(n)

    def get_stats(self) -> dict:
        return self.engine.get_stats()
