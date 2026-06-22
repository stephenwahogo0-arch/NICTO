"""Dynamic brain routing system."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .base import Brain, BrainConfig, BrainResponse, HardwareProfile


class TaskType(Enum):
    """Types of tasks for routing."""
    PRIMARY = "primary"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    STRATEGIC = "strategic"
    KNOWLEDGE = "knowledge"
    INTUITIVE = "intuitive"
    GENERAL = "general"


@dataclass
class TaskCategory:
    """Category of task for routing."""
    name: str
    patterns: List[str]
    confidence_boost: float = 0.0


class TaskClassifier:
    """Classifies tasks into categories using regex patterns."""

    def __init__(self):
        # Define task categories with associated patterns
        self.categories = [
            TaskCategory(
                name="PRIMARY",
                patterns=[
                    r"what is", r"who is", r"where is", r"when is", r"how to",
                    r"explain", r"describe", r"tell me about", r"definition",
                    r"meaning of", r"difference between"
                ],
                confidence_boost=0.1
            ),
            TaskCategory(
                name="ANALYTICAL",
                patterns=[
                    r"analyze", r"compare", r"evaluate", r"assess", r"pros and cons",
                    r"advantages and disadvantages", r"breakdown", r"statistics",
                    r"data", r"trend", r"pattern", r"correlation"
                ],
                confidence_boost=0.15
            ),
            TaskCategory(
                name="CREATIVE",
                patterns=[
                    r"write", r"create", r"generate", r"compose", r"design",
                    r"poem", r"song", r"joke", r"brainstorm",
                    r"ideas for", r"invent", r"imagine", r"creative", r"artistic"
                ],
                confidence_boost=0.2
            ),
            TaskCategory(
                name="STRATEGIC",
                patterns=[
                    r"plan", r"strategy", r"roadmap", r"steps to", r"how to achieve",
                    r"goal", r"objective", r"optimize", r"improve", r"best approach",
                    r"recommend", r"suggest", r"decide to", r"choose to", r"decide on", r"choose between", r"decide between", r"choose option"
                ],
                confidence_boost=0.15
            ),
            TaskCategory(
                name="KNOWLEDGE",
                patterns=[
                    r"recall", r"remember", r"what did", r"history of", r"origin of",
                    r"timeline", r"chronology", r"biography", r"timeline of",
                    r"when did", r"where did", r"what was", r"who was"
                ],
                confidence_boost=0.1
            ),
            TaskCategory(
                name="INTUITIVE",
                patterns=[
                    r"feel", r"intuition", r"gut feeling", r"hunch", r"instinct",
                    r"sense", r"vibe", r"impression", r"seems like", r"appears"
                ],
                confidence_boost=0.05
            ),
            TaskCategory(
                name="GENERAL",
                patterns=[],  # Catch-all
                confidence_boost=0.0
            )
        ]

        # Compile regex patterns for efficiency
        self._compiled_patterns = []
        for category in self.categories:
            compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in category.patterns]
            self._compiled_patterns.append((category, compiled_patterns))

    def classify(self, task: str) -> Tuple[str, float]:
        """
        Classify a task into a category with confidence score.
        Returns (category_name, confidence_score)
        """
        if not task or not task.strip():
            return "GENERAL", 0.0

        task_lower = task.lower().strip()
        scores = {}

        # Initialize scores for all categories
        for category in self.categories:
            scores[category.name] = 0.0

        # Check each pattern
        for category, patterns in self._compiled_patterns:
            matches = sum(1 for pattern in patterns if pattern.search(task_lower))
            if matches > 0:
                # Score based on number of matches and category confidence boost
                scores[category.name] = min(1.0, matches * 0.3 + category.confidence_boost)

        # If no patterns matched, default to GENERAL
        if all(score == 0.0 for score in scores.values()):
            return "GENERAL", 0.5  # Neutral confidence for general

        # Find category with highest score
        best_category = max(scores, key=scores.get)
        confidence = scores[best_category]

        # Ensure confidence is in valid range
        confidence = max(0.0, min(1.0, confidence))

        return best_category, confidence


class DynamicBrainRouter:
    """Routes tasks to appropriate brains with hardware awareness and fallbacks."""

    def __init__(self):
        self.hardware_profile = HardwareProfile.detect()
        self.classifier = TaskClassifier()
        self._brain_cache: Dict[str, Brain] = {}
        self._brain_configs: Dict[str, BrainConfig] = {}
        self._performance_history: Dict[str, List[float]] = {}  # track latency per brain
        self._initialize_brain_configs()

    def _initialize_brain_configs(self):
        """Initialize brain configurations with hardware-aware settings."""
        # Base configurations for each brain type
        base_configs = {
            "PRIMARY": BrainConfig(model_name="primary-reasoner", model_size_gb=2.0, quantization_bits=32),
            "ANALYTICAL": BrainConfig(model_name="analytical-processor", model_size_gb=1.5, quantization_bits=32),
            "CREATIVE": BrainConfig(model_name="creative-generator", model_size_gb=1.8, quantization_bits=32),
            "STRATEGIC": BrainConfig(model_name="strategic-planner", model_size_gb=1.5, quantization_bits=32),
            "KNOWLEDGE": BrainConfig(model_name="knowledge-retriever", model_size_gb=1.0, quantization_bits=32),
            "INTUITIVE": BrainConfig(model_name="intuitive-responder", model_size_gb=0.8, quantization_bits=32),
            "ETHICAL": BrainConfig(model_name="ethical-guardian", model_size_gb=0.5, quantization_bits=32),  # Small, fast
            "META": BrainConfig(model_name="meta-cognitor", model_size_gb=0.7, quantization_bits=32),  # Small, fast
        }

        # Adjust configurations based on hardware
        for brain_name, config in base_configs.items():
            adjusted_config = self._adjust_config_for_hardware(config, brain_name)
            self._brain_configs[brain_name] = adjusted_config

    def _adjust_config_for_hardware(self, config: BrainConfig, brain_name: str) -> BrainConfig:
        """Adjust brain configuration based on available hardware."""
        # If GPU is available, we can use higher precision or larger models
        if self.hardware_profile.gpu_available:
            # Prefer lower quantization (higher precision) when GPU is available
            if config.quantization_bits == 32 and self.hardware_profile.gpu_memory_gb >= 4.0:
                config.quantization_bits = 16  # Use FP16 if we have decent GPU memory
            elif config.quantization_bits == 16 and self.hardware_profile.gpu_memory_gb >= 8.0:
                config.quantization_bits = 32  # Could even use FP32 with lots of VRAM
        else:
            # CPU-only: prefer more aggressive quantization to fit in RAM
            if config.quantization_bits == 32:
                config.quantization_bits = 16  # Try 16-bit first
                # Check if even 16-bit is too big, fallback to 8-bit
                estimated_size_gb = config.model_size_gb * (16 / 32.0)
                if estimated_size_gb > self.hardware_profile.ram_total_gb * 0.5:
                    config.quantization_bits = 8  # Fallback to 8-bit

        # Ensure we don't go below 8-bit
        if config.quantization_bits < 8:
            config.quantization_bits = 8

        return config

    def _get_brain_instance(self, brain_name: str) -> Optional[Brain]:
        """Get or create a brain instance, with lazy loading."""
        if brain_name in self._brain_cache:
            return self._brain_cache[brain_name]

        if brain_name not in self._brain_configs:
            # Unknown brain type
            return None

        # Import brain classes dynamically to avoid circular imports
        brain_class = self._get_brain_class(brain_name)
        if brain_class is None:
            return None

        config = self._brain_configs[brain_name]
        try:
            brain_instance = brain_class(config)
            self._brain_cache[brain_name] = brain_instance
            # Initialize performance tracking
            if brain_name not in self._performance_history:
                self._performance_history[brain_name] = []
            return brain_instance
        except Exception as e:
            # Failed to create brain instance
            print(f"Warning: Failed to load brain {brain_name}: {e}", file=sys.stderr)
            return None

    def _get_brain_class(self, brain_name: str) -> Optional[type]:
        """Get the brain class for a given name."""
        # Map brain names to their modules
        brain_module_map = {
            "PRIMARY": ".primary",
            "ANALYTICAL": ".analytical",
            "CREATIVE": ".creative",
            "STRATEGIC": ".strategic",
            "KNOWLEDGE": ".knowledge",
            "INTUITIVE": ".intuitive",
            "ETHICAL": ".ethical",
            "META": ".meta",
        }

        if brain_name not in brain_module_map:
            return None

        try:
            module_name = brain_module_map[brain_name]
            # Use relative import
            module = __import__(f"src.nicto.brains{module_name}", fromlist=[brain_name])
            class_name = {
                "PRIMARY": "PrimaryBrain",
                "ANALYTICAL": "AnalyticalBrain",
                "CREATIVE": "CreativeBrain",
                "STRATEGIC": "StrategicBrain",
                "KNOWLEDGE": "KnowledgeBrain",
                "INTUITIVE": "IntuitiveBrain",
                "ETHICAL": "EthicalBrain",
                "META": "MetaCognitionBrain",
            }[brain_name]
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not import brain {brain_name}: {e}", file=sys.stderr)
            return None

    def _build_fallback_chain(self, primary_brain: str) -> List[str]:
        """Build a fallback chain for a given primary brain."""
        # Define fallback preferences
        fallback_map = {
            "PRIMARY": ["ANALYTICAL", "KNOWLEDGE", "INTUITIVE"],
            "ANALYTICAL": ["PRIMARY", "KNOWLEDGE", "STRATEGIC"],
            "CREATIVE": ["PRIMARY", "INTUITIVE", "ANALYTICAL"],
            "STRATEGIC": ["PRIMARY", "ANALYTICAL", "KNOWLEDGE"],
            "KNOWLEDGE": ["PRIMARY", "ANALYTICAL", "INTUITIVE"],
            "INTUITIVE": ["PRIMARY", "CREATIVE", "KNOWLEDGE"],
            "ETHICAL": [],  # Ethical brain should not have fallbacks for its core function
            "META": [],     # Meta brain should not have fallbacks for its core function
        }

        # Always put ethical and meta brains at the end for safety/logging
        fallback_chain = fallback_map.get(primary_brain, ["PRIMARY"])
        # Remove duplicates and ensure we don't fall back to ourselves
        seen = set()
        filtered_chain = []
        for brain in fallback_chain:
            if brain not in seen and brain != primary_brain:
                seen.add(brain)
                filtered_chain.append(brain)

        return filtered_chain

    def route(self, task: str) -> BrainResponse:
        """
        Route a task through the full pipeline:
        Ethical Pre-check -> Task Classification -> Brain Selection -> Execution -> Fallback Chain -> Meta Logging
        """
        import time
        start_time = time.perf_counter()

        # Step 1: Ethical pre-check (handled by EthicalBrain in actual implementation)
        # For now, we'll simulate this by checking if we have an ethical brain
        ethical_brain = self._get_brain_instance("ETHICAL")
        ethical_approved = True
        ethical_reason = None
        if ethical_brain:
            # In a real implementation, we would call ethical_brain.process() and check the result
            # For Phase 1 stub, we'll assume it's approved
            pass

        # Step 2: Classify the task
        task_category, classification_confidence = self.classifier.classify(task)

        # Step 3: Select the primary brain
        primary_brain = self._get_brain_instance(task_category)
        fallback_chain = self._build_fallback_chain(task_category)

        # Step 4: Attempt execution with fallback chain
        brains_to_try = [task_category] + fallback_chain
        last_response = None

        for brain_name in brains_to_try:
            brain_instance = self._get_brain_instance(brain_name)
            if brain_instance is None:
                continue

            try:
                response = brain_instance.process(task)
                # Track performance
                if brain_name not in self._performance_history:
                    self._performance_history[brain_name] = []
                self._performance_history[brain_name].append(response.latency_ms)

                # If successful (high enough confidence), return it
                if response.confidence >= 0.5:  # Configurable threshold
                    # Add routing metadata
                    response.metadata.update({
                        "routed_brain": brain_name,
                        "task_category": task_category,
                        "classification_confidence": classification_confidence,
                        "fallback_used": brain_name != task_category,
                        "ethical_approved": ethical_approved,
                        "ethical_reason": ethical_reason,
                    })
                    return response
                else:
                    # Low confidence, but we'll keep it as fallback if nothing better
                    last_response = response
            except Exception as e:
                # Brain execution failed, try next in chain
                print(f"Warning: Brain {brain_name} failed: {e}", file=sys.stderr)
                continue

        # If we got here, either all brains failed or returned low confidence
        # Return the last response we got, or an error
        if last_response is not None:
            last_response.metadata.update({
                "routed_brain": "fallback_low_confidence",
                "task_category": task_category,
                "classification_confidence": classification_confidence,
                "fallback_used": True,
                "ethical_approved": ethical_approved,
                "ethical_reason": ethical_reason,
            })
            return last_response

        # All brains failed to load or execute
        latency_ms = (time.perf_counter() - start_time) * 1000
        return BrainResponse(
            content="Error: All brains failed to process the task.",
            confidence=0.0,
            latency_ms=latency_ms,
            fallback_chain=brains_to_try,
            metadata={
                "error": "all_brains_failed",
                "task_category": task_category,
                "classification_confidence": classification_confidence,
                "ethical_approved": ethical_approved,
                "ethical_reason": ethical_reason,
            },
        )

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the router and brains."""
        status = {
            "hardware_profile": {
                "gpu_available": self.hardware_profile.gpu_available,
                "gpu_name": self.hardware_profile.gpu_name,
                "gpu_memory_gb": self.hardware_profile.gpu_memory_gb,
                "cpu_count": self.hardware_profile.cpu_count,
                "ram_total_gb": self.hardware_profile.ram_total_gb,
                "platform": self.hardware_profile.platform,
            },
            "loaded_brains": list(self._brain_cache.keys()),
            "brain_configs": {
                name: {
                    "model_name": config.model_name,
                    "model_size_gb": config.model_size_gb,
                    "quantization_bits": config.quantization_bits,
                }
                for name, config in self._brain_configs.items()
            },
            "performance_history": {
                brain_name: {
                    "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
                    "min_latency_ms": min(latencies) if latencies else 0.0,
                    "max_latency_ms": max(latencies) if latencies else 0.0,
                    "sample_count": len(latencies),
                }
                for brain_name, latencies in self._performance_history.items()
            },
        }
        return status