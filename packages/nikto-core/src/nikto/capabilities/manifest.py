from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FeatureCapability:
    name: str
    module: str
    doc: str = ""
    methods: list[str] = field(default_factory=list)
    source_preview: str = ""
    summary: Optional[str] = None
    category: str = ""

    def __post_init__(self):
        if not self.category:
            if "bio_medical" in self.module:
                self.category = "Bio-Medical"
            elif "consciousness" in self.module:
                self.category = "Consciousness"
            elif "physics" in self.module:
                self.category = "Physics & Reality"
            elif "communication" in self.module:
                self.category = "Communication"
            elif "global_cosmic" in self.module:
                self.category = "Global & Cosmic"
            elif "breakthrough" in self.module:
                self.category = "Breakthrough"
            elif "security" in self.module:
                self.category = "Security"
            elif "autopilot" in self.module:
                self.category = "Autopilot"
            elif "game" in self.module:
                self.category = "Game Engine"
            elif "evolution" in self.module:
                self.category = "Evolution"
            elif "dream" in self.module:
                self.category = "Dream State"
            elif "mesh" in self.module:
                self.category = "Mesh Network"
            elif "device" in self.module:
                self.category = "Device Control"
            elif "earn" in self.module:
                self.category = "Crypto Earning"
            elif "memory" in self.module:
                self.category = "Memory"
            elif "tools" in self.module:
                self.category = "Tools"
            elif "skills" in self.module:
                self.category = "Skills"
            elif "mcp" in self.module:
                self.category = "MCP"
            elif "cua" in self.module:
                self.category = "Computer Use"
            else:
                self.category = "Core"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "module": self.module,
            "doc": self.doc,
            "methods": self.methods,
            "source_preview": self.source_preview[:200],
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict) -> FeatureCapability:
        return cls(**data)


@dataclass
class CapabilityManifest:
    features: list[FeatureCapability] = field(default_factory=list)
    scanned_at: float = field(default_factory=time.time)
    total_features: int = 0

    def __post_init__(self):
        self.total_features = len(self.features)

    def get_by_category(self, category: str) -> list[FeatureCapability]:
        return [f for f in self.features if f.category == category]

    def get_by_module(self, module: str) -> list[FeatureCapability]:
        return [f for f in self.features if f.module == module]

    def categories(self) -> dict[str, int]:
        counts = {}
        for f in self.features:
            counts[f.category] = counts.get(f.category, 0) + 1
        return counts

    def to_dict(self) -> dict:
        return {
            "scanned_at": self.scanned_at,
            "total_features": self.total_features,
            "features": [f.to_dict() for f in self.features],
        }

    @classmethod
    def from_dict(cls, data: dict) -> CapabilityManifest:
        features = [FeatureCapability.from_dict(f) for f in data.get("features", [])]
        return cls(features=features, scanned_at=data.get("scanned_at", time.time()))
