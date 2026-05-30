"""Brain base classes and hardware profiling."""
from __future__ import annotations

import platform
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from pydantic import BaseModel, Field, validator


@dataclass
class HardwareProfile:
    """Current hardware capabilities for model loading decisions."""
    gpu_available: bool
    gpu_name: Optional[str]
    gpu_memory_gb: float
    cpu_count: int
    ram_total_gb: float
    platform: str  # win32, linux, darwin
    python_version: str

    @classmethod
    def detect(cls) -> "HardwareProfile":
        """Detect current hardware capabilities."""
        # GPU detection
        gpu_available = False
        gpu_name = None
        gpu_memory_gb = 0.0
        if HAS_TORCH:
            gpu_available = torch.cuda.is_available()
            if gpu_available:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / 1e9

        # CPU and RAM
        if HAS_PSUTIL:
            cpu_count = psutil.cpu_count(logical=True)
            ram_total_gb = psutil.virtual_memory().total / 1e9
        else:
            # Fallback
            cpu_count = 1
            ram_total_gb = 4.0  # conservative estimate

        return cls(
            gpu_available=gpu_available,
            gpu_name=gpu_name,
            gpu_memory_gb=gpu_memory_gb,
            cpu_count=cpu_count,
            ram_total_gb=ram_total_gb,
            platform=sys.platform,
            python_version=sys.version,
        )

    def can_run_model(self, model_size_gb: float, quantization_bits: int = 32) -> bool:
        """
        Check if we can load a model of given size with specified quantization.
        Quantization reduces memory usage: size_gb * (quantization_bits / 32)
        """
        effective_size_gb = model_size_gb * (quantization_bits / 32.0)
        # Need to leave room for overhead, framework, etc.
        available_ram = self.ram_total_gb * 0.7  # use 70% of RAM for model
        if self.gpu_available:
            # For GPU, we can use VRAM + system RAM (if using CPU offload)
            available_memory = self.gpu_memory_gb + available_ram
        else:
            available_memory = available_ram
        return effective_size_gb <= available_memory


class BrainConfig(BaseModel):
    """Configuration for a brain instance."""
    model_name: str = Field(default="unknown")
    model_size_gb: float = Field(default=1.0, gt=0)
    quantization_bits: int = Field(default=32, ge=8, le=64)
    max_latency_ms: float = Field(default=5000.0, gt=0)
    timeout_seconds: float = Field(default=30.0, gt=0)
    device_preference: str = Field(default="auto")  # auto, cuda, cpu

    @validator('quantization_bits')
    def validate_quantization_bits(cls, v):
        """Ensure quantization bits are standard values."""
        if v not in [8, 16, 32, 64]:
            raise ValueError('quantization_bits must be 8, 16, 32, or 64')
        return v

    @validator('device_preference')
    def validate_device_preference(cls, v):
        if v not in ['auto', 'cuda', 'cpu']:
            raise ValueError("device_preference must be 'auto', 'cuda', or 'cpu'")
        return v


class BrainResponse(BaseModel):
    """Immutable response from a brain."""
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    latency_ms: float
    fallback_chain: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True


class Brain(ABC):
    """Abstract base class for all NICTO brains."""

    def __init__(self, config: BrainConfig):
        self.config = config
        self.hardware_profile = HardwareProfile.detect()
        self._model = None
        self._is_loaded = False
        self._load_attempted = False

    @abstractmethod
    def _load_model(self) -> Any:
        """Load the brain's model. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def _process_internal(self, prompt: str, **kwargs) -> str:
        """Internal processing logic. Must be implemented by subclasses."""
        pass

    def _ensure_model_loaded(self) -> bool:
        """Ensure model is loaded, attempting to load if not already."""
        if self._is_loaded:
            return True
        if self._load_attempted:
            return False  # Already tried and failed

        self._load_attempted = True
        try:
            self._model = self._load_model()
            self._is_loaded = True
            return True
        except Exception as e:
            # In a real implementation, we might log this
            self._model = None
            self._is_loaded = False
            return False

    def process(self, prompt: str, **kwargs) -> BrainResponse:
        """Process a prompt with timing, error handling, and metrics."""
        import time
        start_time = time.perf_counter()

        # Ensure model is loaded
        if not self._ensure_model_loaded():
            latency_ms = (time.perf_counter() - start_time) * 1000
            return BrainResponse(
                content="Error: Brain model failed to load.",
                confidence=0.0,
                latency_ms=latency_ms,
                fallback_chain=["model_load_failed"],
                metadata={"error": "model_load_failed"},
            )

        # Process with timeout
        try:
            # In a full implementation, we would use asyncio or threading for timeout
            # For now, we'll just call and hope it's fast
            result = self._process_internal(prompt, **kwargs)
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Basic confidence heuristic (to be improved by meta-brain)
            confidence = min(0.95, 0.5 + (len(result) / 1000))  # placeholder

            return BrainResponse(
                content=result,
                confidence=confidence,
                latency_ms=latency_ms,
                fallback_chain=[],
                metadata={"brain_type": self.__class__.__name__},
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return BrainResponse(
                content=f"Error during processing: {str(e)}",
                confidence=0.0,
                latency_ms=latency_ms,
                fallback_chain=["processing_error"],
                metadata={"error": str(e), "brain_type": self.__class__.__name__},
            )

    def get_latency_ms(self) -> float:
        """Get average latency (placeholder)."""
        return 0.0  # Would be tracked in a real implementation

    def get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage (placeholder)."""
        return {"ram_mb": 0.0, "vram_mb": 0.0}

    def get_confidence(self) -> float:
        """Get average confidence (placeholder)."""
        return 0.0