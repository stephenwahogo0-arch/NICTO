"""CognitiveReversalEngine — reverse cognitive biases and reframe thinking."""


class CognitiveReversalEngine:
    def __init__(self):
        self.biases_mapped = 0
        self.bias_types = [
            "confirmation", "anchoring", "availability",
            "dunning_kruger", "hindsight", "negativity"
        ]

    def reverse(self, thought_pattern: str) -> dict:
        self.biases_mapped += 1
        bias = self.bias_types[self.biases_mapped % len(self.bias_types)]
        return {
            "input": thought_pattern,
            "bias_detected": bias,
            "reversed": f"Anti-{bias}: {thought_pattern[::-1] if len(thought_pattern) > 5 else thought_pattern}",
            "biases_mapped": self.biases_mapped
        }

    def status(self) -> dict:
        return {"biases_mapped": self.biases_mapped, "types": self.bias_types}
