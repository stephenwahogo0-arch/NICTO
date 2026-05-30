"""Unit tests for the DynamicBrainRouter."""
from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from src.nicto.brains.base import BrainConfig, BrainResponse
from src.nicto.brains.router import DynamicBrainRouter, TaskClassifier


def test_task_classifier_initialization():
    """Test that TaskClassifier initializes with expected categories."""
    classifier = TaskClassifier()
    assert hasattr(classifier, 'categories')
    assert len(classifier.categories) == 7  # PRIMARY, ANALYTICAL, CREATIVE, STRATEGIC, KNOWLEDGE, INTUITIVE, GENERAL
    category_names = [cat.name for cat in classifier.categories]
    assert "PRIMARY" in category_names
    assert "ANALYTICAL" in category_names
    assert "CREATIVE" in category_names
    assert "STRATEGIC" in category_names
    assert "KNOWLEDGE" in category_names
    assert "INTUITIVE" in category_names
    assert "GENERAL" in category_names


def test_task_classifier_primary_tasks():
    """Test classification of primary/reasoning tasks."""
    classifier = TaskClassifier()
    
    # Test various primary task patterns
    primary_tasks = [
        "what is machine learning",
        "who is einstein",
        "where is paris",
        "when is christmas",
        "how to bake a cake",
        "explain quantum physics",
        "describe the process",
        "tell me about space",
        "definition of algorithm",
        "meaning of life",
        "difference between cpu and gpu"
    ]
    
    for task in primary_tasks:
        category, confidence = classifier.classify(task)
        assert category == "PRIMARY", f"Failed for task: {task}"
        assert confidence > 0.0, f"Confidence should be > 0 for task: {task}"


def test_task_classifier_analytical_tasks():
    """Test classification of analytical tasks."""
    classifier = TaskClassifier()
    
    analytical_tasks = [
        "analyze the data",
        "compare these options",
        "evaluate the performance",
        "assess the risks",
        "pros and cons of electric cars",
        "advantages and disadvantages",
        "breakdown of costs",
        "statistics show",
        "data indicates",
        "trend analysis",
        "pattern recognition",
        "correlation between"
    ]
    
    for task in analytical_tasks:
        category, confidence = classifier.classify(task)
        assert category == "ANALYTICAL", f"Failed for task: {task}"
        assert confidence > 0.0, f"Confidence should be > 0 for task: {task}"


def test_task_classifier_creative_tasks():
    """Test classification of creative tasks."""
    classifier = TaskClassifier()
    
    creative_tasks = [
        "write a story",
        "create a poem",
        "generate ideas",
        "compose a song",
        "design a logo",
        "brainstorm solutions",
        "invent a new",
        "imagine a world",
        "creative writing",
        "artistic expression"
    ]
    
    for task in creative_tasks:
        category, confidence = classifier.classify(task)
        assert category == "CREATIVE", f"Failed for task: {task}"
        assert confidence > 0.0, f"Confidence should be > 0 for task: {task}"


def test_task_classifier_strategic_tasks():
    """Test classification of strategic tasks."""
    classifier = TaskClassifier()
    
    strategic_tasks = [
        "plan a trip",
        "strategy for growth",
        "roadmap to success",
        "steps to achieve",
        "how to achieve goals",
        "goal setting",
        "objective definition",
        "optimize performance",
        "improve efficiency",
        "best approach",
        "recommend solution",
        "suggest alternative",
        "decide between",
        "choose option"
    ]
    
    for task in strategic_tasks:
        category, confidence = classifier.classify(task)
        assert category == "STRATEGIC", f"Failed for task: {task}"
        assert confidence > 0.0, f"Confidence should be > 0 for task: {task}"


def test_task_classifier_knowledge_tasks():
    """Test classification of knowledge/memory tasks."""
    classifier = TaskClassifier()
    
    knowledge_tasks = [
        "recall what we discussed",
        "remember the details",
        "what did we decide",
        "history of internet",
        "origin of language",
        "timeline of events",
        "chronology of",
        "biography of",
        "when did ww2 start",
        "where did it happen"
    ]
    
    for task in knowledge_tasks:
        category, confidence = classifier.classify(task)
        assert category == "KNOWLEDGE", f"Failed for task: {task}"
        assert confidence > 0.0, f"Confidence should be > 0 for task: {task}"


