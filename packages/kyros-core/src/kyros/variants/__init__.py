from kyros.variants.base import AgentVariant, create_variant, HEAVYWEIGHT_CONFIG, SONNET_CONFIG, MYTHOS_CONFIG
from kyros.variants.heavyweight import KyrosHeavyweight
from kyros.variants.sonnet import KyrosSonnet
from kyros.variants.mythos import KyrosMythos

__all__ = [
    "AgentVariant", "create_variant",
    "HEAVYWEIGHT_CONFIG", "SONNET_CONFIG", "MYTHOS_CONFIG",
    "KyrosHeavyweight", "KyrosSonnet", "KyrosMythos",
]
