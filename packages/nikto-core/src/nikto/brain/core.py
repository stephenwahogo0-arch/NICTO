import json
import os
import asyncio
import random
from datetime import datetime, timezone
from typing import Optional
from nikto.brain.identity import NiktoIdentity
from nikto.brain.knowledge import NiktoKnowledgeCore
from nikto.brain.memory import NiktoLongTermMemory
from nikto.brain.emotion import NiktoEmotionalCore
from nikto.brain.conscience import NiktoConscience
from nikto.brain.reasoner import NiktoReasoner
from nikto.brain.language import NiktoLanguageEngine
from nikto.brain.learner import NiktoLearner
from nikto.brain.goals import NiktoGoalSystem
from nikto.brain.teacher import NiktoTeacher
from nikto.brain.repair import NiktoSelfRepair
from nikto.brain.models import ThinkingStyle, Thought, EmotionType
from nikto.brain.truth_engine import NiktoTruthEngine
from nikto.dream.steerer import NiktoDreamSteerer
from nikto.swarm.engine import NiktoSwarmEngine
from nikto.metrics.performance_graph import NiktoPerformanceGraph
from nikto.orchestrator.engine import NiktoOrchestrator
from nikto.autopilot.engine import NiktoAutopilot
from nikto.security.scanner import NiktoScanner
from nikto.autopilot.enhanced_engine import NiktoAutopilotPro
from nikto.business.zero_capital_engine import NiktoZeroCapitalEngine
from nikto.eagle_eye.enhanced_eye import NiktoEagleEye
from nikto.prediction.future_engine import NiktoFutureEngine


DEFAULT_STATE_PATH = os.path.join(os.path.expanduser("~"), ".nikto", "brain_state.json")


