"""Tests for memory system."""

import tempfile
from pathlib import Path

from nicto_neural.memory.base import MemoryEntry
from nicto_neural.memory.episodic import EpisodicMemory
from nicto_neural.memory.semantic import SemanticMemory
from nicto_neural.memory.manager import MemoryManager
from nicto_neural.neural.config import NeuralConfig


def test_episodic_store_and_recall():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = EpisodicMemory(tmpdir)
        entry = MemoryEntry(content={"input": "hello"}, importance=0.8)
        entry_id = mem.store(entry)
        recalled = mem.recall("recent", 10)
        assert len(recalled) >= 1
        assert recalled[0].content == {"input": "hello"}


def test_semantic_search():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = SemanticMemory(tmpdir)
        entry = MemoryEntry(content="Python is a programming language", importance=0.9)
        mem.store(entry)
        results = mem.recall("Python", 10)
        assert len(results) >= 1


def test_memory_manager():
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    manager = MemoryManager(config)
    manager.store_episode({"input": "test task", "domain": "general"})
    stats = manager.total_memories()
    assert stats["episodic"] >= 1


def test_experience_buffer():
    import torch
    from nicto_neural.memory.experience import ExperienceBuffer

    buf = ExperienceBuffer(capacity=100)
    for _ in range(20):
        buf.add(
            state=torch.randn(15),
            action=0,
            reward=1.0,
            next_state=torch.randn(15),
            done=False,
        )
    assert buf.is_ready(10)
    batch = buf.sample(8)
    assert len(batch["states"]) == 8
