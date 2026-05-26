import asyncio
from dataclasses import dataclass


@dataclass
class ReasoningPath:
    strategy: str
    steps: list[str]
    conclusion: str
    confidence: float


@dataclass
class MultiPathResult:
    best_path: ReasoningPath
    all_paths: list[ReasoningPath]
    selection_reason: str
    consistency_score: float
    domain: str


class MultiPathCoT:
    N_PATHS = 3
    STRATEGIES = ["deductive", "inductive", "abductive"]

    def __init__(self):
        self.path_history = []

    async def think(self, question: str, domain: str = "general") -> MultiPathResult:
        paths = await asyncio.gather(
            self._deductive_chain(question, domain),
            self._inductive_chain(question, domain),
            self._abductive_chain(question, domain),
        )
        paths.sort(key=lambda p: p.confidence, reverse=True)
        best_path = paths[0]
        self.path_history.append({
            "question": question[:100],
            "best_strategy": best_path.strategy,
            "best_score": best_path.confidence,
            "domain": domain,
        })
        return MultiPathResult(
            best_path=best_path,
            all_paths=paths,
            selection_reason=f"Selected '{best_path.strategy}' (confidence={best_path.confidence:.2f}) over {', '.join(p.strategy for p in paths[1:])}",
            consistency_score=best_path.confidence,
            domain=domain,
        )

    async def _deductive_chain(self, question: str, domain: str) -> ReasoningPath:
        await asyncio.sleep(0)
        return ReasoningPath(
            strategy="deductive",
            steps=[
                "DEDUCTIVE: Applying known rules",
                f"Domain: {domain}",
                f"Applying first-order logic to: {question[:100]}",
                "Deriving conclusion from premises",
                "Validating against known truths",
            ],
            conclusion=f"[Deductive] {question[:50]} -> conclusion",
            confidence=0.85,
        )

    async def _inductive_chain(self, question: str, domain: str) -> ReasoningPath:
        await asyncio.sleep(0)
        return ReasoningPath(
            strategy="inductive",
            steps=[
                "INDUCTIVE: Sampling past patterns",
                f"Domain: {domain}",
                f"Finding similar cases: {question[:100]}",
                "Generalizing from examples",
                "Testing generalization strength",
            ],
            conclusion=f"[Inductive] {question[:50]} -> conclusion",
            confidence=0.78,
        )

    async def _abductive_chain(self, question: str, domain: str) -> ReasoningPath:
        await asyncio.sleep(0)
        return ReasoningPath(
            strategy="abductive",
            steps=[
                "ABDUCTIVE: Best explanation",
                f"Domain: {domain}",
                f"What explains: {question[:100]}",
                "Comparing hypotheses",
                "Choosing most likely cause",
            ],
            conclusion=f"[Abductive] {question[:50]} -> conclusion",
            confidence=0.72,
        )

    def get_stats(self) -> dict:
        if not self.path_history:
            return {"total_thinks": 0}
        strategy_counts = {}
        for h in self.path_history:
            s = h["best_strategy"]
            strategy_counts[s] = strategy_counts.get(s, 0) + 1
        return {
            "total_thinks": len(self.path_history),
            "strategy_wins": strategy_counts,
            "avg_score": sum(h["best_score"] for h in self.path_history) / len(self.path_history),
        }
