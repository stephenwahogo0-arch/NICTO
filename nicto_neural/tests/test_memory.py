import pytest
import os
import shutil
import tempfile
import time
from ..memory.manager import MemoryManager
from ..memory.base import MemoryEntry


@pytest.fixture
def temp_memory():
    temp_dir = tempfile.mkdtemp()
    mgr = MemoryManager(base_path=temp_dir)
    yield mgr
    # Close SQLite connections before cleanup on Windows
    try:
        for name, store in mgr._stores.items():
            if hasattr(store, '_close'):
                store._close()
            elif hasattr(store, 'close'):
                store.close()
        time.sleep(0.1)
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


def test_manager_crud(temp_memory):
    # Store and recall
    res = temp_memory.store("test_key", "test_value", "episodic", {"meta": "data"})
    assert res is not None
    
    val = temp_memory.recall("test_key", "episodic")
    assert val == "test_value"


def test_semantic_memory(temp_memory):
    store = temp_memory._stores["semantic"]
    store.store_fact("subject", "predicate", "object", 0.95)
    
    facts = store.query_facts(subject="subject")
    assert len(facts) == 1
    assert facts[0]["object"] == "object"


def test_skill_memory(temp_memory):
    store = temp_memory._stores["skills"]
    store.register_skill("python_coding", "code")
    store.update_mastery("python_coding", True)
    
    skills = store.top_skills("code")
    assert len(skills) == 1
    assert skills[0]["skill_name"] == "python_coding"


def test_goal_memory(temp_memory):
    store = temp_memory._stores["goals"]
    goal_id = store.create_goal("Test Goal", priority=5)
    assert goal_id is not None
    
    active = store.active_goals()
    assert len(active) == 1
    assert active[0]["description"] == "Test Goal"


def test_personality_memory(temp_memory):
    store = temp_memory._stores["personality"]
    store.set_trait("creativity", 0.9, 0.95)
    trait = store.get_trait("creativity")
    assert trait is not None


def test_reflection_memory(temp_memory):
    store = temp_memory._stores["reflection"]
    store.store_reflection({
        "reflection_id": "r1",
        "task_id": "t1",
        "brain": "analytical",
        "domain": "math",
        "was_correct": True,
        "confidence": 0.9,
        "missing_knowledge": "",
        "needed_tool": "",
        "improvement": "",
        "score": 0.95,
        "timestamp": 123456.0,
    })
    recent = store.recent_reflections()
    assert len(recent) == 1


def test_experience_replay(temp_memory):
    store = temp_memory._stores["experience"]
    s = [0.1] * 15
    ns = [0.2] * 15
    store.add_experience(s, 1, 1.0, ns, False)
    count = store.count()
    assert count == 1
    
    batch = store.sample(1)
    assert len(batch) >= 1
