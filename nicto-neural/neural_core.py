"""NeuralCore — top-level NICTO Neural Core facade. Single entry point."""

import torch

from .brain.consciousness import NeuralConsciousness
from .brain.orchestrator import BrainRouter
from .evolution.validation import ValidationEngine
from .learning.curriculum import CurriculumScheduler
from .learning.reward_model import RewardModel
from .learning.reward_shaper import RewardShaper
from .learning.rl_agent import PPOAgent
from .learning.trainer import NeuralTrainer
from .neural.config import NeuralConfig
from .reasoning.brainboost import BrainBoost
from .reasoning.consistency import ConsistencyTracker
from .safety.reward_hacking import RewardHackingDetector


class NeuralCore:
    """Top-level NICTO Neural Core facade. Single entry point: process(input) -> output."""

    VERSION = "1.0.0"
    PARAMETER_COUNT = "284B+ (MoE architecture)"

    def __init__(self, config: NeuralConfig = None):
        if config is None:
            config = NeuralConfig()
        self.config = config

        self.consciousness = NeuralConsciousness(config)
        self.memory = self.consciousness.memory
        self.elo = self.consciousness.elo
        self.curriculum = CurriculumScheduler()
        self.rl_agent = PPOAgent(config)
        self.trainer = NeuralTrainer(
            config, self.consciousness,
            self.memory, self.rl_agent, self.curriculum,
        )
        self.validator = ValidationEngine(self.memory)
        self.brainboost = BrainBoost(config, self.consciousness.brains)
        self.consistency = ConsistencyTracker()
        self.reward_shaper = RewardShaper()
        self.hack_detector = RewardHackingDetector()
        self.reward_model = RewardModel(config)
        self.exploration = self.consciousness.exploration

        self.consciousness.router = BrainRouter(config, self.elo, self.curriculum)

        self.trainer.validator = self.validator
        self._initialized = True

    async def process(self, input_text: str, context: dict = None) -> dict:
        """Main entry point for all NICTO neural processing."""
        result = await self.consciousness.think(input_text, context or {})

        shaped = self.reward_shaper.shape(
            correctness=result.get("confidence", 0.5),
            elo_delta=0.0,
            is_novel=False,
            consistency_score=0.5,
            hacking_detected=False,
        )

        features = self.consciousness.feature_engine.extract(
            input_text, context or {}
        )
        self.memory.add_experience(
            state=features,
            action=0,
            reward=shaped["total"],
            next_state=features,
            done=False,
        )

        result["reward"] = shaped["total"]
        return result

    def train(self, mode: str = "hybrid", epochs: int = 10) -> dict:
        return self.trainer.train(mode=mode, epochs=epochs)

    def validate(self) -> dict:
        return self.validator.evaluate(self.consciousness)

    def get_status(self) -> dict:
        return {
            "version": self.VERSION,
            "parameters": self.PARAMETER_COUNT,
            "think_count": self.consciousness._think_count,
            "memory": self.memory.total_memories(),
            "elo_leaderboard": self.elo.get_leaderboard(),
            "consistency": self.consistency.get_stats(),
            "exploration": self.exploration.get_stats(),
            "hacking": self.hack_detector.get_stats(),
            "brainboost_mode": self.brainboost._mode,
            "initialized": self._initialized,
        }
