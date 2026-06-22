"""NICTO X — Central orchestrator coordinating all subsystems: neural core, agents, memory, reasoning, distributed execution."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Optional

from nicto_x.core.config import NictoXConfig
from nicto_x.agents.bus import AgentBus
from nicto_x.agents.research_agent import ResearchAgent
from nicto_x.agents.coding_agent import CodingAgent
from nicto_x.agents.planning_agent import PlanningAgent
from nicto_x.agents.evaluation_agent import EvaluationAgent
from nicto_x.agents.memory_agent import MemoryAgent
from nicto_x.agents.vision_agent import VisionAgent
from nicto_x.agents.security_agent import SecurityAgent
from nicto_x.memory.episodic import EpisodicMemory
from nicto_x.memory.semantic import SemanticMemory
from nicto_x.memory.working import WorkingMemory
from nicto_x.memory.consolidation import MemoryConsolidator
from nicto_x.reasoning.tree_of_thought import TreeOfThought
from nicto_x.reasoning.reflection import SelfReflection
from nicto_x.reasoning.confidence import ConfidenceEstimator
from nicto_x.neural.core import NeuralCore, MoEConfig, AttentionConfig
from nicto_x.neural.tokenizer import NeuralTokenizer
from nicto_x.knowledge.graph import KnowledgeGraph
from nicto_x.knowledge.vector_store import VectorStore
from nicto_x.software.engineer import SoftwareEngineer
from nicto_x.research.literature import LiteratureReview
from nicto_x.vision.analyzer import VisionAnalyzer
from nicto_x.security.auth import AuthManager
from nicto_x.self_improvement.benchmark import BenchmarkRunner
from nicto_x.distributed.executor import DistributedExecutor

logger = logging.getLogger("nicto_x")


class NictoXOrchestrator:
    """Main coordinator for NICTO X — wires neural core, agents, memory, reasoning, knowledge, and distributed execution."""

    def __init__(self, config: Optional[NictoXConfig] = None):
        self.config = config or NictoXConfig()
        self.version = self.config.version

        self.bus = AgentBus()
        self.episodic_memory = EpisodicMemory(self.config.memory)
        self.semantic_memory = SemanticMemory(self.config.memory)
        self.working_memory = WorkingMemory(self.config.memory)
        self.consolidator = MemoryConsolidator(self.episodic_memory, self.semantic_memory)

        self.neural_core = NeuralCore(
            vocab_size=32000,
            d_model=768,
            num_layers=12,
            moe=MoEConfig(num_experts=8, top_k=2),
            attention=AttentionConfig(num_heads=8, head_dim=64, max_seq_len=131072),
        )
        self.tokenizer = NeuralTokenizer()
        self.knowledge_graph = KnowledgeGraph()
        self.vector_store = VectorStore(dim=768)
        self.software_engineer = SoftwareEngineer()
        self.research = LiteratureReview()
        self.vision_analyzer = VisionAnalyzer()
        self.auth_manager = AuthManager()
        self.benchmark_runner = BenchmarkRunner()
        self.distributed_executor = DistributedExecutor(min_workers=2, max_workers=8)

        self.tree_of_thought = TreeOfThought(max_paths=5, max_depth=5)
        self.reflection = SelfReflection()
        self.confidence = ConfidenceEstimator()

        self._agents: dict[str, object] = {}
        self._running = False
        self._start_time: float = 0.0

    @property
    def agents(self) -> dict:
        return self._agents

    async def initialize(self):
        logger.info("Initializing NICTO X subsystems...")
        self._agents = {
            "research": ResearchAgent(self.bus, self.config),
            "coding": CodingAgent(self.bus, self.config),
            "planning": PlanningAgent(self.bus, self.config),
            "evaluation": EvaluationAgent(self.bus, self.config),
            "memory": MemoryAgent(self.bus, self.config, self.episodic_memory, self.semantic_memory),
            "vision": VisionAgent(self.bus, self.config),
            "security": SecurityAgent(self.bus, self.config),
        }
        for name, agent in self._agents.items():
            await agent.initialize()
            logger.debug("Agent initialized: %s", name)
        logger.info("All %d agents initialized.", len(self._agents))

    async def start(self):
        await self.initialize()
        self._running = True
        self._start_time = time.time()
        await self.distributed_executor.start()
        logger.info("NICTO X orchestrator started.")

    async def stop(self):
        self._running = False
        for name, agent in self._agents.items():
            await agent.shutdown()
        await self.consolidator.run()
        await self.distributed_executor.stop()
        self.neural_core.save()
        self.knowledge_graph.save()
        self.vector_store.save()
        logger.info("NICTO X orchestrator stopped.")

    async def process(self, input_text: str, context: Optional[dict] = None) -> dict:
        context = context or {}
        start_time = time.time()

        await self.working_memory.store("current_input", input_text)

        plan = await self._agents["planning"].create_plan(input_text, context)
        results = {}
        for step in plan.get("steps", []):
            agent_name = step.get("agent", "research")
            agent = self._agents.get(agent_name)
            if agent:
                step_result = await agent.execute(step.get("task", input_text))
                results[agent_name] = step_result

        combined = "\n".join(str(r.get("output", "")) for r in results.values() if r)

        neural_result = self.neural_core.process(input_text, max_tokens=2048)

        thought = self.tree_of_thought.explore(problem=input_text, context=combined)
        reflection_result = self.reflection.evaluate(input_text, thought.get("best_path", combined))
        confidence = self.confidence.estimate(thought.get("best_path", combined), reflection_result)

        evaluation = await self._agents["evaluation"].evaluate({"input": input_text, "output": thought.get("best_path", combined)})

        confidence_score = confidence.get("score", 0.5)
        if confidence.get("should_retry", False) and confidence_score < 0.25:
            thought2 = self.tree_of_thought.explore(problem=f"Re-analyze carefully: {input_text}", context=combined + "\n[Previous analysis was low confidence]")
            confidence2 = self.confidence.estimate(thought2.get("best_path", ""), reflection_result)
            if confidence2.get("score", 0) > confidence_score:
                thought = thought2
                confidence = confidence2

        response = thought.get("best_path", combined)
        if neural_result.confidence > 0.5:
            response = f"{response}\n[Neural analysis: {neural_result.output_text[:100]}]"

        episode = {"input": input_text, "output": response, "plan": plan, "confidence": confidence, "evaluation": evaluation, "reflection": reflection_result, "neural": neural_result.to_dict() if hasattr(neural_result, 'to_dict') else str(neural_result), "timestamp": time.time()}
        await self.episodic_memory.store(episode)
        await self.working_memory.clear()

        elapsed = (time.time() - start_time) * 1000

        return {
            "response": response,
            "confidence": confidence,
            "reasoning_paths": thought.get("paths", []),
            "reflection": reflection_result,
            "evaluation": evaluation,
            "neural_processing": {"tokens": neural_result.tokens_processed, "confidence": neural_result.confidence, "perplexity": neural_result.perplexity, "experts": neural_result.expert_activations, "layers": neural_result.layer_activations, "time_ms": neural_result.processing_time_ms},
            "agents_used": list(results.keys()),
            "plan": plan,
            "latency_ms": round(elapsed, 2),
        }

    async def execute_task(self, task: str, context: Optional[dict] = None) -> dict:
        context = context or {}
        mode = context.get("mode", "auto")

        if mode == "direct":
            agent_name = context.get("agent", "research")
            agent = self._agents.get(agent_name)
            if not agent:
                return {"error": f"Agent '{agent_name}' not found", "available": list(self._agents.keys())}
            result = await agent.execute(task)
            return result

        task_id = await self.distributed_executor.submit(task, {"task": task, "context": context})
        result = self.distributed_executor.get_result(task_id)

        plan = await self._agents["planning"].create_plan(task, context)
        return {"task": task, "result": result, "plan": plan, "task_id": task_id}

    async def process_neural(self, text: str) -> dict:
        result = self.neural_core.process(text)
        return {"output": result.output_text, "confidence": result.confidence, "tokens": result.tokens_processed, "perplexity": result.perplexity, "experts": result.expert_activations, "time_ms": result.processing_time_ms}

    async def search_knowledge(self, query: str, top_k: int = 10) -> dict:
        vector_results = self.vector_store.search(query, top_k=top_k)
        graph_results = self.knowledge_graph.query(query)
        return {"vector_results": vector_results, "graph_results": graph_results, "total": len(vector_results) + len(graph_results)}

    async def generate_code(self, spec: str, language: str = "python") -> dict:
        return await self.software_engineer.generate(spec, language)

    async def research_topic(self, topic: str) -> dict:
        deep = await self.research.deep_search(topic)
        hyp = await self.research.generate_hypothesis(topic)
        return {"literature_review": deep, "hypothesis": hyp}

    async def run_benchmarks(self) -> dict:
        return await self.benchmark_runner.run_full_evaluation(self)

    async def analyze_image(self, image_path: str) -> dict:
        return await self.vision_analyzer.analyze(image_path)

    def get_status(self) -> dict:
        return {
            "running": self._running,
            "uptime": time.time() - self._start_time if self._running else 0,
            "version": self.version,
            "agents": list(self._agents.keys()),
            "neural_core": self.neural_core.get_info(),
            "episodic_count": len(self.episodic_memory),
            "semantic_count": len(self.semantic_memory),
            "vector_store_count": self.vector_store.count(),
            "knowledge_graph": self.knowledge_graph.get_stats(),
            "distributed": self.distributed_executor.get_status(),
            "benchmark_skills": self.benchmark_runner.get_skill_report(),
        }

    def get_memory_status(self) -> dict:
        return {
            "episodic": len(self.episodic_memory),
            "semantic": len(self.semantic_memory),
            "vector_store": self.vector_store.count(),
            "knowledge_graph_nodes": self.knowledge_graph.get_stats().get("nodes", 0),
            "knowledge_graph_edges": self.knowledge_graph.get_stats().get("edges", 0),
        }

    def get_benchmark_status(self) -> dict:
        return {
            "skills": self.benchmark_runner.get_skill_report(),
            "weaknesses": self.benchmark_runner.get_weaknesses(),
            "improvement_plan": self.benchmark_runner.get_improvement_plan(),
        }
