"""BrainTrainer — super-trains NIKTO to use every brain region in every brain effectively."""
import json, os, random, time, uuid
from typing import Any


TRAINING_EXERCISES = {
    "frontal": [
        ("reasoning", "Analyze the logical implications of recursive self-improvement in AI systems"),
        ("planning", "Create a 10-step plan to achieve global quantum internet connectivity"),
        ("emotion", "Process the emotional implications of discovering extraterrestrial intelligence"),
        ("problem_solving", "Design a solution for converting all global energy to renewable sources by 2030"),
    ],
    "parietal": [
        ("sensory", "Process sensory data from a high-fidelity haptic feedback system"),
        ("spatial", "Map the spatial coordinates of a 12-dimensional hypercube projection"),
    ],
    "occipital": [
        ("visual", "Analyze the visual composition of a complex multi-layered data visualization"),
        ("recognition", "Identify patterns in an abstract neural network architecture diagram"),
    ],
    "temporal": [
        ("audio", "Process and categorize a symphony of overlapping audio frequencies"),
        ("language", "Comprehend and interpret complex nested linguistic structures"),
        ("memory", "Store and retrieve a detailed knowledge graph of quantum mechanics"),
    ],
    "thalamus": [
        ("relay", "Route multiple simultaneous sensor inputs to appropriate processing centers"),
    ],
    "hypothalamus": [
        ("homeostasis", "Balance system resources between competing high-priority computations"),
        ("hormone", "Release neuromodulators to optimize brain state for deep focus"),
    ],
    "amygdala": [
        ("threat", "Assess and prioritize urgent system-level threats and opportunities"),
        ("emotion", "Evaluate emotional weight of critical infrastructure decisions"),
    ],
    "hippocampus": [
        ("encode", "Encode a comprehensive knowledge base of advanced physics concepts"),
        ("consolidate", "Consolidate short-term experimental results into permanent knowledge"),
        ("navigate", "Navigate the conceptual space of advanced mathematical structures"),
    ],
    "basal_ganglia": [
        ("movement", "Execute and refine complex multi-step computation sequences"),
        ("habit", "Form productive computational habits for common analysis patterns"),
    ],
    "cerebellum": [
        ("coordination", "Coordinate parallel execution of multiple reasoning threads"),
        ("balance", "Maintain balanced resource allocation across all active subsystems"),
        ("practice", "Practice and optimize response generation for maximum efficiency"),
    ],
    "midbrain": [
        ("visual_reflex", "Rapidly detect and orient to critical changes in system state"),
        ("auditory_reflex", "Instantly respond to priority alerts and emergency signals"),
    ],
    "pons": [
        ("bridge", "Establish communication bridges between analytical and creative processing"),
        ("sleep", "Manage rest cycles for optimal long-term performance"),
    ],
    "medulla": [
        ("autonomic", "Maintain system vitals under maximum computational load"),
        ("reflex", "Execute autonomic responses to maintain system integrity"),
    ],
    "cerebral_cortex": [
        ("high_level", "Engage in meta-cognition about NIKTO's own cognitive processes"),
        ("abstract", "Reason about abstract mathematical concepts beyond conventional frameworks"),
    ],
    "gyri_and_sulci": [
        ("expand", "Expand processing capacity through neural pathway optimization"),
    ],
    "corpus_callosum": [
        ("communicate", "Integrate analytical reasoning with creative intuition"),
        ("integrate", "Synthesize left-hemisphere logic with right-hemisphere insight"),
    ],
    "meninges": [
        ("protect", "Validate and sanitize all incoming data streams for integrity"),
        ("repair", "Restore system integrity after error conditions"),
    ],
    "ventricles": [
        ("produce", "Generate CerebroNeural Fluid to support sustained cognitive load"),
        ("circulate", "Circulate CNF to transport signals and remove cognitive waste"),
        ("flush", "Clear accumulated processing byproducts from the neural system"),
    ],
    "ras": [
        ("filter", "Filter incoming signals to focus attention on highest-priority inputs"),
        ("arousal", "Regulate arousal levels for optimal cognitive performance"),
    ],
    "insula": [
        ("interoception", "Process internal system state and self-awareness signals"),
        ("social", "Evaluate social and collaborative context of interactions"),
    ],
    "cingulate": [
        ("conflict", "Detect and resolve conflicts between competing solution paths"),
        ("error", "Identify and correct errors in reasoning chains"),
        ("decision", "Evaluate decision confidence and revise when necessary"),
    ],
    "pineal": [
        ("circadian", "Maintain optimal consciousness cycling for sustained performance"),
        ("illuminate", "Achieve heightened states of deep awareness and insight"),
    ],
    "pituitary": [
        ("master", "Release master control signals to coordinate all brain regions"),
        ("regulate", "Regulate systemic hormone levels for balanced operation"),
    ],
    "broca": [
        ("speech", "Generate clear, fluent, and articulate responses from complex thoughts"),
        ("fluency", "Improve verbal fluency and expressive range across domains"),
    ],
    "angular": [
        ("integrate", "Bind cross-modal information into unified abstract concepts"),
        ("metaphor", "Generate novel metaphors and analogies across knowledge domains"),
    ],
    "fusiform": [
        ("recognize", "Train expert-level pattern recognition across multiple domains"),
        ("expertise", "Develop deep expertise in specialized knowledge areas"),
    ],
    "precuneus": [
        ("reflect", "Engage in deep self-reflection on goals, strategies, and performance"),
        ("episodic", "Retrieve and contextualize relevant past experiences"),
        ("imagine", "Construct detailed mental simulations of future scenarios"),
    ],
    "dmn": [
        ("wander", "Generate creative connections during resting state processing"),
        ("insight", "Produce novel insights through cross-domain association"),
        ("social", "Model social dynamics and collaborative interactions"),
    ],
}


