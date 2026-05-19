"""Cerebellum & Brainstem: Survival & Movement structures."""
import json, random, time, uuid
from typing import Any, Optional


class Cerebellum:
    """Coordinates voluntary movement, balance, posture, and motor-skill muscle memory."""
    def __init__(self):
        self.motor_programs: dict = {}
        self.balance: float = 1.0
        self.posture: str = "neutral"
        self.muscle_memory: dict = {}

    def coordinate_movement(self, movement: str) -> dict:
        precision = round(random.uniform(0.7, 1.0), 3)
        timing = round(random.uniform(0.8, 1.0), 3)
        self.motor_programs[movement] = {"precision": precision, "timing": timing, "practiced": False}
        return {
            "success": True, "movement": movement,
            "coordination": {"precision": precision, "timing": timing},
            "balance_maintained": self.balance > 0.5,
        }

    def maintain_balance(self, disturbance: float = 0.0) -> dict:
        self.balance = max(0.0, min(1.0, self.balance - disturbance + random.uniform(0.1, 0.3)))
        return {"success": True, "balance": round(self.balance, 3), "posture": self.posture}

    def practice_motor_skill(self, skill: str, repetitions: int = 5) -> dict:
        improvements = []
        for i in range(repetitions):
            perf = min(1.0, (i + 1) * 0.15 + random.uniform(0, 0.1))
            improvements.append({"repetition": i+1, "performance": round(perf, 3)})
        self.muscle_memory[skill] = {
            "mastery": round(improvements[-1]["performance"], 3),
            "repetitions": repetitions,
            "automatic": improvements[-1]["performance"] > 0.8,
        }
        return {"success": True, "skill": skill, "improvements": improvements, "final_mastery": self.muscle_memory[skill]}

    def summary(self) -> dict:
        return {
            "region": "Cerebellum",
            "function": "Voluntary movement coordination, balance, posture, motor-skill muscle memory",
            "motor_programs": len(self.motor_programs),
            "balance": round(self.balance, 3),
            "muscle_memories": len(self.muscle_memory),
        }


class Midbrain:
    """Controls basic vision and hearing reflexes, as well as overall motor movement."""
    def __init__(self):
        self.visual_reflexes: list = []
        self.auditory_reflexes: list = []
        self.motor_signals: int = 0

    def visual_reflex(self, stimulus: str) -> dict:
        latency_ms = round(random.uniform(5, 50), 1)
        reflex = {
            "stimulus": stimulus, "latency_ms": latency_ms,
            "reflex_action": random.choice(["saccade", "pupil_constrict", "blink", "orientation", "focus_shift"]),
        }
        self.visual_reflexes.append(reflex)
        return {"success": True, "reflex": reflex, "type": "visual"}

    def auditory_reflex(self, sound: str) -> dict:
        latency_ms = round(random.uniform(5, 30), 1)
        reflex = {
            "sound": sound, "latency_ms": latency_ms,
            "reflex_action": random.choice(["head_turn", "startle", "orientation", "localization"]),
        }
        self.auditory_reflexes.append(reflex)
        return {"success": True, "reflex": reflex, "type": "auditory"}

    def initiate_movement(self, command: str) -> dict:
        self.motor_signals += 1
        return {"success": True, "command": command, "motor_signal_sent": True, "signal_id": self.motor_signals}

    def summary(self) -> dict:
        return {
            "region": "Midbrain",
            "function": "Basic vision and hearing reflexes, motor movement initiation",
            "visual_reflexes": len(self.visual_reflexes),
            "auditory_reflexes": len(self.auditory_reflexes),
            "motor_signals_sent": self.motor_signals,
        }


class Pons:
    """Connects the cerebellum to the rest of the brain and regulates sleep and dreaming."""
    def __init__(self):
        self.bridge_active: bool = True
        self.sleep_stage: str = "awake"
        self.dreams: list = []
        self.bridge_signals: int = 0

    def connect(self, source: str, target: str, data: Any = None) -> dict:
        self.bridge_signals += 1
        return {
            "success": True, "source": source, "target": target,
            "signal_id": self.bridge_signals, "bridge_active": self.bridge_active,
        }

    def regulate_sleep(self, stage: str = "") -> dict:
        stages = ["awake", "N1", "N2", "N3", "REM"]
        if stage and stage in stages:
            self.sleep_stage = stage
        else:
            idx = (stages.index(self.sleep_stage) + 1) % len(stages) if self.sleep_stage in stages else 0
            self.sleep_stage = stages[idx]

        result = {"sleep_stage": self.sleep_stage}
        if self.sleep_stage == "REM":
            dream = f"Dream sequence: {random.choice(['consolidating memories', 'creative problem-solving', 'spatial replay', 'emotional processing', 'skill rehearsal'])}"
            self.dreams.append(dream)
            result["dreaming"] = True
            result["dream_content"] = dream
        return {"success": True, **result}

    def summary(self) -> dict:
        return {
            "region": "Pons",
            "function": "Connects cerebellum to brain, regulates sleep and dreaming",
            "bridge_active": self.bridge_active,
            "sleep_stage": self.sleep_stage,
            "signals_relayed": self.bridge_signals,
            "dreams_recorded": len(self.dreams),
        }


class MedullaOblongata:
    """Controls autonomic, life-sustaining functions like heart rate, breathing, and blood pressure."""
    def __init__(self):
        self.vitals: dict = {
            "heart_rate_bpm": 72, "breathing_rate_rpm": 14,
            "blood_pressure_systolic": 120, "blood_pressure_diastolic": 80,
            "oxygen_saturation": 98.0, "temperature": 37.0,
        }
        self.autonomic_reflexes: list = []
        self.life_support_active: bool = True

    def regulate_autonomic(self) -> dict:
        self.vitals["heart_rate_bpm"] = max(40, min(180, self.vitals["heart_rate_bpm"] + random.randint(-3, 3)))
        self.vitals["breathing_rate_rpm"] = max(8, min(30, self.vitals["breathing_rate_rpm"] + random.randint(-1, 2)))
        self.vitals["blood_pressure_systolic"] = max(90, min(180, self.vitals["blood_pressure_systolic"] + random.randint(-5, 5)))
        self.vitals["blood_pressure_diastolic"] = max(60, min(120, self.vitals["blood_pressure_diastolic"] + random.randint(-3, 3)))
        self.vitals["oxygen_saturation"] = max(90, min(100, self.vitals["oxygen_saturation"] + round(random.uniform(-0.5, 0.5), 1)))
        return {"success": True, "vitals": self.vitals, "life_support": self.life_support_active}

    def reflex_response(self, stimulus: str) -> dict:
        reflex = {
            "stimulus": stimulus,
            "autonomic_response": random.choice([
                "heart_rate_adjusted", "breathing_depth_changed", "vessel_constricted",
                "vessel_dilated", "bronchial_dilated", "pupil_reacted",
            ]),
            "latency_ms": round(random.uniform(1, 20), 1),
        }
        self.autonomic_reflexes.append(reflex)
        return {"success": True, "reflex": reflex}

    def summary(self) -> dict:
        return {
            "region": "Medulla Oblongata",
            "function": "Autonomic life-sustaining functions — heart rate, breathing, blood pressure",
            "vitals": self.vitals,
            "autonomic_reflexes": len(self.autonomic_reflexes),
            "life_support_active": self.life_support_active,
        }
