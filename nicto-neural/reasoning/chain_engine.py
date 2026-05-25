"""Chain-of-thought engine — CoT construction with backtracking."""


class ChainOfThoughtEngine:
    """Builds chain-of-thought reasoning with backtracking support."""

    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self._chains: dict[str, list[str]] = {}

    def start_chain(self, task: str) -> str:
        """Start a new reasoning chain."""
        chain_id = str(hash(task))[:8]
        self._chains[chain_id] = [f"Task: {task[:100]}"]
        return chain_id

    def add_step(self, chain_id: str, step: str) -> bool:
        """Add a reasoning step to the chain."""
        if chain_id not in self._chains:
            return False
        if len(self._chains[chain_id]) >= self.max_depth:
            return False
        self._chains[chain_id].append(step)
        return True

    def backtrack(self, chain_id: str, n_steps: int = 1) -> list[str]:
        """Remove last N steps and return removed steps."""
        if chain_id not in self._chains:
            return []
        removed = []
        for _ in range(min(n_steps, len(self._chains[chain_id]) - 1)):
            removed.append(self._chains[chain_id].pop())
        return removed

    def get_chain(self, chain_id: str) -> list[str]:
        return self._chains.get(chain_id, [])

    def get_depth(self, chain_id: str) -> int:
        return len(self._chains.get(chain_id, []))

    def conclude(self, chain_id: str, conclusion: str) -> dict:
        """Finalize chain with a conclusion."""
        chain = self._chains.get(chain_id, [])
        chain.append(f"Conclusion: {conclusion}")
        return {
            "chain_id": chain_id,
            "steps": chain,
            "depth": len(chain),
            "conclusion": conclusion,
        }

    def build_cot(self, task: str, steps: list[str]) -> dict:
        """Build a complete chain-of-thought from provided steps."""
        chain_id = self.start_chain(task)
        for step in steps:
            self.add_step(chain_id, step)
        return {
            "chain_id": chain_id,
            "chain": self.get_chain(chain_id),
            "depth": self.get_depth(chain_id),
        }
