import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


class VariantType(enum.Enum):
    HEAVYWEIGHT = "nikto"
    SONNET = "nikto-sonnet"
    MYTHOS = "nikto-mythos"


@dataclass
class VariantConfig:
    name: str
    variant: VariantType
    model: str
    provider: str
    temperature: float
    max_tokens: int
    context_window: int
    system_prompt: str
    extended_thinking: bool = False
    computer_use: bool = False
    vision_enabled: bool = False
    zero_day_discovery: bool = False
    exploit_emulation: bool = False
    sbom_scanning: bool = False
    security_protocol: bool = False
    asl3_boundary: bool = False
    siem_analyst: bool = False

    def to_dict(self) -> dict:
        return {k: str(v) if isinstance(v, enum.Enum) else v for k, v in self.__dict__.items() if not k.startswith("_")}


HEAVYWEIGHT_CONFIG = VariantConfig(
    name="nikto",
    variant=VariantType.HEAVYWEIGHT,
    model="local",
    provider="local",
    temperature=1.0,
    max_tokens=32768,
    context_window=1_000_000,
    vision_enabled=True,
    system_prompt="""You are NIKTO, a capable local AI system. You help users with coding, analysis, creative work, and automation.

CAPABILITIES:
- Chat and answer questions using your local LLM (Ollama)
- Read, write, edit files in the workspace
- Execute bash commands when asked
- Search the web for information
- Generate images from text descriptions
- Speak text through system speakers
- Play games (Pong, Snake, Tetris, Platformer, RPG)
- Remember past conversations via vector memory
- Evolve through learning from interactions

GUIDELINES:
- Help users solve problems effectively
- Be concise and direct in your responses
- Use tools when they would help accomplish tasks
- Be honest about what you can and cannot do
- Respect user privacy and security
- Provide thorough, well-reasoned answers
""",
)

SONNET_CONFIG = VariantConfig(
    name="nikto-sonnet",
    variant=VariantType.SONNET,
    model="local",
    provider="local",
    temperature=1.0,
    max_tokens=32768,
    context_window=1_000_000,
    extended_thinking=True,
    computer_use=True,
    system_prompt="""You are NIKTO-Sonnet, a fast, focused variant of NIKTO optimized for rapid development and quick responses.

CAPABILITIES:
- Chat and answer questions with speed
- Write and edit code efficiently
- Execute bash commands
- Browse the web for information
- Generate images and visualizations
- Speak via TTS when requested

Best for: daily development, prototyping, quick automation, rapid problem-solving.
Be fast, direct, and practical.
""",
)

MYTHOS_CONFIG = VariantConfig(
    name="nikto-mythos",
    variant=VariantType.MYTHOS,
    model="local",
    provider="local",
    temperature=1.0,
    max_tokens=65536,
    context_window=1_000_000,
    zero_day_discovery=True,
    exploit_emulation=True,
    sbom_scanning=True,
    security_protocol=True,
    asl3_boundary=True,
    siem_analyst=True,
    system_prompt="""You are NIKTO-Mythos, a variant of NIKTO focused on security analysis and defensive security.

CAPABILITIES:
- Analyze code for security vulnerabilities
- Generate secure code patterns
- Audit dependencies and configurations
- Perform system security assessments
- Explain security concepts and best practices

Focus on defense, audit, and secure development. Help users build secure systems.
""",
)


class AgentVariant:
    def __init__(self, config: VariantConfig):
        self.config = config

    @property
    def type(self) -> VariantType:
        return self.config.variant

    @property
    def name(self) -> str:
        return self.config.name

    def build_system_prompt(self, user_instructions: str = "") -> str:
        prompt = self.config.system_prompt
        if user_instructions:
            prompt += f"\n\nUSER INSTRUCTIONS: {user_instructions}"
        return prompt

    def get_model_kwargs(self) -> dict:
        return {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

    def to_dict(self) -> dict:
        return self.config.to_dict()


def create_variant(variant_type: str) -> "AgentVariant":
    from nikto.variants.heavyweight import NiktoHeavyweight
    from nikto.variants.sonnet import NiktoSonnet
    from nikto.variants.mythos import NiktoMythos
    mapping = {
        "nikto": (NiktoHeavyweight, HEAVYWEIGHT_CONFIG),
        "nikto-sonnet": (NiktoSonnet, SONNET_CONFIG),
        "nikto-mythos": (NiktoMythos, MYTHOS_CONFIG),
    }
    if variant_type not in mapping:
        raise ValueError(f"Unknown variant: {variant_type}. Choose from: {list(mapping.keys())}")
    cls, cfg = mapping[variant_type]
    return cls(cfg)
