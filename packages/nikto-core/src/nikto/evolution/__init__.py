"""Autonomous Self-Evolution Loop — NIKTO improves itself automatically."""

from nikto.evolution.engine import (
    EvolutionEngine, EvolutionConfig, EvolutionResult,
    SelfHealer, SelfOptimizer, BenchmarkSuite,
)

__all__ = [
    "EvolutionEngine", "EvolutionConfig", "EvolutionResult",
    "SelfHealer", "SelfOptimizer", "BenchmarkSuite",
]