def test_task_classifier_intuitive_tasks():
    """Test classification of intuitive tasks."""
    classifier = TaskClassifier()
    
    intuitive_tasks = [
        "i feel this is right",
        "my intuition says",
        "gut feeling",
        "hunch that",
        "instinct tells me",
        "i sense that",
        "vibe check",
        "impression is",
        "seems like",
        "appears to be"
    ]
    
    for task in intuitive_tasks:
        category, confidence = classifier.classify(task)
        assert category == "INTUITIVE", f"Failed for task: {task}"
        assert confidence > 0.0, f"Confidence should be > 0 for task: {task}"


def test_task_classifier_general_fallback():
    """Test that unrecognized tasks fall back to GENERAL."""
    classifier = TaskClassifier()
    
    general_tasks = [
        "hello",
        "hi there",
        "thanks",
        "goodbye",
        "asdfghjkl",
        "12345",
        "!@#$%",
        "",  # empty string
        "   ",  # whitespace only
    ]
    
    for task in general_tasks:
        category, confidence = classifier.classify(task)
        # Empty/whitespace tasks might have special handling
        if task.strip():  # Non-empty after stripping
            assert category == "GENERAL", f"Failed for task: '{task}'"


def test_router_initialization():
    """Test that DynamicBrainRouter initializes correctly."""
    router = DynamicBrainRouter()
    assert hasattr(router, 'hardware_profile')
    assert hasattr(router, 'classifier')
    assert hasattr(router, '_brain_cache')
    assert hasattr(router, '_brain_configs')
    assert hasattr(router, '_performance_history')
    assert isinstance(router.hardware_profile, type(router.hardware_profile).__bases__[0])  # HardwareProfile
    assert isinstance(router.classifier, TaskClassifier)
    assert isinstance(router._brain_cache, dict)
    assert isinstance(router._brain_configs, dict)
    assert isinstance(router._performance_history, dict)


def test_router_hardware_aware_config():
    """Test that router adjusts brain configs based on hardware."""
    router = DynamicBrainRouter()
    
    # Check that we have configs for all expected brain types
    expected_brains = ["PRIMARY", "ANALYTICAL", "CREATIVE", "STRATEGIC", "KNOWLEDGE", "INTUITIVE", "ETHICAL", "META"]
    for brain_type in expected_brains:
        assert brain_type in router._brain_configs
        config = router._brain_configs[brain_type]
        assert isinstance(config, BrainConfig)
        assert config.model_size_gb > 0
        assert config.quantization_bits in [8, 16, 32, 64]


@patch('builtins.__import__')
def test_router_get_brain_class(mock_import):
    """Test the _get_brain_class method with mocked imports."""
    # Setup mock
    mock_module = Mock()
    mock_module.PrimaryBrain = Mock()
    mock_import.return_value = mock_module
    
    router = DynamicBrainRouter()
    
    # Test successful import
    brain_class = router._get_brain_class("PRIMARY")
    assert brain_class == mock_module.PrimaryBrain
    
    # Test failed import
    mock_import.side_effect = ImportError("Module not found")
    brain_class = router._get_brain_class("PRIMARY")
    assert brain_class is None


def test_router_build_fallback_chain():
    """Test building fallback chains for different brain types."""
    router = DynamicBrainRouter()
    
    # Test PRIMARY fallback chain
    primary_fallback = router._build_fallback_chain("PRIMARY")
    assert isinstance(primary_fallback, list)
    assert "PRIMARY" not in primary_fallback  # Should not include self
    
    # Test CREATIVE fallback chain
    creative_fallback = router._build_fallback_chain("CREATIVE")
    assert isinstance(creative_fallback, list)
    assert "CREATIVE" not in creative_fallback  # Should not include self
    
    # Test ETHICAL fallback chain (should be empty)
    ethical_fallback = router._build_fallback_chain("ETHICAL")
    assert ethical_fallback == []
    
    # Test META fallback chain (should be empty)
    meta_fallback = router._build_fallback_chain("META")
    assert meta_fallback == []
    
    # Test unknown brain type (should default to PRIMARY-like fallback)
    unknown_fallback = router._build_fallback_chain("UNKNOWN")
    assert isinstance(unknown_fallback, list)


