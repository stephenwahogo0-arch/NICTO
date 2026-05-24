from nikto.variants.base import AgentVariant, create_variant, HEAVYWEIGHT_CONFIG, SONNET_CONFIG, MYTHOS_CONFIG
from nikto.variants.heavyweight import NiktoHeavyweight
from nikto.variants.sonnet import NiktoSonnet
from nikto.variants.mythos import NiktoMythos

__all__ = [
    "AgentVariant", "create_variant",
    "HEAVYWEIGHT_CONFIG", "SONNET_CONFIG", "MYTHOS_CONFIG",
    "NiktoHeavyweight", "NiktoSonnet", "NiktoMythos",
]
