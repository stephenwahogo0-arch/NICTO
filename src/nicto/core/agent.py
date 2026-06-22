"""NICTO Agent — primary runtime entry point."""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from ..brains.router import DynamicBrainRouter, TaskType, BrainResponse
from ..brains.ethical import EthicalBrain
from ..brains.meta import MetaCognitionBrain


@dataclass
class AgentConfig:
    brains: list[str] = field(default_factory=lambda: ["primary", "ethical"])
    policy_level: str = "strict"
    sandbox: bool = True
    log_level: str = "INFO"
    hardware_profile: dict = field(default_factory=dict)


class Agent:
    """Primary NICTO agent — routes tasks through the HyperBrain ensemble."""

    def __init__(self, brains: Optional[list[str]] = None,
                  policy_level: str = "strict",
                  sandbox: bool = True,
                  log_level: str = "DEBUG"):
        self.router = DynamicBrainRouter()
        # Convert the router's hardware_profile to the dict format expected by AgentConfig
        hw_dict = {
            "gpu": self.router.hardware_profile.gpu_available,
            "vram_gb": self.router.hardware_profile.gpu_memory_gb,
            "npu": False,   # We don't have NPU detection yet
            "ram_gb": self.router.hardware_profile.ram_total_gb
        }
        self.config = AgentConfig(
            brains=brains or ["primary", "ethical"],
            policy_level=policy_level,
            sandbox=sandbox,
            log_level=log_level,
            hardware_profile=hw_dict
        )
        self.ethical = EthicalBrain(policy_pack="default")
        self.meta = MetaCognitionBrain()
        self._interaction_count = 0

    def _detect_hardware(self) -> dict:
        hw = {"gpu": False, "vram_gb": 0, "npu": False, "ram_gb": 0}
        try:
            import psutil
            hw["ram_gb"] = round(psutil.virtual_memory().total / 1e9, 1)
        except Exception:
            pass
        try:
            import torch
            hw["gpu"] = torch.cuda.is_available()
            if hw["gpu"]:
                hw["vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)
        except Exception:
            pass
        return hw

    def process(self, query: str, domain: str = "general",
                metadata: Optional[dict] = None) -> BrainResponse:
        self._interaction_count += 1
        ctx = {"domain": domain, "interaction": self._interaction_count,
               **(metadata or {})}

        ethical = self.ethical.audit(query)
        if not ethical.approved:
            return BrainResponse(
                content=ethical.reason or "Request blocked by ethical policy.",
                confidence=1.0, blocked=True,
                reason=ethical.reason
            )

        result = self.router.route(query)
        self.meta.log_execution(None, result, result.confidence)
        return result

    def get_status(self) -> dict:
        return {
            "version": "2.1.0",
            "interactions": self._interaction_count,
            "hardware": self._detect_hardware(),
            "brains": list(self.router.brains.keys()) if hasattr(self.router, 'brains') else [],
        }
