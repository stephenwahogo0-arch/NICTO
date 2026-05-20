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
from nikto.autopilot.engine import AutopilotEngine, AutopilotConfig, AutopilotStatus
from nikto.autopilot.finance import FinanceManager, PaymentMethod
from nikto.autopilot.connections import ConnectionManager, Connection, ConnectionType
from nikto.tools.autopilot_control import _set_autopilot
from nikto.devices.engine import DeviceController, DeviceType, DeviceDiscovery
from nikto.game_engine.engine import GameEngine, GameProject, GameGenre
from nikto.evolution.engine import EvolutionEngine, EvolutionConfig, SelfHealer, SelfOptimizer, BenchmarkSuite
from nikto.dream.engine import DreamEngine, DreamConfig, DreamInsight
from nikto.mesh.engine import MeshEngine, MeshConfig, MeshNode, NodeStatus
from nikto.knowledge.engine import KnowledgeEngine
from nikto.capabilities.scanner import CapabilityScanner
from nikto.capabilities.manifest import CapabilityManifest, FeatureCapability
from nikto.training.engine import TrainingEngine
from nikto.business.engine import BusinessEngine, BusinessUnit, BusinessType, BusinessStatus
from nikto.sandbox.engine import SandboxEngine, SandboxType, SandboxInstance
from nikto.thinking.engine import ThinkingEngine, Insight, ThoughtChain
from nikto.mobile.engine import MobileCommEngine, MessageChannel
from nikto.deploy.engine import DeployEngine, DeploymentTarget
from nikto.surpass.engine import SurpassEngine
from nikto.arsenal.engine import ArsenalEngine, KaliTool
from nikto.quantum.engine import QuantumEngine
from nikto.neuro.engine import NeuroEngine
from nikto.api_gateway.engine import APIGateway, APIKey
from nikto.super.engine import SuperEngine
from nikto.autonomous.engine import AutonomousEngine
from nikto.synthetic.engine import SyntheticEngine
from nikto.consciousness.expansions.engine import ConsciousnessExpansion
from nikto.reasoning.engine import ReasoningEngine
from nikto.brain.engine import BrainEngine
from nikto.brain.multi import HyperBrain, SpecializedBrain, BRAIN_SPECS
from nikto.brain.training import BrainTrainer
from nikto.brain.optimize import BrainOptimizer
from nikto.resilience.engine import ResilienceEngine
from nikto.diagnostics.engine import DiagnosticsEngine
from nikto.self_repair.engine import CodeHealer
from nikto.code_gen.engine import CodeGenerator
from nikto.improve.engine import ContinuousImprovement, ImprovementCycle
from nikto.avatar.engine import AvatarEngine
from nikto.avatar.renderer import AvatarRenderer
from nikto.avatar.desktop import DesktopController as AvatarDesktopController
from nikto.avatar.webcam import WebcamEngine as AvatarWebcamEngine
from nikto.avatar.animations import AnimationType, Expression
from nikto.avatar.sprites import create_avatar_frame, AVAILABLE_POSES, AVAILABLE_EXPRESSIONS
from nikto.avatar.personalize import PersonalAvatarGenerator, ColorPalette

# Eagle Eye — Truth Verification & Preemptive Issue Detection
from nikto.eagle_eye import (
    EagleEye, LieDetector, PreemptiveIssueScanner,
    AnomalyDetector, create_eagle_eye,
)

# Sourcing Engine — Citation Tracking & Truth Verification
from nikto.sourcing.engine import SourcingEngine, Citation, SourcedClaim

# Voice Engine — Text-to-Speech with Multiple Backends
from nikto.voice.engine import VoiceEngine, VoiceProfile

# Evolution Protocol — Autonomous Self-Improvement
from nikto.evolution.protocol import EvolutionProtocol
from nikto.evolution.masterclass import MasterclassTrainer

# Infinite Context — Million-Word Processing
from nikto.infinite_context import InfiniteContextEngine

# Hotkeys — Global Keyboard Shortcuts
from nikto.avatar.hotkeys import HotkeyManager

# Registration, Privacy & Safety
from nikto.registration import UserRegistry, RegistrationData, RegistrationFlow
from nikto.privacy import get_privacy_policy, get_policy_summary
from nikto.safety import (
    SafetySystem, ActivityAuditLog, EmergencySystem, AbuseReporter,
    PoliceCooperationMode, SafetyLock, ContentSafetyMonitor,
    LogEntry, create_safety_system,
)

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
    "AutopilotEngine", "AutopilotConfig", "AutopilotStatus",
    "FinanceManager", "PaymentMethod",
    "ConnectionManager", "Connection", "ConnectionType",
    "_set_autopilot",
    "DeviceController", "DeviceType", "DeviceDiscovery",
    "GameEngine", "GameProject", "GameGenre",
    "EvolutionEngine", "EvolutionConfig", "SelfHealer", "SelfOptimizer", "BenchmarkSuite",
    "DreamEngine", "DreamConfig", "DreamInsight",
    "MeshEngine", "MeshConfig", "MeshNode", "NodeStatus",
    "KnowledgeEngine",
    "CapabilityScanner",
    "CapabilityManifest", "FeatureCapability",
    "TrainingEngine",
    "BusinessEngine", "BusinessUnit", "BusinessType", "BusinessStatus",
    "SandboxEngine", "SandboxType", "SandboxInstance",
    "ThinkingEngine", "Insight", "ThoughtChain",
    "MobileCommEngine", "MessageChannel",
    "DeployEngine", "DeploymentTarget",
    "SurpassEngine",
    "ArsenalEngine", "KaliTool",
    "QuantumEngine",
    "NeuroEngine",
    "APIGateway", "APIKey",
    "SuperEngine",
    "AutonomousEngine",
    "SyntheticEngine",
    "ConsciousnessExpansion",
    "ReasoningEngine",
    "BrainEngine",
    "HyperBrain", "SpecializedBrain", "BRAIN_SPECS",
    "BrainTrainer",
    "BrainOptimizer",
    "ResilienceEngine",
    "DiagnosticsEngine",
    "CodeHealer",
    "CodeGenerator",
    "ContinuousImprovement",
    "ImprovementCycle",
    "AvatarEngine",
    "AvatarRenderer",
    "AvatarDesktopController",
    "AvatarWebcamEngine",
    "AnimationType",
    "Expression",
    "create_avatar_frame",
    "AVAILABLE_POSES",
    "AVAILABLE_EXPRESSIONS",
    "PersonalAvatarGenerator", "ColorPalette",
    "EagleEye", "LieDetector", "PreemptiveIssueScanner",
    "AnomalyDetector", "create_eagle_eye",
    "SourcingEngine", "Citation", "SourcedClaim",
    "VoiceEngine", "VoiceProfile",
    "EvolutionProtocol",
    "MasterclassTrainer",
    "InfiniteContextEngine",
    "HotkeyManager",
    "UserRegistry", "RegistrationData", "RegistrationFlow",
    "get_privacy_policy", "get_policy_summary",
    "SafetySystem", "ActivityAuditLog", "EmergencySystem",
    "AbuseReporter", "PoliceCooperationMode", "SafetyLock",
    "ContentSafetyMonitor", "LogEntry", "create_safety_system",
]
