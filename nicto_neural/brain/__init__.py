from .primary import PrimaryBrain
from .analytical import AnalyticalBrain
from .creative import CreativeBrain
from .strategic import StrategicBrain
from .knowledge import KnowledgeBrain
from .intuitive import IntuitiveBrain
from .orchestrator import BrainRouter
from .consciousness import NeuralConsciousness

BRAIN_CLASSES = {
    "primary": PrimaryBrain,
    "analytical": AnalyticalBrain,
    "creative": CreativeBrain,
    "strategic": StrategicBrain,
    "knowledge": KnowledgeBrain,
    "intuitive": IntuitiveBrain,
}

__all__ = [
    "PrimaryBrain",
    "AnalyticalBrain",
    "CreativeBrain",
    "StrategicBrain",
    "KnowledgeBrain",
    "IntuitiveBrain",
    "BrainRouter",
    "NeuralConsciousness",
    "BRAIN_CLASSES",
]
