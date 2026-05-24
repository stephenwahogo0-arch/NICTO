from nikto.config.settings import ModelConfig

HEAVYWEIGHT_CONFIG = ModelConfig(provider="anthropic", model="claude-sonnet-4-20250514", temperature=0.3, max_tokens=8192)
SONNET_CONFIG = ModelConfig(provider="anthropic", model="claude-sonnet-4-20250514", temperature=0.5, max_tokens=4096)
MYTHOS_CONFIG = ModelConfig(provider="anthropic", model="claude-sonnet-4-20250514", temperature=0.2, max_tokens=8192)


class AgentVariant:
    def __init__(self, name: str, config: ModelConfig):
        self.name = name
        self.config = config
        self.id = None

    def build_system_prompt(self, base_prompt: str = "") -> str:
        return base_prompt


def create_variant(variant_name: str, config: ModelConfig = None) -> AgentVariant:
    if variant_name == "nikto-heavyweight":
        return AgentVariant("nikto-heavyweight", config or HEAVYWEIGHT_CONFIG)
    elif variant_name == "nikto-sonnet":
        return AgentVariant("nikto-sonnet", config or SONNET_CONFIG)
    elif variant_name == "nikto-mythos":
        return AgentVariant("nikto-mythos", config or MYTHOS_CONFIG)
    return AgentVariant(variant_name, config or ModelConfig())
