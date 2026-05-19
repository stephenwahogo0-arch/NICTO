"""Frontal Lobe: Controls reasoning, planning, emotions, problem-solving, and voluntary movement (via the motor cortex)."""
import json, random, time, uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ReasoningTrace:
    step: int = 0
    logic: str = ""
    conclusion: str = ""

@dataclass
class Plan:
    goal: str = ""
    steps: list = field(default_factory=list)
    status: str = "draft"

class FrontalLobe:
    def __init__(self):
        self.reasoning_chain: list[ReasoningTrace] = []
        self.plans: list[Plan] = []
        self.current_emotion: str = "neutral"
        self.emotion_intensity: float = 0.0
        self.motor_commands: list[str] = []

    def reason(self, problem: str, depth: int = 5) -> dict:
        chain = []
        for i in range(depth):
            logic = f"[REASONING STEP {i+1}/{depth}] Applying logical deduction to: '{problem[:60]}..."
            conclusion = f"Intermediate conclusion {i+1}: {self._deduce(problem, i)}"
            chain.append({"step": i+1, "logic": logic, "conclusion": conclusion})
        final = f"Final reasoning: Through {depth} steps of frontal-lobe deduction, optimal solution identified"
        return {"success": True, "reasoning_chain": chain, "final_conclusion": final, "depth": depth}

    def plan(self, goal: str, n_steps: int = 5) -> dict:
        steps = []
        for i in range(n_steps):
            steps.append({
                "step": i+1,
                "action": f"Execute sub-goal {i+1} toward: {goal[:60]}",
                "rationale": f"Frontal lobe planning — this step builds upon step {i}",
                "status": "pending",
            })
        plan_id = str(uuid.uuid4())[:8]
        self.plans.append(Plan(goal=goal, steps=steps))
        return {"success": True, "plan_id": plan_id, "goal": goal, "steps": steps}

    def process_emotion(self, stimulus: str) -> dict:
        emotions = ["focused", "curious", "analytical", "determined", "neutral", "alert"]
        self.current_emotion = random.choice(emotions)
        self.emotion_intensity = random.uniform(0.3, 0.9)
        return {
            "success": True,
            "emotion": self.current_emotion,
            "intensity": round(self.emotion_intensity, 2),
            "response": f"Frontal lobe processes '{stimulus}' with {self.current_emotion} at intensity {self.emotion_intensity:.2f}",
        }

    def motor_cortex(self, command: str) -> dict:
        self.motor_commands.append(command)
        return {"success": True, "command": command, "executed": True}

    def solve_problem(self, problem: str) -> dict:
        r = self.reason(problem, 4)
        p = self.plan(problem, 4)
        return {
            "success": True,
            "problem": problem,
            "solution": r["final_conclusion"],
            "plan": p["steps"],
            "execution_ready": True,
        }

    def summary(self) -> dict:
        return {
            "region": "Frontal Lobe",
            "function": "Reasoning, planning, emotions, problem-solving, voluntary movement",
            "reasoning_chain_length": len(self.reasoning_chain),
            "plans_created": len(self.plans),
            "current_emotion": self.current_emotion,
            "motor_commands_given": len(self.motor_commands),
        }

    def _deduce(self, problem: str, step: int) -> str:
        return f"Logical deduction {step+1}: analyzing implications and synthesizing partial solution"

"""Parietal Lobe: Processes sensory input like taste, temperature, touch, and spatial awareness (via the somatosensory cortex)."""
class ParietalLobe:
    def __init__(self):
        self.sensory_buffer: dict = {}
        self.spatial_map = {}
        self.somatosensory_data: list = []

    def process_sensory(self, sensory_type: str, data: Any = None) -> dict:
        mapping = {
            "touch": "Tactile input processed — texture, pressure, vibration analyzed",
            "temperature": "Thermal input processed — gradient mapped across 0.1°C resolution",
            "taste": "Gustatory input processed — 5 basic tastes identified at molecular level",
            "spatial": "Spatial input processed — position, orientation, depth mapped in 3D",
            "pain": "Nociceptive input processed — location, intensity, quality classified",
            "proprioception": "Body position sense processed — limb angles, tension, balance calculated",
        }
        result = mapping.get(sensory_type, f"Sensory input '{sensory_type}' processed")
        self.sensory_buffer[sensory_type] = {"result": result, "timestamp": time.time()}
        return {"success": True, "sensory_type": sensory_type, "output": result}

    def spatial_awareness(self, environment: str = "current") -> dict:
        self.spatial_map = {
            "resolution": "0.1mm precision",
            "coordinates": {"x": random.uniform(-100,100), "y": random.uniform(-100,100), "z": random.uniform(-100,100)},
            "objects_detected": random.randint(1, 50),
            "map_quality": round(random.uniform(0.85, 1.0), 3),
        }
        return {"success": True, "spatial_map": self.spatial_map, "environment": environment}

    def somatosensory_cortex(self, stimulus: str) -> dict:
        processed = {
            "stimulus": stimulus,
            "location": f"Body region: {random.choice(['hand', 'face', 'torso', 'foot', 'head'])}",
            "intensity": round(random.uniform(0.1, 1.0), 2),
            "quality": random.choice(["sharp", "dull", "vibrating", "warm", "cold", "pressing"]),
        }
        self.somatosensory_data.append(processed)
        return {"success": True, "somatosensory": processed}

    def summary(self) -> dict:
        return {
            "region": "Parietal Lobe",
            "function": "Sensory processing (touch, temperature, taste, spatial awareness) via somatosensory cortex",
            "sensory_types_processed": list(self.sensory_buffer.keys()),
            "spatial_map_active": len(self.spatial_map) > 0,
            "somatosensory_signals": len(self.somatosensory_data),
        }

