"""
Brain Optimizer for NIKTO.

Implements Hebbian learning (strengthen frequently-used regions),
synaptic pruning (remove weak connections), and neuroplasticity
reporting.
"""

import time
from typing import Any, Optional


class BrainOptimizer:
    """Optimise brain connections through Hebbian learning and pruning."""

    def __init__(self) -> None:
        self.region_usage: dict[str, float] = {}  # region_name → cumulative activation
        self.region_strength: dict[str, float] = {}  # region_name → weight
        self._pruning_events: int = 0
        self._hebbian_updates: int = 0

    def hebbian_learning(self, region_name: str, activation_strength: float = 1.0) -> dict[str, Any]:
        """Strengthen *region_name* by *activation_strength*.

        Neurons that fire together wire together: frequently used regions
        get their activation threshold lowered (i.e., they become easier
        to activate in the future).
        """
        region_name = region_name.lower()
        current = self.region_strength.get(region_name, 0.5)
        increment = 0.05 * activation_strength
        self.region_strength[region_name] = min(1.0, current + increment)
        self.region_usage[region_name] = self.region_usage.get(region_name, 0.0) + activation_strength
        self._hebbian_updates += 1
        return {
            "region": region_name,
            "new_strength": self.region_strength[region_name],
            "total_usage": self.region_usage[region_name],
        }

    def synaptic_pruning(self, threshold: float = 0.1) -> dict[str, Any]:
        """Prune regions whose strength has fallen below *threshold*.

        Returns a dict with the number of pruned entries.
        """
        pruned: list[str] = []
        for name, strength in list(self.region_strength.items()):
            if strength < threshold:
                pruned.append(name)
                del self.region_strength[name]
                self.region_usage.pop(name, None)
        if pruned:
            self._pruning_events += len(pruned)
        return {"pruned_count": len(pruned), "pruned_regions": pruned}

    def neuroplasticity_report(self) -> dict[str, Any]:
        """Return usage statistics per region."""
        report: dict[str, Any] = {
            "total_regions_tracked": len(self.region_strength),
            "total_hebbian_updates": self._hebbian_updates,
            "total_pruning_events": self._pruning_events,
            "regions": {},
        }
        for name in sorted(self.region_strength):
            report["regions"][name] = {
                "strength": round(self.region_strength.get(name, 0.0), 4),
                "usage": round(self.region_usage.get(name, 0.0), 4),
            }
        return report

    def get_efficiency(self) -> float:
        """Return an overall efficiency score (0..1)."""
        if not self.region_strength:
            return 1.0
        avg = sum(self.region_strength.values()) / len(self.region_strength)
        return min(1.0, avg)

    def summary(self) -> dict[str, Any]:
        """Return a human-readable summary."""
        return {
            "hebbian_updates": self._hebbian_updates,
            "pruning_events": self._pruning_events,
            "efficiency": self.get_efficiency(),
            "regions_tracked": len(self.region_strength),
        }

    def get_status(self) -> dict[str, Any]:
        """Alias for summary."""
        return self.summary()