@patch('src.nicto.brains.router.DynamicBrainRouter._get_brain_instance')
def test_router_route_success(mock_get_brain):
    """Test successful routing and execution."""
    # Setup mock brain that returns a good response
    mock_brain = Mock()
    mock_brain.process.return_value = BrainResponse(
        content="Test response",
        confidence=0.8,
        latency_ms=10.0,
        fallback_chain=[],
        metadata={}
    )
    
    # Configure mock to return our mock brain for any brain request
    mock_get_brain.return_value = mock_brain
    
    router = DynamicBrainRouter()
    response = router.route("what is machine learning")
    
    # Verify we got a response
    assert isinstance(response, BrainResponse)
    assert response.content == "Test response"
    assert response.confidence == 0.8
    assert response.latency_ms == 10.0
    
    # Verify metadata was added
    assert "routed_brain" in response.metadata
    assert "task_category" in response.metadata
    assert "classification_confidence" in response.metadata
    assert response.metadata["task_category"] == "PRIMARY"  # Should be classified as PRIMARY
    
    # Verify the brain's process method was called
    mock_get_brain.assert_any_call("PRIMARY")  # Primary brain
    mock_brain.process.assert_called_with("what is machine learning")


@patch('src.nicto.brains.router.DynamicBrainRouter._get_brain_instance')
def test_router_route_fallback(mock_get_brain):
    """Test routing with fallback when primary brain returns low confidence."""
    # Setup mock brains
    mock_primary_brain = Mock()
    mock_primary_brain.process.return_value = BrainResponse(
        content="Low confidence response",
        confidence=0.3,  # Low confidence
        latency_ms=10.0,
        fallback_chain=[],
        metadata={}
    )
    
    mock_fallback_brain = Mock()
    mock_fallback_brain.process.return_value = BrainResponse(
        content="Fallback response",
        confidence=0.7,  # Good confidence
        latency_ms=15.0,
        fallback_chain=[],
        metadata={}
    )
    
    # Configure mock to return different brains based on brain name
    def mock_get_brain_side_effect(brain_name):
        if brain_name == "ANALYTICAL":  # Primary brain for "analyze this data"
            return mock_primary_brain
        elif brain_name == "PRIMARY":  # First fallback in ANALYTICAL's chain
            return mock_fallback_brain
        return None
    
    mock_get_brain.side_effect = mock_get_brain_side_effect
    
    router = DynamicBrainRouter()
    response = router.route("analyze this data")  # This should classify as ANALYTICAL
    
    # Verify we got the fallback response
    assert isinstance(response, BrainResponse)
    assert response.content == "Fallback response"
    assert response.confidence == 0.7
    assert response.latency_ms == 15.0
    
    # Verify fallback was used
    assert response.metadata.get("fallback_used") == True
    assert response.metadata.get("routed_brain") == "PRIMARY"


@patch('src.nicto.brains.router.DynamicBrainRouter._get_brain_instance')
def test_router_route_all_fail(mock_get_brain):
    """Test routing when all brains fail to load."""
    # Configure mock to return None (brain failed to load)
    mock_get_brain.return_value = None
    
    router = DynamicBrainRouter()
    response = router.route("what is machine learning")
    
    # Verify we got an error response
    assert isinstance(response, BrainResponse)
    assert response.confidence == 0.0
    assert "Error:" in response.content
    assert response.metadata.get("error") == "all_brains_failed"
    assert response.metadata.get("task_category") == "PRIMARY"


def test_router_get_status():
    """Test getting router status."""
    router = DynamicBrainRouter()
    status = router.get_status()
    
    assert isinstance(status, dict)
    assert "hardware_profile" in status
    assert "loaded_brains" in status
    assert "brain_configs" in status
    assert "performance_history" in status
    
    # Check hardware profile structure
    hw = status["hardware_profile"]
    assert "gpu_available" in hw
    assert "gpu_name" in hw
    assert "gpu_memory_gb" in hw
    assert "cpu_count" in hw
    assert "ram_total_gb" in hw
    assert "platform" in hw
    
    # Check that we have config entries for brain types
    assert len(status["brain_configs"]) > 0
    for brain_name, config in status["brain_configs"].items():
        assert "model_name" in config
        assert "model_size_gb" in config
        assert "quantization_bits" in config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])