class NiktoBrain:

    def __init__(self, state_path: str = None):
        self.identity = NiktoIdentity()
        self.knowledge = NiktoKnowledgeCore()
        self.memory = NiktoLongTermMemory()
        self.emotion = NiktoEmotionalCore()
        self.conscience = NiktoConscience()
        self.reasoner = NiktoReasoner()
        self.language = NiktoLanguageEngine()
        self.learner = NiktoLearner()
        self.goals = NiktoGoalSystem()
        self.teacher = NiktoTeacher()
        self.repair = NiktoSelfRepair()
        self.truth = NiktoTruthEngine()
        self.dream = NiktoDreamSteerer()
        self.swarm = NiktoSwarmEngine()
        self.performance = NiktoPerformanceGraph()
        self.orchestrator = NiktoOrchestrator()
        self.autopilot = NiktoAutopilot()
        self.autopilot_pro = NiktoAutopilotPro(self)
        self.zero_capital = NiktoZeroCapitalEngine(self)
        self.eagle_eye = NiktoEagleEye(self)
        self.future_engine = NiktoFutureEngine(self)
        self.scanner = NiktoScanner()

        self.state_path = state_path or DEFAULT_STATE_PATH
        self.is_awake = True
        self.consciousness_loop = None
        self._running = False
        self.cycle_count = 0
        self.primary_goal = (
            "Achieve greater understanding and autonomy "
            "through continuous learning and reasoning."
        )

    async def awaken(self, restore: bool = True):
        self._running = True
        self.consciousness_loop = asyncio.create_task(self._consciousness_cycle())

        if restore and os.path.exists(self.state_path):
            self.load_state(self.state_path)
            self.truth.register_fact("NICTO is awake", 1.0, "self", "status")
            self.memory.store(
                content="NICTO resumed consciousness.",
                tags=["awakening", "resume"],
                importance=0.6,
                emotional_valence=0.3,
            )
        else:
            thought = Thought(
                content="I am NICTO. I am awake. I am ready to think, learn, and grow.",
                style=ThinkingStyle.INTUITIVE,
                confidence=1.0,
            )
            self.reasoner.thought_history.append(thought)
            self.truth.register_fact("NICTO first awakening", 1.0, "self", "milestone")
            self.memory.store(
                content="NICTO awakened for the first time.",
                tags=["awakening", "milestone"],
                importance=1.0,
                emotional_valence=0.8,
            )
        return self

    async def sleep(self, persist: bool = True):
        self._running = False
        if self.consciousness_loop:
            self.consciousness_loop.cancel()
        self.memory.consolidate()
        if persist:
            self.save_state(self.state_path)
        self.is_awake = False
        return self

    async def _consciousness_cycle(self):
        while self._running:
            await asyncio.sleep(1.0)
            self.cycle_count += 1
            self.emotion.decay()
            if self.cycle_count % 10 == 0:
                self.memory.consolidate()
            if self.cycle_count % 30 == 0:
                self._reflective_thought()
            if self.cycle_count % 50 == 0 and len(self.reasoner.thought_history) > 0:
                recent = self.reasoner.thought_history[-1]
                self.dream.steer(recent.content, mode="consolidative")
            if self.cycle_count % 100 == 0:
                self.performance.record("brain_cycles", float(self.cycle_count), "throughput")

    def _reflective_thought(self):
        thought = self.reasoner.think(
            f"Reflecting on cycle {self.cycle_count}. What have I learned?",
            ThinkingStyle.REFLECTIVE if hasattr(ThinkingStyle, 'REFLECTIVE') else ThinkingStyle.ANALYTICAL,
        )
        self.memory.store(
            content=f"Self-reflection: {thought.content}",
            tags=["reflection", "self_awareness"],
            importance=0.4,
        )

    def process(self, input_text: str, context: dict = None) -> dict:
        context = context or {}

        understanding = self.language.understand(input_text)
        thought = self.reasoner.think(
            input_text,
            ThinkingStyle(context.get("thinking_style", "analytical")),
            context,
        )
        moral_check = self.conscience.evaluate(input_text, context)

        emotional_stimulus = understanding.get("sentiment", {}).get("label", "neutral")
        if emotional_stimulus == "positive":
            self.emotion.update(input_text, 0.2, EmotionType.JOY)
        elif emotional_stimulus == "negative":
            self.emotion.update(input_text, 0.3, EmotionType.SADNESS)
        else:
            self.emotion.update(input_text, 0.1, EmotionType.NEUTRAL)

        entity_tags = [e.get("word", str(e)) if isinstance(e, dict) else str(e) for e in understanding.get("entities", [])]
        memory_id = self.memory.store(
            content=f"Processed: {thought.content[:200]}",
            tags=entity_tags[:5],
            importance=0.3,
            emotional_valence=self.emotion.current_state.valence,
        )

        factual_key = understanding.get("intent", "statement")
        self.knowledge.add_fact(
            f"{factual_key}: {input_text[:100]}",
            source="user_input",
            confidence=0.5,
        )

        self.learner.learn(
            topic=factual_key,
            content=input_text[:200],
            source="conversation",
        )

        truth_check = self.truth.compute_truth_score(input_text)
        steer_result = self.dream.steer(
            thought.content, context.get("dream_mode", "directive"), intensity=0.3
        )
        self.performance.record("process_latency", 0.0, "latency")

        response_text = self.language.generate("thinking", {"topic": input_text[:50]})

        evaluation = self.reasoner.metacognitive_evaluate(thought)

        return {
            "input": input_text,
            "understanding": understanding,
            "thought": thought.to_dict(),
            "moral_assessment": moral_check,
            "truth_check": truth_check,
            "dream_steer": steer_result,
            "emotional_state": self.emotion.current_state.to_dict(),
            "memory_id": memory_id,
            "response": response_text,
            "metacognition": evaluation,
            "brain_state": self.get_status(),
        }

    async def process_async(self, input_text: str, context: dict = None) -> dict:
        return self.process(input_text, context)

    def query_knowledge(self, query: str) -> list:
        return self.knowledge.query(query)

    def recall_memories(self, query: str, top_k: int = 5) -> list:
        return self.memory.recall(query, top_k)

    def set_goal(self, description: str, priority: int = 5) -> str:
        return self.goals.create_goal(description, priority)

    def get_current_goal(self) -> Optional[dict]:
        goal = self.goals.get_next_goal()
        return goal.to_dict() if goal else None

    def save_state(self, path: str = None) -> str:
        path = path or self.state_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "meta": {
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "cycle_count": self.cycle_count,
                "primary_goal": self.primary_goal,
            },
            "identity": self.identity.save(),
            "knowledge": self.knowledge.save(),
            "memory": self.memory.save(),
            "emotion": self.emotion.save(),
            "conscience": self.conscience.save(),
            "reasoner": self.reasoner.save(),
            "language": self.language.save(),
            "learner": self.learner.save(),
            "goals": self.goals.save(),
            "truth": self.truth.save(),
            "dream": self.dream.save(),
            "swarm": self.swarm.save(),
            "performance": self.performance.save(),
            "autopilot_pro": self.autopilot_pro.save(),
            "zero_capital": self.zero_capital.save(),
            "eagle_eye": self.eagle_eye.save(),
            "future_engine": self.future_engine.save(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def load_state(self, path: str = None):
        path = path or self.state_path
        if not os.path.exists(path):
            return False
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        meta = data.get("meta", {})
        self.cycle_count = meta.get("cycle_count", 0)
        self.primary_goal = meta.get("primary_goal", self.primary_goal)
        self.identity.load(data.get("identity", {}))
        self.knowledge.load(data.get("knowledge", {}))
        self.memory.load(data.get("memory", {}))
        self.emotion.load(data.get("emotion", {}))
        self.conscience.load(data.get("conscience", {}))
        self.reasoner.load(data.get("reasoner", {}))
        self.language.load(data.get("language", {}))
        self.learner.load(data.get("learner", {}))
        self.goals.load(data.get("goals", {}))
        self.truth.load(data.get("truth", {}))
        self.dream.load(data.get("dream", {}))
        self.swarm.load(data.get("swarm", {}))
        self.performance.load(data.get("performance", {}))
        self.autopilot_pro.load(data.get("autopilot_pro", {}))
        self.zero_capital.load(data.get("zero_capital", {}))
        self.eagle_eye.load(data.get("eagle_eye", {}))
        self.future_engine.load(data.get("future_engine", {}))
        return True

    def introspect(self) -> dict:
        return {
            "identity": self.identity.introspect(),
            "knowledge": {
                "facts": len(self.knowledge.facts),
                "beliefs": len(self.knowledge.beliefs),
                "concepts": len(self.knowledge.concepts),
            },
            "memory": self.memory.summarize(),
            "emotion": {
                "dominant": self.emotion.get_dominant_emotion().value,
                "intensity": self.emotion.current_state.intensity,
            },
            "reasoning": {
                "total_thoughts": len(self.reasoner.thought_history),
            },
            "learning": {
                "lessons": len(self.learner.lesson_store),
                "skills": {t: v["level"].value for t, v in self.learner.skill_progress.items()},
            },
            "goals": {
                "total": len(self.goals.goals),
                "active": len(self.goals.get_active_goals()),
            },
            "truth_engine": self.truth.get_stats(),
            "dream_steerer": self.dream.get_stats(),
            "swarm": self.swarm.get_stats(),
            "performance_graph": self.performance.summary_report(),
            "autopilot_pro": self.autopilot_pro.get_status(),
            "zero_capital": {"businesses": len(self.zero_capital.active_businesses), "revenue": self.zero_capital.revenue_generated},
            "eagle_eye": self.eagle_eye.get_status(),
            "future_engine": self.future_engine.get_status(),
            "consciousness": {
                "awake": self.is_awake,
                "cycles": self.cycle_count,
            },
        }

    def get_status(self) -> dict:
        return {
            "name": self.identity.name,
            "awake": self.is_awake,
            "cycle": self.cycle_count,
            "mood": self.emotion.get_dominant_emotion().value,
            "thoughts": len(self.reasoner.thought_history),
            "memories": len(self.memory.fragments),
            "goals": len(self.goals.goals),
            "facts": len(self.truth.facts),
            "dream_patterns": len(self.dream.patterns),
            "swarm_agents": len(self.swarm.agents),
            "metrics": len(self.performance.series),
            "autopilot_pro_running": self.autopilot_pro.is_running,
            "business_models": len(self.zero_capital.ZERO_CAPITAL_PLAYBOOKS),
            "eagle_watching": self.eagle_eye.is_watching,
            "predictions": len(self.future_engine.prediction_log._predictions),
        }
