"""Neural consciousness — top-level brain coordinator."""

import math

import torch

from ..memory.manager import MemoryManager
from ..neural.brain_heads import BrainHeads
from ..neural.config import NeuralConfig
from ..neural.elo_system import EloSystem
from ..neural.exploration import ExplorationManager
from ..neural.model_selector import ModelSelector
from ..neural.moe_router import MoERouter
from ..neural.transformer import TransformerCore
from ..perception.feature_engine import TaskFeatureEngine
from ..perception.normalizer import FeatureNormalizer
from ..perception.tokenizer import NictoTokenizer


class NeuralConsciousness:
    """Top-level brain coordinator. Single entry point: think(input) -> output."""

    def __init__(self, config: NeuralConfig = None):
        if config is None:
            config = NeuralConfig()
        self.config = config
        self.elo = EloSystem(config)
        self.memory = MemoryManager(config)
        self.exploration = ExplorationManager(config)
        self.feature_engine = TaskFeatureEngine()
        self.normalizer = FeatureNormalizer()
        self.model_selector = ModelSelector()

        self.transformer = TransformerCore(config)
        self.moe = MoERouter(config)
        self.heads = BrainHeads(config)

        from .analytical import AnalyticalBrain
        from .creative import CreativeBrain
        from .intuitive import IntuitiveBrain
        from .knowledge import KnowledgeBrain
        from .primary import PrimaryBrain
        from .strategic import StrategicBrain

        self._curriculum = None

        self.brains = {
            "primary": PrimaryBrain(config, self.elo),
            "analytical": AnalyticalBrain(config, self.elo),
            "creative": CreativeBrain(config, self.elo),
            "strategic": StrategicBrain(config, self.elo),
            "knowledge": KnowledgeBrain(config, self.elo),
            "intuitive": IntuitiveBrain(config, self.elo, self.exploration),
        }
        self.router = None

        self._awake = True
        self._think_count = 0

    async def think(self, input_text: str, context: dict = None) -> dict:
        """Full thinking pipeline."""
        if not self._awake:
            return {"output": "NICTO is in sleep mode", "confidence": 0.0}

        ctx = context or {}
        self._think_count += 1

        raw_features = self.feature_engine.extract(input_text, ctx)
        features = self.normalizer.transform(raw_features)

        dataset_size = self.memory.episodic.count()
        path = self.model_selector.select(dataset_size)

        tokenizer = NictoTokenizer()
        tokens = tokenizer.batch_encode([input_text])
        with torch.no_grad():
            transformer_out = self.transformer(tokens)

        domain = self.feature_engine._detect_domain(input_text)
        use_explore = self.brains["intuitive"].should_explore()

        if self.router:
            active_brains = self.router.select_brains(
                domain,
                self.feature_engine._detect_task_type(input_text),
                n_brains=2,
                use_exploration=use_explore,
            )
        else:
            active_brains = ["analytical", "primary"]

        brain_outputs = {}
        brain_confidences = {}
        with torch.no_grad():
            for brain_name in active_brains:
                brain = self.brains[brain_name]
                result = brain(transformer_out)
                brain_outputs[brain_name] = result.get("output", transformer_out)
                brain_confidences[brain_name] = float(
                    result.get("confidence", torch.tensor(0.5)).mean()
                )

        self.memory.store_episode({
            "input": input_text,
            "brains_used": active_brains,
            "domain": domain,
            "path": path,
            "think_count": self._think_count,
        })

        if not ctx.get("no_elo_update"):
            for brain_name in active_brains:
                self.elo.update(brain_name, domain, 0.7)

        return {
            "output": f"[NICTO processed: {input_text[:50]}]",
            "confidence": max(brain_confidences.values()) if brain_confidences else 0.5,
            "brains_used": active_brains,
            "domain": domain,
            "path": path,
            "think_count": self._think_count,
        }

    def sleep(self) -> None:
        self._awake = False
        self.memory.consolidate()

    def wake(self) -> None:
        self._awake = True

    def save(self, path: str) -> None:
        state = {
            "transformer": self.transformer.state_dict(),
            "elo": {
                b: self.elo.get_all_ratings(b)
                for b in self.config.brain_names
            },
            "think_count": self._think_count,
            "epsilon": self.exploration.get_epsilon(),
        }
        torch.save(state, path)

    def load(self, path: str) -> None:
        state = torch.load(path, map_location="cpu", weights_only=False)
        self.transformer.load_state_dict(state["transformer"])
        self._think_count = state.get("think_count", 0)
