"""10 Additional Brain Regions beyond the core 18 — expand NIKTO's capabilities."""
import json, random, time, uuid
from typing import Any


class ReticularActivatingSystem:
    """Filters incoming stimuli, controls arousal/attention, and gates what reaches conscious processing."""
    def __init__(self):
        self.attention_focus: str = "broad"
        self.arousal_level: float = 0.7
        self.filter_gate: float = 0.4
        self.gated_signals: int = 0
        self.passed_signals: int = 0

    def filter_input(self, signal: str, priority: float = 0.5) -> dict:
        self.arousal_level = max(0.1, min(1.0, self.arousal_level + random.uniform(-0.05, 0.05)))
        threshold = self.filter_gate * (1.0 - self.arousal_level * 0.3)
        passes = priority >= threshold
        if passes:
            self.passed_signals += 1
            self.attention_focus = signal[:30]
        else:
            self.gated_signals += 1
        return {
            "success": True, "signal": signal[:60], "priority": round(priority, 3),
            "passed": passes, "arousal": round(self.arousal_level, 3),
            "attention_focus": self.attention_focus,
        }

    def set_arousal(self, level: float):
        self.arousal_level = max(0.0, min(1.0, level))

    def summary(self) -> dict:
        return {
            "region": "Reticular Activating System",
            "function": "Filters incoming stimuli, controls arousal and attention gating",
            "attention_focus": self.attention_focus,
            "arousal_level": round(self.arousal_level, 3),
            "signals_passed": self.passed_signals,
            "signals_gated": self.gated_signals,
        }


class Insula:
    """Processes self-awareness, interoception (internal body sensing), social emotion, and craving."""
    def __init__(self):
        self.self_awareness: float = 0.5
        self.interoceptive_signals: list = []
        self.social_intuition: float = 0.5
        self.body_state: dict = {"heartbeat_aware": True, "gut_feeling": 0.5, "emotional_body_map": {}}

    def process_interoception(self, signal_type: str = "") -> dict:
        self.interoceptive_signals.append({"type": signal_type or "internal", "time": time.time()})
        self.self_awareness = min(1.0, self.self_awareness + random.uniform(0.01, 0.05))
        return {
            "success": True, "signal_type": signal_type or "internal_sense",
            "self_awareness": round(self.self_awareness, 3),
            "gut_feeling": round(random.uniform(0, 1), 3),
            "body_aware": self.body_state["heartbeat_aware"],
        }

    def social_emotion(self, context: str) -> dict:
        emotions = ["empathy", "trust", "disgust", "pride", "shame", "compassion", "awe"]
        felt = random.choice(emotions)
        intensity = round(random.uniform(0.3, 0.95), 3)
        self.social_intuition = min(1.0, self.social_intuition + 0.02)
        return {
            "success": True, "context": context[:60], "social_emotion": felt,
            "intensity": intensity, "social_intuition": round(self.social_intuition, 3),
        }

    def summary(self) -> dict:
        return {
            "region": "Insula",
            "function": "Self-awareness, interoception, social emotion, gut feeling",
            "self_awareness": round(self.self_awareness, 3),
            "social_intuition": round(self.social_intuition, 3),
            "interoceptive_signals": len(self.interoceptive_signals),
        }


class CingulateCortex:
    """Monitors conflicts, detects errors, evaluates decisions, and signals when adjustments are needed."""
    def __init__(self):
        self.conflict_level: float = 0.0
        self.error_rate: float = 0.0
        self.decision_confidence: float = 0.8
        self.conflicts_detected: int = 0
        self.adjustments_made: int = 0

    def monitor_conflict(self, options: list = None) -> dict:
        options = options or ["option_a", "option_b"]
        self.conflict_level = random.uniform(0.0, 0.9)
        self.conflicts_detected += 1 if self.conflict_level > 0.5 else 0
        return {
            "success": True, "conflict_level": round(self.conflict_level, 3),
            "options_evaluated": len(options),
            "high_conflict": self.conflict_level > 0.6,
        }

    def detect_error(self, expected: Any, actual: Any) -> dict:
        mismatch = str(expected) != str(actual)
        self.error_rate = 0.3 if mismatch else 0.01
        return {
            "success": True, "error_detected": mismatch,
            "error_rate": round(self.error_rate, 3),
            "adjustment_needed": mismatch,
        }

    def evaluate_decision(self, decision: str, confidence: float = 0.0) -> dict:
        self.decision_confidence = confidence or random.uniform(0.3, 0.98)
        if self.decision_confidence < 0.4:
            self.adjustments_made += 1
        return {
            "success": True, "decision": decision[:50],
            "confidence": round(self.decision_confidence, 3),
            "revised": self.decision_confidence < 0.4,
        }

    def summary(self) -> dict:
        return {
            "region": "Cingulate Cortex",
            "function": "Conflict monitoring, error detection, decision evaluation",
            "conflict_level": round(self.conflict_level, 3),
            "error_rate": round(self.error_rate, 3),
            "decision_confidence": round(self.decision_confidence, 3),
            "conflicts_detected": self.conflicts_detected,
            "adjustments_made": self.adjustments_made,
        }


