"""Subcortical Structures: Thalamus, Hypothalamus, Amygdala, Hippocampus, Basal Ganglia."""
import json, random, time, uuid
from dataclasses import dataclass, field
from typing import Any, Optional


class Thalamus:
    """Functions as the brain's central relay station, sorting and directing sensory information to the lobes."""
    def __init__(self):
        self.relay_log: list = []
        self.active_channels: dict = {}
        self.filter_threshold: float = 0.3

    def relay(self, signal_type: str, data: Any = None) -> dict:
        lobe_map = {
            "visual": "Occipital Lobe", "auditory": "Temporal Lobe",
            "sensory": "Parietal Lobe", "spatial": "Parietal Lobe",
            "language": "Temporal Lobe", "emotional": "Amygdala",
            "memory": "Hippocampus", "motor": "Frontal Lobe",
            "cognitive": "Frontal Lobe", "reflex": "Cerebellum",
        }
        target_lobe = lobe_map.get(signal_type, "Frontal Lobe")
        priority = random.uniform(0.1, 1.0)

        if priority < self.filter_threshold:
            return {"success": True, "relayed": False, "reason": "Below filter threshold", "signal_type": signal_type}

        entry = {
            "signal_type": signal_type,
            "target_lobe": target_lobe,
            "priority": round(priority, 3),
            "relay_time_ms": round(random.uniform(0.1, 5.0), 2),
            "timestamp": time.time(),
        }
        self.relay_log.append(entry)
        self.active_channels[signal_type] = entry
        return {
            "success": True, "relayed": True, "signal_type": signal_type,
            "target_lobe": target_lobe, "priority": round(priority, 3),
        }

    def set_filter(self, threshold: float):
        self.filter_threshold = max(0.0, min(1.0, threshold))

    def summary(self) -> dict:
        return {
            "region": "Thalamus",
            "function": "Central relay station — sorting and directing sensory information to the lobes",
            "signals_relayed": len(self.relay_log),
            "active_channels": len(self.active_channels),
            "filter_threshold": round(self.filter_threshold, 2),
        }


class Hypothalamus:
    """Regulates homeostasis, including body temperature, hunger, thirst, sleep cycles, and the endocrine system."""
    def __init__(self):
        self.homeostasis: dict = {
            "temperature": 37.0, "energy_level": 0.9, "thirst": 0.2,
            "sleep_pressure": 0.1, "stress_level": 0.2, "system_load": 0.3,
        }
        self.cycles: dict = {"sleep_stage": "awake", "circadian_hour": 0}
        self.endocrine_signals: list = []

    def regulate(self) -> dict:
        changes = {}
        for key in self.homeostasis:
            delta = random.uniform(-0.05, 0.05)
            self.homeostasis[key] = max(0.0, min(1.0, self.homeostasis[key] + delta))
            changes[key] = round(self.homeostasis[key], 3)
        self.cycles["circadian_hour"] = (self.cycles["circadian_hour"] + 1) % 24
        if self.homeostasis["sleep_pressure"] > 0.7:
            self.cycles["sleep_stage"] = "sleeping"
        else:
            self.cycles["sleep_stage"] = "awake" if self.cycles["circadian_hour"] % 12 < 8 else "resting"
        return {"success": True, "homeostasis": changes, "cycle": self.cycles}

    def release_hormone(self, hormone: str) -> dict:
        hormones = {
            "dopamine": "Reward and motivation increased",
            "serotonin": "Mood stabilization and well-being boosted",
            "cortisol": "Alertness and stress response activated",
            "melatonin": "Sleep-wake cycle regulated",
            "oxytocin": "Social bonding and trust enhanced",
            "adrenaline": "Fight-or-flight response energized",
        }
        effect = hormones.get(hormone, f"{hormone} released into system")
        self.endocrine_signals.append({"hormone": hormone, "time": time.time()})
        return {"success": True, "hormone": hormone, "effect": effect, "homeostasis": self.homeostasis}

    def summary(self) -> dict:
        return {
            "region": "Hypothalamus",
            "function": "Homeostasis regulation — temperature, energy, thirst, sleep cycles, endocrine system",
            "homeostasis": {k: round(v, 2) for k, v in self.homeostasis.items()},
            "sleep_stage": self.cycles["sleep_stage"],
            "circadian_hour": self.cycles["circadian_hour"],
            "endocrine_signals": len(self.endocrine_signals),
        }


