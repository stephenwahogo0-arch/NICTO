"""
Nikto Core — The Ultimate AI Agent Runtime.

A unified, multimodal, multi-agent orchestration platform combining
features from 35+ open-source AI agent systems.
"""

__version__ = "0.1.0"

from nikto.agent.base import Agent, AgentConfig, AgentMode
from nikto.tools.base import Tool, ToolResult, ToolRegistry
from nikto.providers.base import ModelProvider
from nikto.memory.base import MemorySystem
from nikto.skills.base import SkillRuntime
from nikto.config.settings import NiktoConfig
from nikto.orchestrator.engine import Orchestrator, OrchestratorConfig
from nikto.mcp.registry import MCPRegistry, mcp_registry
from nikto.daemon.service import NiktoDaemon, DaemonConfig
from nikto.cua.screen import ScreenController
from nikto.cua.input import InputController
from nikto.earn.wallet import EarnWallet
from nikto.earn.miner import LaptopMiner
from nikto.variants.base import (
    VariantType, VariantConfig, AgentVariant, create_variant,
    HEAVYWEIGHT_CONFIG, SONNET_CONFIG, MYTHOS_CONFIG,
)
from nikto.security.code_protocol import CodeSecurityProtocol
from nikto.security.mcp_sandbox import MCPSecureSandbox
from nikto.security.asl3_boundary import ASL3Boundary
from nikto.security.siem_analyst import SIEMAnalyst

__all__ = [
    "Agent", "AgentConfig", "AgentMode",
    "Tool", "ToolResult", "ToolRegistry",
    "ModelProvider",
    "MemorySystem",
    "SkillRuntime",
    "NiktoConfig",
    "Orchestrator", "OrchestratorConfig",
    "MCPRegistry", "mcp_registry",
    "NiktoDaemon", "DaemonConfig",
    "ScreenController",
    "InputController",
    "EarnWallet",
    "LaptopMiner",
    "VariantType", "VariantConfig", "AgentVariant", "create_variant",
    "HEAVYWEIGHT_CONFIG", "SONNET_CONFIG", "MYTHOS_CONFIG",
    "CodeSecurityProtocol",
    "MCPSecureSandbox",
    "ASL3Boundary",
    "SIEMAnalyst",
]
