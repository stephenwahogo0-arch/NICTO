from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


class ModelComplexity(Enum):
    BOOST_FIXED = "brainboost_fixed"
    BOOST_TRAINED = "brainboost_trained"
    TRANSFORMER = "transformer"
    TRANSFORMER_RL = "transformer_rl"
    FULL_PIPELINE = "full_pipeline"


class InterpretabilityLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ModelSelection:
    model_type: ModelComplexity
    interpretability: InterpretabilityLevel
    dataset_size: int
    domain: str
    estimated_time_minutes: float
    reason: str


class ModelSelector:
    def __init__(self):
        self.selection_history: List[ModelSelection] = []

    def select(
        self,
        dataset_size: int,
        domain: str,
        task_complexity: float = 0.5,
        require_interpretability: bool = False,
        time_budget_minutes: float = float("inf"),
    ) -> ModelSelection:
        reason = ""
        interpretability = InterpretabilityLevel.MEDIUM

        if dataset_size < 100:
            model_type = ModelComplexity.BOOST_FIXED
            estimated_time = 1.0
            interpretability = InterpretabilityLevel.HIGH
            reason = f"Small dataset ({dataset_size} examples): using simple fixed-weight ensemble to avoid overfitting"
        elif dataset_size < 1000:
            model_type = ModelComplexity.BOOST_TRAINED
            estimated_time = 5.0
            interpretability = InterpretabilityLevel.HIGH
            reason = f"Moderate dataset ({dataset_size} examples): trained ensemble offers best accuracy-complexity tradeoff"
        elif dataset_size < 10000:
            if require_interpretability:
                model_type = ModelComplexity.BOOST_TRAINED
                interpretability = InterpretabilityLevel.HIGH
                estimated_time = 15.0
                reason = f"Large dataset ({dataset_size} examples) with interpretability requirement: using trained ensemble"
            else:
                model_type = ModelComplexity.TRANSFORMER
                interpretability = InterpretabilityLevel.MEDIUM
                estimated_time = 30.0
                reason = f"Large dataset ({dataset_size} examples): transformer core provides best accuracy"
        else:
            if task_complexity > 0.7:
                model_type = ModelComplexity.TRANSFORMER_RL
                interpretability = InterpretabilityLevel.LOW
                estimated_time = 120.0
                reason = f"Very large dataset ({dataset_size} examples) with complex task: full transformer + RL pipeline"
            else:
                model_type = ModelComplexity.TRANSFORMER
                interpretability = InterpretabilityLevel.MEDIUM
                estimated_time = 60.0
                reason = f"Very large dataset ({dataset_size} examples): transformer core for maximum accuracy"

        if estimated_time > time_budget_minutes:
            simpler_type = self._fallback_simpler(model_type)
            simpler_time = estimated_time * 0.3
            reason += f" (time budget {time_budget_minutes}m < estimated {estimated_time:.0f}m — falling back to {simpler_type.value})"
            model_type = simpler_type
            estimated_time = simpler_time

        selection = ModelSelection(
            model_type=model_type,
            interpretability=interpretability,
            dataset_size=dataset_size,
            domain=domain,
            estimated_time_minutes=estimated_time,
            reason=reason or f"Default selection for {domain} with {dataset_size} examples",
        )
        self.selection_history.append(selection)
        return selection

    def _fallback_simpler(self, model_type: ModelComplexity) -> ModelComplexity:
        fallback_map = {
            ModelComplexity.FULL_PIPELINE: ModelComplexity.TRANSFORMER_RL,
            ModelComplexity.TRANSFORMER_RL: ModelComplexity.TRANSFORMER,
            ModelComplexity.TRANSFORMER: ModelComplexity.BOOST_TRAINED,
            ModelComplexity.BOOST_TRAINED: ModelComplexity.BOOST_FIXED,
            ModelComplexity.BOOST_FIXED: ModelComplexity.BOOST_FIXED,
        }
        return fallback_map.get(model_type, ModelComplexity.BOOST_FIXED)

    def get_selection_history(self, n: int = 10) -> List[ModelSelection]:
        return self.selection_history[-n:]
