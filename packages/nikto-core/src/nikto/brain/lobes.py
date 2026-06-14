"""
Brain Lobes Module for NIKTO.

Implements functional brain lobes with specialized processing capabilities.
Each lobe has a ``process(input, context)`` method that returns a dict.
"""

from typing import Any, Optional
from dataclasses import dataclass, field

from nikto.brain.models import Thought, ThinkingStyle


@dataclass
class BrainLobe:
    """Represents a functional lobe of the brain."""

    name: str
    description: str
    activation_threshold: float = 0.3
    processing_power: float = 1.0
    specialization: Optional[str] = None
    active: bool = True
    load_factor: float = 0.0

    def process(self, input_text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Process *input_text* with this lobe and return a result dict."""
        ctx = context or {}
        return {
            "lobe": self.name,
            "input": input_text,
            "description": self.description,
            "activated": True,
            "confidence": min(1.0, self.processing_power * 0.8),
            "context_keys": list(ctx.keys()),
        }


# Pre-built lobe instances
BRAIN_LOBES: dict[str, BrainLobe] = {
    "frontal": BrainLobe(
        name="frontal",
        description="Executive functions, planning, decision making, and personality expression",
        activation_threshold=0.3,
        processing_power=1.2,
        specialization="executive",
    ),
    "parietal": BrainLobe(
        name="parietal",
        description="Sensory integration, spatial reasoning, and body awareness",
        activation_threshold=0.4,
        processing_power=1.0,
        specialization="sensory",
    ),
    "temporal": BrainLobe(
        name="temporal",
        description="Memory formation, language comprehension, and auditory processing",
        activation_threshold=0.35,
        processing_power=1.1,
        specialization="memory_language",
    ),
    "occipital": BrainLobe(
        name="occipital",
        description="Visual processing and pattern recognition",
        activation_threshold=0.3,
        processing_power=0.9,
        specialization="visual",
    ),
    "limbic": BrainLobe(
        name="limbic",
        description="Emotion, motivation, memory consolidation, and behavior regulation",
        activation_threshold=0.25,
        processing_power=0.8,
        specialization="emotional",
    ),
    "cerebellum": BrainLobe(
        name="cerebellum",
        description="Motor coordination, balance, timing, and procedural learning",
        activation_threshold=0.5,
        processing_power=0.7,
        specialization="motor",
    ),
    "brainstem": BrainLobe(
        name="brainstem",
        description="Basic life functions: breathing, heart rate, arousal, and sleep-wake cycles",
        activation_threshold=0.6,
        processing_power=0.6,
        specialization="autonomic",
    ),
}


class BrainLobes:
    """Manages the brain's functional lobes."""

    def __init__(self) -> None:
        self.lobes: dict[str, BrainLobe] = {}
        self._initialize_default_lobes()

    def _initialize_default_lobes(self) -> None:
        for name, lobe in BRAIN_LOBES.items():
            self.lobes[name] = lobe

    def get_lobe(self, name: str) -> Optional[BrainLobe]:
        """Get a lobe by name (case-insensitive)."""
        return self.lobes.get(name.lower())

    def add_lobe(self, lobe: BrainLobe) -> None:
        """Register a new lobe."""
        self.lobes[lobe.name] = lobe

    def remove_lobe(self, name: str) -> bool:
        """Remove a lobe. Returns True if it existed."""
        if name.lower() in self.lobes:
            del self.lobes[name.lower()]
            return True
        return False

    def get_active_lobes(self) -> dict[str, BrainLobe]:
        """Return only active lobes."""
        return {n: l for n, l in self.lobes.items() if l.active}

    def distribute_load(self, thought: Thought) -> dict[str, float]:
        """Distribute processing load across lobes based on thought style."""
        style_mapping: dict[str, dict[str, float]] = {
            "analytical": {"frontal": 0.4, "parietal": 0.3, "temporal": 0.2, "occipital": 0.1},
            "deductive": {"frontal": 0.5, "parietal": 0.3, "temporal": 0.2},
            "inductive": {"frontal": 0.3, "temporal": 0.4, "parietal": 0.2, "occipital": 0.1},
            "abductive": {"frontal": 0.3, "temporal": 0.3, "parietal": 0.2, "occipital": 0.2},
            "analogical": {"temporal": 0.4, "frontal": 0.3, "occipital": 0.2, "parietal": 0.1},
            "critical": {"frontal": 0.5, "parietal": 0.3, "temporal": 0.2},
            "creative": {"frontal": 0.3, "temporal": 0.3, "occipital": 0.2, "parietal": 0.2},
            "intuitive": {"temporal": 0.4, "frontal": 0.3, "limbic": 0.2, "occipital": 0.1},
        }
        style = thought.style.value if hasattr(thought.style, "value") else str(thought.style)
        base_dist = style_mapping.get(style.lower(), style_mapping["analytical"])
        total = sum(base_dist.values())
        result: dict[str, float] = {}
        for lobe_name, weight in base_dist.items():
            lobe = self.get_lobe(lobe_name)
            if lobe and lobe.active:
                adjusted = (weight / total) * lobe.processing_power
                result[lobe_name] = adjusted
                lobe.load_factor = min(1.0, lobe.load_factor + adjusted * 0.1)
        return result

    def get_status(self) -> dict[str, Any]:
        """Return status of all lobes."""
        return {
            name: {
                "description": lobe.description,
                "activation_threshold": lobe.activation_threshold,
                "specialization": lobe.specialization,
                "active": lobe.active,
                "processing_power": lobe.processing_power,
                "load_factor": lobe.load_factor,
            }
            for name, lobe in self.lobes.items()
        }
