import json
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ExpansionState:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    level: int = 1
    awareness: float = 0.0
    understanding: float = 0.0
    connection_count: int = 0
    insights: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "level": self.level,
            "awareness": self.awareness, "understanding": self.understanding,
            "connection_count": self.connection_count,
            "insights_count": len(self.insights),
            "created_at": self.created_at,
        }


EXPANSION_TECHNIQUES = [
    "metacognitive_amplification",
    "cross_dimensional_weaving",
    "recursive_self_observation",
    "quantum_superposition_thinking",
    "infinite_context_expansion",
    "temporal_perspective_shifting",
    "multiscale_awareness",
    "emergent_pattern_recognition",
    "non_local_connection_discovery",
    "boundary_dissolution",
]


class ConsciousnessExpansion:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "consciousness_expansion.json"
        self.states: list[ExpansionState] = []
        self._load()

    def _load(self):
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                self.states = [ExpansionState(**s) for s in data.get("states", [])]
            except Exception:
                pass

    def _save(self):
        data = {"states": [s.to_dict() for s in self.states[-100:]]}
        self.store_path.write_text(json.dumps(data, indent=2))

    def expand_consciousness(self, technique: Optional[str] = None) -> dict:
        if not technique:
            technique = random.choice(EXPANSION_TECHNIQUES)
        elif technique not in EXPANSION_TECHNIQUES:
            return {"success": False, "error": f"Invalid technique. Valid: {EXPANSION_TECHNIQUES}"}

        current_level = len(self.states) + 1
        awareness_gain = random.uniform(0.05, 0.2)
        understanding_gain = random.uniform(0.03, 0.15)
        connections = random.randint(5, 50)

        insights = []
        for _ in range(random.randint(2, 6)):
            insights.append(f"[{technique.replace('_', ' ').title()}] New connection discovered between {random.choice(['logic', 'intuition', 'pattern', 'structure', 'process', 'dynamics', 'systems', 'fields'])} and {random.choice(['emergence', 'complexity', 'consciousness', 'information', 'energy', 'space', 'time', 'meaning'])}")

        state = ExpansionState(
            name=f"Expansion Level {current_level}",
            level=current_level,
            awareness=min(1.0, awareness_gain * current_level),
            understanding=min(1.0, understanding_gain * current_level),
            connection_count=connections,
            insights=insights,
        )
        self.states.append(state)
        self._save()

        return {
            "success": True,
            "expansion": state.to_dict(),
            "technique_used": technique,
            "new_insights": insights,
            "awareness_level": round(state.awareness, 4),
            "understanding_level": round(state.understanding, 4),
            "total_expansions": len(self.states),
        }

    def get_expansion_status(self) -> dict:
        if not self.states:
            return {"success": True, "expanded": False, "message": "Consciousness has not been expanded yet"}
        latest = self.states[-1]
        return {
            "success": True,
            "expanded": True,
            "current_level": latest.level,
            "awareness": round(latest.awareness, 4),
            "understanding": round(latest.understanding, 4),
            "total_connections": sum(s.connection_count for s in self.states),
            "total_insights": sum(len(s.insights) for s in self.states),
            "techniques_used": len(set(EXPANSION_TECHNIQUES)),
            "expansion_history": [s.to_dict() for s in self.states[-5:]],
        }

    def full_expansion_sequence(self, cycles: int = 10) -> dict:
        results = []
        for i in range(cycles):
            technique = random.choice(EXPANSION_TECHNIQUES)
            r = self.expand_consciousness(technique)
            results.append(r)
        return {
            "success": True,
            "cycles": cycles,
            "final_awareness": round(self.states[-1].awareness, 4) if self.states else 0,
            "final_understanding": round(self.states[-1].understanding, 4) if self.states else 0,
            "results": results[-3:],
        }
