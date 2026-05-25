"""Brain API — NeuralConsciousness.think() wrapper."""


class BrainAPI:
    """Public API for brain operations."""

    def __init__(self, consciousness):
        self.consciousness = consciousness

    async def think(self, input_text: str, context: dict = None) -> dict:
        return await self.consciousness.think(input_text, context or {})

    def get_brain_info(self, brain_name: str) -> dict:
        brain = self.consciousness.brains.get(brain_name)
        if not brain:
            return {"error": f"Brain '{brain_name}' not found"}
        return {
            "name": brain.name,
            "specializations": brain.specializations,
        }

    def list_brains(self) -> list[dict]:
        return [
            {"name": b.name, "specializations": b.specializations}
            for b in self.consciousness.brains.values()
        ]

    def get_status(self) -> dict:
        return {
            "awake": self.consciousness._awake,
            "think_count": self.consciousness._think_count,
            "brains": len(self.consciousness.brains),
        }
