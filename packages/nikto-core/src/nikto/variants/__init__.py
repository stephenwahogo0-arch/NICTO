"""NIKTO Agent Variants — Three distinct AI personalities with specialized capabilities."""
from nikto.variants.base import (
    VariantType, VariantConfig, AgentVariant,
    HEAVYWEIGHT_CONFIG, SONNET_CONFIG, MYTHOS_CONFIG,
)
from nikto.variants.heavyweight import NiktoHeavyweight
from nikto.variants.sonnet import NiktoSonnet
from nikto.variants.mythos import NiktoMythos

__all__ = [
    "VariantType", "VariantConfig", "AgentVariant",
    "HEAVYWEIGHT_CONFIG", "SONNET_CONFIG", "MYTHOS_CONFIG",
    "NiktoHeavyweight", "NiktoSonnet", "NiktoMythos",
]
