"""
Brain Region Mapping for NIKTO.

Implements a ``BrainRegionMap`` with all 28 documented regions.
Each region has: ``name``, ``region_type`` (``"core"`` / ``"advanced"``),
``function_description``, and a ``process(text, ctx)`` method.
"""

from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class BrainRegionSpec:
    """Specification for a single brain region."""

    name: str
    region_type: str  # "core" | "advanced"
    function_description: str

    def process(self, text: str, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
        """Process *text* through this region and return a result dict."""
        return {
            "region": self.name,
            "type": self.region_type,
            "input": text,
            "processed": True,
        }


# fmt: off
_CORE_REGIONS: list[tuple[str, str]] = [
    ("Frontal",          "Decision-making, planning, problem-solving, social cognition"),
    ("Parietal",         "Sensory integration, spatial awareness, numerical cognition"),
    ("Occipital",        "Visual processing, object recognition, color perception"),
    ("Temporal",         "Auditory processing, language comprehension, memory formation"),
    ("Thalamus",         "Sensory relay station, consciousness regulation, sleep-wake cycles"),
    ("Hypothalamus",     "Homeostasis, hormone regulation, autonomic control, circadian rhythms"),
    ("Amygdala",         "Emotion processing, fear response, emotional memory, threat detection"),
    ("Hippocampus",      "Long-term memory formation, spatial navigation, learning consolidation"),
    ("Basal Ganglia",    "Motor control, habit formation, reward-based learning, action selection"),
    ("Cerebellum",       "Motor coordination, balance, fine motor control, procedural learning"),
    ("Midbrain",         "Visual and auditory reflexes, alertness, motor control"),
    ("Pons",             "Bridge between cerebrum and cerebellum, sleep regulation, arousal"),
    ("Medulla",          "Autonomic functions: breathing, heart rate, blood pressure regulation"),
    ("Cerebral Cortex",  "Higher-order cognition: thought, memory, attention, perception, language"),
    ("Corpus Callosum",  "Interhemispheric communication, integration of sensory and cognitive info"),
    ("Meninges",         "Protective layers surrounding brain and spinal cord, shock absorption"),
    ("Ventricles",       "Cerebrospinal fluid production and circulation, waste removal"),
    ("Gyri_Sulci",       "Increased cortical surface area, folding pattern for neural density"),
]

_ADVANCED_REGIONS: list[tuple[str, str]] = [
    ("RAS",              "Reticular Activating System: arousal, attention gating, sleep-wake transitions"),
    ("Insula",           "Interoception, visceral awareness, social emotion, self-recognition"),
    ("Cingulate",        "Conflict monitoring, error detection, decision evaluation, pain perception"),
    ("Pineal",           "Melatonin production, circadian rhythm regulation, sleep-wake timing"),
    ("Pituitary",        "Master hormone gland: growth, metabolism, reproduction, stress response"),
    ("Broca",            "Speech production, language articulation, syntactic processing"),
    ("Angular Gyrus",    "Cross-modal integration, metaphor comprehension, number processing"),
    ("Fusiform",         "Facial recognition, expert pattern recognition, object categorization"),
    ("Precuneus",        "Self-reflection, episodic memory retrieval, mental imagery, consciousness"),
    ("DMN",              "Default Mode Network: mind-wandering, social cognition, autobiographical memory"),
]
# fmt: on


class BrainRegionMap:
    """Maps 28 brain regions to their specs and provides lookup methods."""

    def __init__(self) -> None:
        self.regions: dict[str, BrainRegionSpec] = {}
        self._initialize()

    def _initialize(self) -> None:
        for name, desc in _CORE_REGIONS:
            self.regions[name.lower()] = BrainRegionSpec(
                name=name,
                region_type="core",
                function_description=desc,
            )
        for name, desc in _ADVANCED_REGIONS:
            self.regions[name.lower()] = BrainRegionSpec(
                name=name,
                region_type="advanced",
                function_description=desc,
            )

    def get_region(self, key: str) -> Optional[BrainRegionSpec]:
        """Look up a region by name (case-insensitive)."""
        return self.regions.get(key.lower().replace(" ", "_"))

    def get_regions_by_type(self, region_type: str) -> list[BrainRegionSpec]:
        """Return all regions matching ``region_type`` (``"core"`` / ``"advanced"``)."""
        return [r for r in self.regions.values() if r.region_type == region_type]

    def get_status(self) -> dict[str, Any]:
        """Return summary stats."""
        core = self.get_regions_by_type("core")
        adv = self.get_regions_by_type("advanced")
        return {
            "total_regions": len(self.regions),
            "core_regions": len(core),
            "advanced_regions": len(adv),
            "region_names": sorted(r.name for r in self.regions.values()),
        }
