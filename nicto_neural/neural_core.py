import os
import hashlib
from typing import Any, Dict, List, Optional
import numpy as np
import torch
import torch.nn as nn

from .neural.config import NeuralConfig, BASE_CONFIG
from .neural.elo_system import ELOEstimator
from .neural.exploration import ExplorationEngine
from .neural.model_selector import ModelSelector
from .perception.tokenizer import Tokenizer
from .perception.feature_engine import FeatureEngine
from .perception.normalizer import FeatureNormalizer
from .memory.manager import MemoryManager
from .brain.primary import PrimaryBrain
from .brain.analytical import AnalyticalBrain
from .brain.creative import CreativeBrain
from .brain.strategic import StrategicBrain
from .brain.knowledge import KnowledgeBrain
from .brain.intuitive import IntuitiveBrain
from .brain.orchestrator import BrainRouter
from .brain.consciousness import NeuralConsciousness
from .reasoning.planner import Planner
from .reasoning.evaluator import Evaluator
from .reasoning.reflection import ReflectionEngine
from .reasoning.confidence import ConfidenceCalibrator
from .reasoning.chain_engine import ChainEngine
from .reasoning.brainboost import BrainBoost
from .reasoning.consistency import ConsistencyTracker
from .reasoning.interpretability import InterpretabilityReporter
from .learning.dataset_builder import DatasetBuilder
from .learning.trainer import NeuralTrainer
from .learning.reward_model import RewardModel
from .learning.reward_shaper import RewardShaper
from .learning.rl_agent import RLAgent
from .learning.experience_buffer import ExperienceBuffer
from .learning.curriculum import Curriculum
from .learning.feedback_loop import FeedbackLoop
from .learning.fine_tune import FineTuner
from .evolution.engine import EvolutionEngine
from .evolution.improvement import ImprovementEngine
from .evolution.validation import ValidationEngine
from .evolution.curriculum_manager import CurriculumManager
from .evolution.cost_estimator import TrainingCostEstimator
from .execution.tools import ToolRegistry
from .execution.actions import ActionExecutor
from .execution.agents import (
    ResearchAgent,
    CodeAgent,
    PlannerAgent,
    MemoryAgent,
    EvaluationAgent,
    ExecutionAgent,
)
from .execution.orchestration import AgentOrchestrator
from .safety.permissions import PermissionManager
from .safety.rollback import RollbackManager
from .safety.audit import AuditLogger
from .safety.policies import PolicyEngine
from .safety.reward_hacking import RewardHackingDetector
from .api.brain_api import BrainAPI
from .api.memory_api import MemoryAPI
from .api.agent_api import AgentAPI
from .api.reflection_api import ReflectionAPI
from .api.evolution_api import EvolutionAPI
from .api.elo_api import ELOAPI