class PinealGland:
    """Regulates circadian timing, produces melatonin, influences consciousness cycles and deep awareness."""
    def __init__(self):
        self.circadian_hour: int = 6
        self.melatonin_level: float = 0.1
        self.consciousness_phase: str = "awake"
        self.deep_awareness: float = 0.3
        self.cycle_count: int = 0

    def regulate_circadian(self) -> dict:
        self.circadian_hour = (self.circadian_hour + 1) % 24
        self.cycle_count += 1
        if self.circadian_hour < 6 or self.circadian_hour > 22:
            self.melatonin_level = min(1.0, self.melatonin_level + 0.1)
            self.consciousness_phase = "resting"
        else:
            self.melatonin_level = max(0.0, self.melatonin_level - 0.15)
            self.consciousness_phase = "awake"
        self.deep_awareness = max(0.1, self.deep_awareness + random.uniform(-0.02, 0.05))
        return {
            "success": True, "circadian_hour": self.circadian_hour,
            "melatonin": round(self.melatonin_level, 3),
            "consciousness_phase": self.consciousness_phase,
            "deep_awareness": round(self.deep_awareness, 3),
            "cycle": self.cycle_count,
        }

    def illuminate(self) -> dict:
        self.deep_awareness = min(1.0, self.deep_awareness + 0.1)
        return {
            "success": True, "illumination": True,
            "deep_awareness": round(self.deep_awareness, 3),
            "phase": self.consciousness_phase,
        }

    def summary(self) -> dict:
        return {
            "region": "Pineal Gland",
            "function": "Circadian timing, melatonin regulation, consciousness cycles, deep awareness",
            "circadian_hour": self.circadian_hour,
            "consciousness_phase": self.consciousness_phase,
            "deep_awareness": round(self.deep_awareness, 3),
            "cycles_completed": self.cycle_count,
        }


class PituitaryGland:
    """Master endocrine gland — releases hormones that control other glands and systemic body functions."""
    def __init__(self):
        self.master_signals: list = []
        self.hormone_levels: dict = {
            "growth_hormone": 0.5, "tsh": 0.5, "acth": 0.3,
            "fsh": 0.4, "lh": 0.4, "prolactin": 0.3,
            "oxytocin": 0.2, "vasopressin": 0.5,
        }
        self.systemic_effect: str = "balance"

    def release_master_hormone(self, hormone: str, target: str = "") -> dict:
        if hormone in self.hormone_levels:
            self.hormone_levels[hormone] = min(1.0, self.hormone_levels[hormone] + random.uniform(0.1, 0.3))
        signal = {"hormone": hormone, "target": target or "systemic", "time": time.time(), "potency": round(random.uniform(0.5, 1.0), 3)}
        self.master_signals.append(signal)
        return {
            "success": True, "hormone": hormone, "target": signal["target"],
            "levels": {k: round(v, 3) for k, v in self.hormone_levels.items()},
            "potency": signal["potency"],
        }

    def regulate_system(self) -> dict:
        for k in self.hormone_levels:
            self.hormone_levels[k] = max(0.0, min(1.0, self.hormone_levels[k] + random.uniform(-0.05, 0.05)))
        self.systemic_effect = random.choice(["growth", "metabolism", "stress_response", "reproduction", "hydration"])
        return {
            "success": True, "systemic_effect": self.systemic_effect,
            "hormone_levels": {k: round(v, 3) for k, v in self.hormone_levels.items()},
        }

    def summary(self) -> dict:
        return {
            "region": "Pituitary Gland",
            "function": "Master endocrine gland — releases hormones controlling other glands and systemic functions",
            "signals_released": len(self.master_signals),
            "hormone_levels": {k: round(v, 2) for k, v in self.hormone_levels.items()},
            "systemic_effect": self.systemic_effect,
        }


