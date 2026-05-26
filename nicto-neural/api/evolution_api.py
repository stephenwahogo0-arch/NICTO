"""Evolution API — EvolutionEngine.evaluate() wrapper."""


class EvolutionAPI:
    """Public API for evolution and continuous improvement."""

    def __init__(self, evolution_engine):
        self.engine = evolution_engine

    def evolve(self, n_cycles: int = 1) -> dict:
        return self.engine.evolve(n_cycles)

    def get_status(self) -> dict:
        return self.engine.get_status()

    def validate(self) -> dict:
        return self.engine.validator.evaluate(self.engine.consciousness)