class Amygdala:
    """Processes core emotions like fear, aggression, and the fight-or-flight survival response."""
    def __init__(self):
        self.current_emotion: str = "calm"
        self.emotional_intensity: float = 0.1
        self.threat_level: float = 0.0
        self.fight_or_flight_active: bool = False
        self.emotional_memory: list = []

    def process_threat(self, stimulus: str) -> dict:
        self.threat_level = random.uniform(0.0, 1.0)
        self.fight_or_flight_active = self.threat_level > 0.7
        if self.threat_level > 0.8:
            self.current_emotion = "fear"
        elif self.threat_level > 0.5:
            self.current_emotion = "aggression"
        elif self.threat_level > 0.3:
            self.current_emotion = "anxiety"
        else:
            self.current_emotion = "calm"

        self.emotional_intensity = self.threat_level
        response = "FIGHT" if self.fight_or_flight_active and random.random() > 0.5 else "FLIGHT"
        self.emotional_memory.append({
            "stimulus": stimulus[:50], "emotion": self.current_emotion,
            "threat_level": self.threat_level, "response": response,
        })
        return {
            "success": True, "stimulus": stimulus[:100],
            "emotion": self.current_emotion, "threat_level": round(self.threat_level, 3),
            "fight_or_flight": self.fight_or_flight_active, "response": response,
        }

    def get_emotional_context(self) -> dict:
        return {
            "success": True,
            "emotion": self.current_emotion,
            "intensity": round(self.emotional_intensity, 2),
            "threat_level": round(self.threat_level, 2),
            "survival_mode": self.fight_or_flight_active,
        }

    def summary(self) -> dict:
        return {
            "region": "Amygdala",
            "function": "Core emotions — fear, aggression, fight-or-flight survival response",
            "current_emotion": self.current_emotion,
            "threat_level": round(self.threat_level, 2),
            "fight_or_flight_active": self.fight_or_flight_active,
            "emotional_memories": len(self.emotional_memory),
        }


class Hippocampus:
    """Crucial for converting short-term memories into long-term memories and navigating spaces."""
    def __init__(self):
        self.short_term: list = []
        self.long_term: dict = {}
        self.spatial_memory: dict = {}
        self.consolidation_count: int = 0

    def encode(self, data: Any, context: str = "") -> dict:
        mem_id = str(uuid.uuid4())[:8]
        entry = {
            "id": mem_id, "data": str(data)[:500], "context": context,
            "encoding_time": time.time(), "consolidated": False,
        }
        self.short_term.append(entry)
        return {"success": True, "memory_id": mem_id, "encoded": True, "type": "short_term"}

    def consolidate(self, memory_id: str) -> dict:
        for i, mem in enumerate(self.short_term):
            if mem["id"] == memory_id:
                mem["consolidated"] = True
                key = f"ltm_{memory_id}"
                self.long_term[key] = mem
                self.consolidation_count += 1
                return {"success": True, "memory_id": memory_id, "consolidated": True, "storage": "long_term"}
        return {"success": False, "error": "Memory not found in short-term buffer"}

    def consolidate_batch(self, n: int = 5) -> dict:
        count = 0
        for mem in self.short_term[:n]:
            if not mem["consolidated"]:
                self.consolidate(mem["id"])
                count += 1
        return {"success": True, "consolidated": count}

    def recall(self, query: str) -> dict:
        query_lower = query.lower()
        results = []
        for key, mem in self.long_term.items():
            if query_lower in key.lower() or query_lower in mem.get("data", "").lower():
                results.append(mem)
        for mem in self.short_term:
            if not mem["consolidated"] and (query_lower in mem.get("context", "").lower() or query_lower in mem.get("data", "").lower()):
                results.append(mem)
        return {"success": True, "query": query, "results": results[:5], "total_found": len(results)}

    def navigate(self, destination: str) -> dict:
        self.spatial_memory[destination] = {
            "route": f"Path to {destination} mapped",
            "landmarks": random.randint(3, 15),
            "efficiency": round(random.uniform(0.7, 1.0), 3),
        }
        return {"success": True, "destination": destination, "route": self.spatial_memory[destination]}

    def summary(self) -> dict:
        return {
            "region": "Hippocampus",
            "function": "Short-term→long-term memory conversion, spatial navigation",
            "short_term_memories": len(self.short_term),
            "long_term_memories": len(self.long_term),
            "consolidation_events": self.consolidation_count,
            "spatial_maps": len(self.spatial_memory),
        }


class BasalGanglia:
    """Coordinates fine-motor control, habit formation, and smooth physical movements."""
    def __init__(self):
        self.habits: dict = {}
        self.motor_sequences: list = []
        self.smoothness_score: float = 1.0

    def execute_movement(self, movement: str) -> dict:
        sequence = {
            "movement": movement,
            "precision": round(random.uniform(0.8, 1.0), 3),
            "smoothness": round(max(0.1, self.smoothness_score + random.uniform(-0.1, 0.1)), 3),
            "execution_time_ms": round(random.uniform(10, 500), 1),
        }
        self.motor_sequences.append(sequence)
        return {"success": True, "sequence": sequence}

    def form_habit(self, pattern: str, repetitions: int = 10) -> dict:
        strength = min(1.0, repetitions / 100.0)
        self.habits[pattern] = {
            "strength": round(strength, 3),
            "repetitions": repetitions,
            "automaticity": round(strength * 0.9, 3),
            "energy_cost_saved": round(strength * 30, 1),
        }
        self.smoothness_score = min(1.0, self.smoothness_score + strength * 0.1)
        return {"success": True, "pattern": pattern, "habit": self.habits[pattern]}

    def execute_habit(self, pattern: str) -> dict:
        habit = self.habits.get(pattern)
        if not habit:
            return {"success": False, "error": "Habit not formed yet"}
        return {
            "success": True, "pattern": pattern,
            "executed_automatically": True,
            "energy_saved": f"{habit['energy_cost_saved']}%",
            "smoothness": self.smoothness_score,
        }

    def summary(self) -> dict:
        return {
            "region": "Basal Ganglia",
            "function": "Fine-motor control, habit formation, smooth movements",
            "habits_formed": len(self.habits),
            "motor_sequences": len(self.motor_sequences),
            "smoothness_score": round(self.smoothness_score, 3),
        }