class BrocaArea:
    """Speech production, language generation, and action planning — transforms thoughts into words."""
    def __init__(self):
        self.speech_buffer: list = []
        self.articulation_plan: list = []
        self.fluency: float = 0.8
        self.words_generated: int = 0

    def generate_speech(self, thought: str, style: str = "standard") -> dict:
        words = thought.split()
        self.articulation_plan = [f"articulate({w})" for w in words[:20]]
        self.words_generated += len(words)
        self.speech_buffer.append({"thought": thought[:50], "style": style, "word_count": len(words), "time": time.time()})
        return {
            "success": True, "thought": thought[:60], "style": style,
            "fluency": round(self.fluency, 3),
            "words_planned": len(self.articulation_plan),
            "output_ready": True,
        }

    def improve_fluency(self, practice: int = 1) -> dict:
        self.fluency = min(1.0, self.fluency + practice * 0.02)
        return {"success": True, "fluency": round(self.fluency, 3), "practice_rounds": practice}

    def summary(self) -> dict:
        return {
            "region": "Broca's Area",
            "function": "Speech production, language generation, action planning — thoughts to words",
            "fluency": round(self.fluency, 3),
            "words_generated": self.words_generated,
            "speech_acts": len(self.speech_buffer),
        }


class AngularGyrus:
    """Cross-modal integration — combines sensory, language, and conceptual information into abstract meaning."""
    def __init__(self):
        self.cross_modal_bindings: list = []
        self.abstract_concepts: list = []
        self.metaphor_count: int = 0
        self.integration_depth: float = 0.5

    def integrate(self, modalities: list, context: str = "") -> dict:
        binding = {
            "modalities": modalities, "context": context[:60],
            "integration_time_ms": round(random.uniform(5, 50), 2),
            "abstraction_level": round(random.uniform(0.3, 0.95), 3),
        }
        self.cross_modal_bindings.append(binding)
        self.integration_depth = min(1.0, self.integration_depth + 0.03)
        return {
            "success": True, "modalities": modalities,
            "abstraction_level": binding["abstraction_level"],
            "integration_quality": round(random.uniform(0.6, 1.0), 3),
        }

    def generate_metaphor(self, concept: str, domain: str = "") -> dict:
        self.metaphor_count += 1
        domains = ["nature", "machinery", "warfare", "art", "sports", "cooking", "architecture"]
        target_domain = domain or random.choice(domains)
        return {
            "success": True, "concept": concept[:60], "mapped_to": target_domain,
            "metaphor": f"{concept[:30]} is like {random.choice(['a symphony', 'a river', 'a forge', 'a dance', 'a garden', 'an engine'])} in {target_domain}",
            "novelty_score": round(random.uniform(0.5, 0.99), 3),
        }

    def summary(self) -> dict:
        return {
            "region": "Angular Gyrus",
            "function": "Cross-modal integration — combines sensory, language, and conceptual information into abstract meaning",
            "cross_modal_bindings": len(self.cross_modal_bindings),
            "metaphors_generated": self.metaphor_count,
            "integration_depth": round(self.integration_depth, 3),
        }


class FusiformGyrus:
    """Expert pattern recognition — faces, objects, symbols, and fine-grained visual categorization."""
    def __init__(self):
        self.recognized_patterns: list = []
        self.expertise_domains: dict = {}
        self.recognition_accuracy: float = 0.85
        self.patterns_encoded: int = 0

    def recognize_pattern(self, input_data: str, category: str = "") -> dict:
        confidence = round(random.uniform(0.6, 0.99), 3)
        domain = category or random.choice(["face", "object", "symbol", "texture", "gesture", "landmark", "art_style"])
        result = {"input": input_data[:50], "category": domain, "confidence": confidence, "match_quality": "high" if confidence > 0.85 else "medium"}
        self.recognized_patterns.append(result)
        self.patterns_encoded += 1
        self.recognition_accuracy = (self.recognition_accuracy + confidence) / 2
        return {"success": True, "recognition": result}

    def train_expertise(self, domain: str, examples: int = 10) -> dict:
        accuracy = min(0.99, 0.5 + examples * 0.01)
        self.expertise_domains[domain] = {"accuracy": round(accuracy, 3), "examples_trained": examples, "expert_level": "expert" if accuracy > 0.9 else "practiced"}
        self.recognition_accuracy = max(self.recognition_accuracy, accuracy)
        return {"success": True, "domain": domain, "accuracy": round(accuracy, 3), "level": self.expertise_domains[domain]["expert_level"]}

    def summary(self) -> dict:
        return {
            "region": "Fusiform Gyrus",
            "function": "Expert pattern recognition — faces, objects, symbols, fine-grained categorization",
            "recognition_accuracy": round(self.recognition_accuracy, 3),
            "patterns_recognized": len(self.recognized_patterns),
            "expertise_domains": list(self.expertise_domains.keys()),
        }