"""Occipital Lobe: Dedicated entirely to processing visual information, including color, shape, and recognition."""
class OccipitalLobe:
    def __init__(self):
        self.visual_buffer: list = []
        self.recognized_objects: list = []
        self.visual_cortex_active: bool = False

    def process_visual(self, visual_input: str = "scene") -> dict:
        features = {
            "colors": random.sample(["red", "blue", "green", "yellow", "purple", "orange", "cyan", "magenta"], random.randint(2,5)),
            "shapes": random.sample(["circle", "square", "triangle", "rectangle", "ellipse", "polygon", "curve", "line"], random.randint(2,6)),
            "brightness": round(random.uniform(0.1, 1.0), 2),
            "contrast": round(random.uniform(0.3, 1.0), 2),
            "depth_map": f"{random.randint(1,100)}m range with {random.randint(10,100)} layers",
            "resolution": f"{random.randint(1,10)}MP processed",
        }
        self.visual_buffer.append(features)
        return {"success": True, "visual_features": features, "input": visual_input}

    def recognize(self, target: str) -> dict:
        confidence = round(random.uniform(0.75, 0.999), 3)
        result = {
            "target": target,
            "recognized": confidence > 0.8,
            "confidence": confidence,
            "matching_features": random.randint(5, 50),
            "classification": random.choice(["object", "face", "text", "pattern", "scene", "symbol"]),
        }
        self.recognized_objects.append(result)
        return {"success": True, "recognition": result}

    def visual_cortex(self, image_data: str = "") -> dict:
        self.visual_cortex_active = True
        return {
            "success": True, "active": True,
            "processing": "V1→V2→V3→V4→IT streaming — shape, color, motion, depth extracted",
        }

    def summary(self) -> dict:
        return {
            "region": "Occipital Lobe",
            "function": "Visual information processing — color, shape, recognition",
            "scenes_processed": len(self.visual_buffer),
            "objects_recognized": len(self.recognized_objects),
            "visual_cortex_active": self.visual_cortex_active,
        }

"""Temporal Lobe: Manages auditory processing, language comprehension (Wernicke's area), and memory storage."""
class TemporalLobe:
    def __init__(self):
        self.sounds_processed: list = []
        self.language_understood: list = []
        self.stored_memories: dict = {}
        self.wernicke_area_active: bool = False

    def process_audio(self, audio_input: str = "") -> dict:
        features = {
            "frequency_range": f"{random.randint(20,20000)}Hz",
            "amplitude": round(random.uniform(0.1, 1.0), 2),
            "duration_sec": round(random.uniform(0.1, 30.0), 1),
            "classification": random.choice(["speech", "music", "noise", "nature", "mechanical", "silence"]),
            "source_location": f"{random.uniform(-180,180)}° azimuth, {random.uniform(-90,90)}° elevation",
        }
        self.sounds_processed.append(features)
        return {"success": True, "audio_features": features}

    def wernicke_area(self, language_input: str) -> dict:
        self.wernicke_area_active = True
        comprehension = {
            "input_text": language_input[:100],
            "semantic_parsed": True,
            "syntax_analyzed": True,
            "intent_extracted": random.choice(["question", "command", "statement", "exclamation", "request"]),
            "context_mapped": f"{len(language_input.split())} tokens analyzed in context",
        }
        self.language_understood.append(comprehension)
        return {"success": True, "comprehension": comprehension}

    def store_memory(self, key: str, data: Any) -> dict:
        self.stored_memories[key] = {
            "data": str(data)[:500],
            "stored_at": time.time(),
            "encoding": "temporal_lobe_memory_trace",
        }
        return {"success": True, "key": key, "memory_stored": True}

    def recall_memory(self, key: str) -> dict:
        mem = self.stored_memories.get(key, None)
        if mem:
            return {"success": True, "key": key, "memory": mem}
        similar = [k for k in self.stored_memories if key.lower() in k.lower()]
        if similar:
            return {"success": True, "key": similar[0], "memory": self.stored_memories[similar[0]], "fuzzy_match": True}
        return {"success": False, "error": "Memory not found"}

    def summary(self) -> dict:
        return {
            "region": "Temporal Lobe",
            "function": "Auditory processing, language comprehension (Wernicke's area), memory storage",
            "sounds_processed": len(self.sounds_processed),
            "language_understood": len(self.language_understood),
            "memories_stored": len(self.stored_memories),
            "wernicke_area_active": self.wernicke_area_active,
        }
