"""
NICTO v2.1 — Production-grade AI agent system with HyperBrain ensemble.

Usage:
    from nicto import Agent
    agent = Agent(brains=["primary", "ethical"])
    result = agent.process("What is the capital of France?")
"""

__version__ = "2.1.0"
__codename__ = "ULTIMATE_MASTER"

from .core.agent import Agent
from .core.event_loop import EventLoop
from .brains.router import DynamicBrainRouter, TaskType, BrainConfig, BrainResponse
from .brains.ethical import EthicalBrain, EthicalAuditResult, PolicyRule
from .brains.meta import MetaCognitionBrain
from .security.policy_engine import ASL3PolicyEngine, PolicyEnforcementResult, EnforcementLevel
from .perception.wifi.csi_capture import CrossPlatformCSI, GestureRecognizer
from .avatar.godot_bridge import Avatar
from .cli.main import main as cli_main

__all__ = [
    "Agent",
    "EventLoop",
    "DynamicBrainRouter",
    "TaskType",
    "BrainConfig",
    "BrainResponse",
    "EthicalBrain",
    "EthicalAuditResult",
    "PolicyRule",
    "MetaCognitionBrain",
    "ASL3PolicyEngine",
    "PolicyEnforcementResult",
    "EnforcementLevel",
    "CrossPlatformCSI",
    "GestureRecognizer",
    "Avatar",
    "cli_main",
]