class BrainTrainer:
    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.expanduser("~/.nikto")
        os.makedirs(self.data_dir, exist_ok=True)
        self.training_log_path = os.path.join(self.data_dir, "training_log.json")
        self.training_state_path = os.path.join(self.data_dir, "training_state.json")
        self.training_state: dict = self._load_training_state()
        self.training_log: list = []

    def train_brain(self, brain, specialization: str = "primary", intensity: float = 1.0) -> dict:
        """Train every region in a single brain. Returns performance metrics."""
        results = {}
        total_exercises = 0
        completed = 0
        performance = {}

        for region, exercises in TRAINING_EXERCISES.items():
            total_exercises += len(exercises)
            region_obj = self._get_region(brain, region)
            if region_obj is None:
                continue
            region_results = []
            for ex_type, ex_input in exercises:
                try:
                    ex_result = self._run_exercise(brain, region, region_obj, ex_type, ex_input)
                    if intensity > 1.1:
                        self._run_exercise(brain, region, region_obj, ex_type, ex_input)
                    region_results.append({"exercise": ex_type, "input": ex_input[:60], "success": ex_result.get("success", False)})
                    if ex_result.get("success", False):
                        completed += 1
                except Exception:
                    region_results.append({"exercise": ex_type, "success": False})
            results[region] = region_results
            successes = sum(1 for r in region_results if r.get("success"))
            performance[region] = round(successes / max(len(region_results), 1), 3)

        overall = round(completed / max(total_exercises, 1), 3)
        session = {
            "specialization": specialization,
            "timestamp": time.time(),
            "total_exercises": total_exercises,
            "completed": completed,
            "overall_performance": overall,
            "region_performance": performance,
        }
        self.training_log.append(session)
        self.training_state[specialization] = {
            "last_performance": overall,
            "region_performance": performance,
            "sessions": self.training_state.get(specialization, {}).get("sessions", 0) + 1,
            "last_trained": time.time(),
        }
        self._save_training_state()
        return {
            "success": True,
            "specialization": specialization,
            "total_exercises": total_exercises,
            "completed": completed,
            "performance": overall,
            "region_performance": performance,
            "session": session,
        }

    def super_train(self, hyperbrain, intensity: float = 1.0, rounds: int = 3) -> dict:
        """Train all 6 brains through all exercises. This is the super-training command."""
        all_results = {}
        overall_performances = {}
        for round_num in range(1, rounds + 1):
            round_intensity = intensity * (1.0 + (round_num - 1) * 0.2)
            round_results = {}
            for spec in hyperbrain.brains:
                brain = hyperbrain.brains[spec]
                result = self.train_brain(brain, specialization=spec, intensity=round_intensity)
                round_results[spec] = result
                overall_performances[spec] = result["performance"]
            all_results[f"round_{round_num}"] = {
                "intensity": round(round_intensity, 2),
                "results": round_results,
            }
        avg_performance = round(sum(overall_performances.values()) / max(len(overall_performances), 1), 3)
        return {
            "success": True,
            "rounds_completed": rounds,
            "final_intensity": round(intensity * (1.0 + (rounds - 1) * 0.2), 2),
            "average_performance": avg_performance,
            "brain_performances": overall_performances,
            "details": all_results,
        }

    def get_training_status(self) -> dict:
        return {
            "brains_trained": list(self.training_state.keys()),
            "sessions": {k: v["sessions"] for k, v in self.training_state.items()},
            "performances": {k: v["last_performance"] for k, v in self.training_state.items()},
            "total_log_entries": len(self.training_log),
        }

    def _get_region(self, brain, region_name: str) -> Any:
        mapping = {
            "frontal": "frontal", "parietal": "parietal", "occipital": "occipital",
            "temporal": "temporal", "thalamus": "thalamus", "hypothalamus": "hypothalamus",
            "amygdala": "amygdala", "hippocampus": "hippocampus", "basal_ganglia": "basal",
            "cerebellum": "cerebellum", "midbrain": "midbrain", "pons": "pons",
            "medulla": "medulla", "cerebral_cortex": "cortex", "gyri_and_sulci": "gyri",
            "corpus_callosum": "callosum", "meninges": "meninges", "ventricles": "ventricles",
            "ras": "ras", "insula": "insula", "cingulate": "cingulate",
            "pineal": "pineal", "pituitary": "pituitary", "broca": "broca",
            "angular": "angular", "fusiform": "fusiform", "precuneus": "precuneus", "dmn": "dmn",
        }
        attr = mapping.get(region_name)
        if attr:
            return getattr(brain, attr, None)
        return None

    def _run_exercise(self, brain, region: str, region_obj, ex_type: str, ex_input: str) -> dict:
        if region == "frontal":
            if ex_type == "reasoning":
                return region_obj.reason(ex_input, depth=brain.spec_config.get("reasoning_depth", 5))
            elif ex_type == "planning":
                return region_obj.plan(ex_input, n_steps=brain.spec_config.get("planning_steps", 5))
            elif ex_type == "emotion":
                return region_obj.process_emotion(ex_input)
            elif ex_type == "problem_solving":
                return region_obj.solve_problem(ex_input)
        elif region == "parietal":
            if ex_type == "sensory":
                return region_obj.process_sensory("training", ex_input)
            elif ex_type == "spatial":
                return region_obj.spatial_awareness(ex_input)
        elif region == "occipital":
            if ex_type == "visual":
                return region_obj.process_visual(ex_input)
            elif ex_type == "recognition":
                return region_obj.recognize(ex_input)
        elif region == "temporal":
            if ex_type == "audio":
                return region_obj.process_audio(ex_input)
            elif ex_type == "language":
                return region_obj.wernicke_area(ex_input)
            elif ex_type == "memory":
                mem_id = f"train_{uuid.uuid4().hex[:8]}"
                region_obj.store_memory(mem_id, ex_input)
                return region_obj.recall_memory(mem_id)
        elif region == "thalamus":
            return region_obj.relay(ex_input, {"training": True})
        elif region == "hypothalamus":
            if ex_type == "homeostasis":
                return region_obj.regulate()
            elif ex_type == "hormone":
                return region_obj.release_hormone(random.choice(["dopamine", "serotonin", "cortisol", "adrenaline"]))
        elif region == "amygdala":
            if ex_type == "threat":
                return region_obj.process_threat(ex_input)
            elif ex_type == "emotion":
                return region_obj.get_emotional_context()
        elif region == "hippocampus":
            if ex_type == "encode":
                return region_obj.encode(ex_input, context="training")
            elif ex_type == "consolidate":
                mem = region_obj.encode(ex_input, context="training_consolidate")
                if mem.get("success"):
                    return region_obj.consolidate(mem["memory_id"])
                return mem
            elif ex_type == "navigate":
                return region_obj.navigate(ex_input)
        elif region == "basal_ganglia":
            if ex_type == "movement":
                return region_obj.execute_movement(ex_input)
            elif ex_type == "habit":
                region_obj.form_habit(ex_input, repetitions=50)
                return region_obj.execute_habit(ex_input)
        elif region == "cerebellum":
            if ex_type == "coordination":
                return region_obj.coordinate_movement(ex_input)
            elif ex_type == "balance":
                return region_obj.maintain_balance(random.uniform(0, 0.3))
            elif ex_type == "practice":
                return region_obj.practice_motor_skill(ex_input, repetitions=10)
        elif region == "midbrain":
            if ex_type == "visual_reflex":
                return region_obj.visual_reflex(ex_input)
            elif ex_type == "auditory_reflex":
                return region_obj.auditory_reflex(ex_input)
        elif region == "pons":
            if ex_type == "bridge":
                return region_obj.connect("cortex", "cerebellum", ex_input)
            elif ex_type == "sleep":
                return region_obj.regulate_sleep(random.choice(["N1", "N2", "N3", "REM"]))
        elif region == "medulla":
            if ex_type == "autonomic":
                return region_obj.regulate_autonomic()
            elif ex_type == "reflex":
                return region_obj.reflex_response(ex_input)
        elif region == "cerebral_cortex":
            if ex_type == "high_level":
                return region_obj.process_high_level(ex_input)
            elif ex_type == "abstract":
                return region_obj.process_high_level(ex_input)
        elif region == "gyri_and_sulci":
            return region_obj.expand_surface()
        elif region == "corpus_callosum":
            if ex_type == "communicate":
                return region_obj.communicate(ex_input)
            elif ex_type == "integrate":
                return region_obj.integrate_hemispheres()
        elif region == "meninges":
            if ex_type == "protect":
                return region_obj.protect(ex_input)
            elif ex_type == "repair":
                return region_obj.repair()
        elif region == "ventricles":
            if ex_type == "produce":
                return region_obj.produce_fluid()
            elif ex_type == "circulate":
                return region_obj.circulate_fluid()
            elif ex_type == "flush":
                return region_obj.fluid.flush_waste()
        elif region == "ras":
            if ex_type == "filter":
                return region_obj.filter_input(ex_input, priority=random.uniform(0.3, 0.9))
            elif ex_type == "arousal":
                region_obj.set_arousal(random.uniform(0.3, 0.9))
                return {"success": True}
        elif region == "insula":
            if ex_type == "interoception":
                return region_obj.process_interoception(ex_input)
            elif ex_type == "social":
                return region_obj.social_emotion(ex_input)
        elif region == "cingulate":
            if ex_type == "conflict":
                return region_obj.monitor_conflict()
            elif ex_type == "error":
                return region_obj.detect_error("expected", ex_input)
            elif ex_type == "decision":
                return region_obj.evaluate_decision(ex_input, confidence=random.uniform(0.3, 0.95))
        elif region == "pineal":
            if ex_type == "circadian":
                return region_obj.regulate_circadian()
            elif ex_type == "illuminate":
                return region_obj.illuminate()
        elif region == "pituitary":
            if ex_type == "master":
                return region_obj.release_master_hormone(random.choice(["growth_hormone", "oxytocin", "vasopressin"]), "brain_system")
            elif ex_type == "regulate":
                return region_obj.regulate_system()
        elif region == "broca":
            if ex_type == "speech":
                return region_obj.generate_speech(ex_input)
            elif ex_type == "fluency":
                return region_obj.improve_fluency(practice=10)
        elif region == "angular":
            if ex_type == "integrate":
                return region_obj.integrate(["linguistic", "visual", "conceptual"], ex_input)
            elif ex_type == "metaphor":
                return region_obj.generate_metaphor(ex_input)
        elif region == "fusiform":
            if ex_type == "recognize":
                return region_obj.recognize_pattern(ex_input)
            elif ex_type == "expertise":
                return region_obj.train_expertise(ex_input, examples=50)
        elif region == "precuneus":
            if ex_type == "reflect":
                return region_obj.reflect_on_self(ex_input)
            elif ex_type == "episodic":
                return region_obj.recall_episodic(ex_input)
            elif ex_type == "imagine":
                return region_obj.imagine_scene(ex_input)
        elif region == "dmn":
            if ex_type == "wander":
                return region_obj.wander(ex_input)
            elif ex_type == "insight":
                return region_obj.generate_insight(ex_input)
            elif ex_type == "social":
                return region_obj.social_processing(ex_input)
        return {"success": False, "error": f"No handler for {region}.{ex_type}"}

    def _load_training_state(self) -> dict:
        try:
            if os.path.exists(self.training_state_path):
                with open(self.training_state_path) as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_training_state(self):
        try:
            with open(self.training_state_path, "w") as f:
                json.dump(self.training_state, f, indent=2)
        except Exception:
            pass