class NeuralCore:
    def __init__(self, config: Optional[NeuralConfig] = None):
        self.config = config or BASE_CONFIG
        
        # 1. Foundation & Shared State
        state_dir = os.path.join(os.path.expanduser("~"), ".nicto", "neural")
        os.makedirs(state_dir, exist_ok=True)
        self.elo = ELOEstimator(state_path=os.path.join(state_dir, "elo_ratings.json"))
        self.exploration = ExplorationEngine()
        self.model_selector = ModelSelector()
        self.tokenizer = Tokenizer()
        self.feature_engine = FeatureEngine()
        self.normalizer = FeatureNormalizer()
        
        # 2. Memory System
        self.memory = MemoryManager()
        
        # 3. Brain Subsystems
        self.brains: Dict[str, nn.Module] = {
            "primary": PrimaryBrain(self.config),
            "analytical": AnalyticalBrain(self.config),
            "creative": CreativeBrain(self.config),
            "strategic": StrategicBrain(self.config),
            "knowledge": KnowledgeBrain(self.config, self.memory),
            "intuitive": IntuitiveBrain(self.config),
        }
        self.router = BrainRouter(self.config, self.elo, self.exploration)
        self.consciousness = NeuralConsciousness(
            self.config,
            self.router,
            self.brains,
            self.elo,
            self.memory,
            self.exploration,
        )
        
        # 4. Reasoning Subsystems
        self.planner = Planner()
        self.evaluator = Evaluator()
        self.reflection = ReflectionEngine(self.memory)
        self.confidence_calibrator = ConfidenceCalibrator()
        self.chain_engine = ChainEngine()
        self.brainboost = BrainBoost()
        self.consistency = ConsistencyTracker()
        self.interpretability = InterpretabilityReporter()
        
        # 5. Learning & Evolution
        self.dataset_builder = DatasetBuilder(self.memory)
        self.trainer = NeuralTrainer(self.config, nn.ModuleList(list(self.brains.values())), self.config.device)
        self.reward_model = RewardModel()
        self.reward_shaper = RewardShaper()
        self.rl_agent = RLAgent(self.config)
        self.experience_buffer = ExperienceBuffer()
        self.curriculum = Curriculum()
        self.feedback_loop = FeedbackLoop(
            self.trainer,
            self.dataset_builder,
            self.reward_model,
            self.evaluator,
            self.reflection,
            self.curriculum,
            self.memory,
        )
        self.fine_tuner = FineTuner(self.config, nn.ModuleList(list(self.brains.values())))
        self.evolution = EvolutionEngine(
            self.memory,
            self.elo,
            self.trainer,
            self.feedback_loop,
            self.curriculum,
            self.evaluator,
        )
        self.improvement = ImprovementEngine(self.memory)
        self.validation = ValidationEngine(self.evaluator, self.elo)
        self.curriculum_manager = CurriculumManager(self.curriculum, self.memory)
        self.cost_estimator = TrainingCostEstimator()
        
        # 6. Execution & Safety
        self.tools = ToolRegistry()
        self.actions = ActionExecutor()
        self.agents = {
            "research": ResearchAgent(),
            "code": CodeAgent(),
            "planner": PlannerAgent(),
            "memory": MemoryAgent(),
            "evaluation": EvaluationAgent(),
            "execution": ExecutionAgent(),
        }
        self.orchestrator = AgentOrchestrator(self.agents, self.tools)
        
        self.permissions = PermissionManager()
        self.rollback = RollbackManager()
        self.audit = AuditLogger()
        self.policies = PolicyEngine()
        self.reward_hacking = RewardHackingDetector()
        
        # 7. Public API Surface
        self.api = {
            "brain": BrainAPI(self.consciousness),
            "memory": MemoryAPI(self.memory),
            "agent": AgentAPI(self.agents, self.tools),
            "reflection": ReflectionAPI(self.reflection),
            "evolution": EvolutionAPI(self.evolution),
            "elo": ELOAPI(self.elo),
        }
        
        # Autopoint router orchestrator links
        self.api["agent"].set_orchestrator(self.orchestrator)
        
    def process(self, task: Dict) -> Dict:
        # Enforce safety policy prior to processing
        allowed, reason = self.policies.enforce("brain:think", task)
        if not allowed:
            self.audit.log_action("system", "brain:think", f"Blocked: {reason}", "SAFETY_BLOCK")
            return {"error": f"Security policy block: {reason}"}
            
        # Log incoming request in audit trail
        task_str = str(task)
        state_hash = hashlib.sha256(task_str.encode()).hexdigest() if "hashlib" in globals() else "hash"
        self.audit.log_action("user", "brain:think", task_str, state_hash)
        
        # Trigger awake if necessary
        if not self.consciousness._awake:
            self.consciousness.awake()
            
        # Process the task
        result = self.consciousness.think(task, domain=task.get("domain", "general"))
        
        # Return structured output
        return result
        
    def train(self, mode: str = "supervised") -> Dict:
        dataset = self.dataset_builder.build()
        if not dataset:
            return {"status": "skipped", "reason": "No interaction data available for training"}
            
        # Estimate training cost
        cost = self.cost_estimator.estimate(len(dataset), mode, epochs=5, device=self.config.device)
        
        # Enforce rate limit/iterations check before starting training
        allowed, reason = self.policies.enforce("train", {"mode": mode})
        if not allowed:
            return {"status": "blocked", "reason": reason}
            
        # Run training loop
        history = self.trainer.train(dataset, mode=mode, epochs=5)
        return {"status": "completed", "history": history, "estimated_cost": cost}
        
    def reflect(self, task: Dict, result: Dict) -> Dict:
        return self.reflection.reflect(task, result)