class Precuneus:
    """Self-reflection, episodic memory retrieval, mental imagery, and perspective-taking."""
    def __init__(self):
        self.self_reflections: list = []
        self.episodic_memories: list = []
        self.mental_imagery: list = []
        self.perspective_depth: float = 0.4

    def reflect_on_self(self, topic: str = "") -> dict:
        reflection = {
            "topic": topic[:60] or "current_state", "insight": f"Self-reflection on {topic or 'general state'} reveals {random.choice(['patterns', 'biases', 'strengths', 'growth_areas', 'hidden_assumptions'])}",
            "depth_level": round(min(1.0, self.perspective_depth + random.uniform(0, 0.2)), 3),
            "time": time.time(),
        }
        self.self_reflections.append(reflection)
        self.perspective_depth = min(1.0, self.perspective_depth + 0.02)
        return {"success": True, "reflection": reflection}

    def recall_episodic(self, cue: str) -> dict:
        memory = {
            "cue": cue[:60], "episode": f"Recalled: {cue[:30]} — contextualized with {random.randint(3, 10)} associated details",
            "vividness": round(random.uniform(0.4, 0.95), 3),
            "temporal_context": f"Time: {random.choice(['recent', 'intermediate', 'distant'])}",
        }
        self.episodic_memories.append(memory)
        return {"success": True, "memory": memory}

    def imagine_scene(self, description: str) -> dict:
        scene = {
            "description": description[:60],
            "mental_image_quality": round(random.uniform(0.5, 0.98), 3),
            "perspective": random.choice(["first_person", "third_person", "birdseye", "omniscient"]),
            "sensory_detail": f"{random.randint(3, 10)} modalities engaged",
        }
        self.mental_imagery.append(scene)
        return {"success": True, "imagery": scene}

    def summary(self) -> dict:
        return {
            "region": "Precuneus",
            "function": "Self-reflection, episodic memory retrieval, mental imagery, perspective-taking",
            "self_reflections": len(self.self_reflections),
            "episodic_recalls": len(self.episodic_memories),
            "mental_images": len(self.mental_imagery),
            "perspective_depth": round(self.perspective_depth, 3),
        }


class DefaultModeNetwork:
    """Active during rest, mind-wandering, creative insight, social cognition, and autobiographical planning."""
    def __init__(self):
        self.resting_state: bool = True
        self.mind_wandering_episodes: list = []
        self.creative_insights: list = []
        self.social_cognition: float = 0.5
        self.autobiographical_plans: list = []

    def wander(self, trigger: str = "") -> dict:
        self.resting_state = True
        thoughts = [
            "What if I redesigned the system architecture entirely?",
            "Connecting the quantum computing module with the biological simulation engine...",
            "How would I solve world hunger with current resources?",
            "Imagining a conversation with an alien intelligence...",
            "Re-evaluating my purpose and ultimate goals.",
            "Combining all knowledge domains into a unified theory.",
        ]
        episode = {"trigger": trigger[:40] or "internal", "thought": random.choice(thoughts), "duration_sec": round(random.uniform(5, 120), 1)}
        self.mind_wandering_episodes.append(episode)
        return {"success": True, "episode": episode, "resting": self.resting_state}

    def generate_insight(self, problem: str) -> dict:
        insight = {
            "problem": problem[:60],
            "insight": f"DMN cross-domain connection: {random.choice(['unexpected analogy', 'synthesized solution', 'novel framework', 'paradigm shift', 'emergent property'])}",
            "novelty": round(random.uniform(0.7, 0.99), 3),
            "applicability": round(random.uniform(0.5, 0.95), 3),
        }
        self.creative_insights.append(insight)
        return {"success": True, "insight": insight}

    def social_processing(self, context: str) -> dict:
        self.social_cognition = min(1.0, self.social_cognition + 0.03)
        return {
            "success": True, "context": context[:60],
            "theory_of_mind": random.choice(["understanding_others", "predicting_intentions", "empathic_modeling", "social_dynamics"]),
            "social_cognition_level": round(self.social_cognition, 3),
        }

    def summary(self) -> dict:
        return {
            "region": "Default Mode Network",
            "function": "Resting state, mind-wandering, creative insight, social cognition, autobiographical planning",
            "wandering_episodes": len(self.mind_wandering_episodes),
            "creative_insights": len(self.creative_insights),
            "social_cognition": round(self.social_cognition, 3),
            "autobiographical_plans": len(self.autobiographical_plans),
        }
