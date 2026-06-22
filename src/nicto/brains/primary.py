"""Primary Brain — general reasoning (stub for Phase 1)."""
from __future__ import annotations

from .base import Brain, BrainConfig, BrainResponse


class PrimaryBrain(Brain):
    """General reasoning brain."""

    def __init__(self, config: Optional[BrainConfig] = None):
        if config is None:
            config = BrainConfig(
                model_name="primary-reasoner",
                model_size_gb=2.0,
                quantization_bits=32,
                max_latency_ms=1000.0,
                timeout_seconds=30.0
            )
        super().__init__(config)

    def _load_model(self) -> Any:
        """Load the primary brain's model. For Phase 1, we return a dummy object."""
        return object()

    def _process_internal(self, prompt: str, **kwargs) -> str:
        """Process a prompt by returning a simple response."""
        # In a real implementation, this would use the model to generate a response.
        # For Phase 1, we return a placeholder.
        return f"I processed your request: '{prompt}' using the Primary Brain."