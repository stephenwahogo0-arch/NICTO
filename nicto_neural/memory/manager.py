from .base import MemoryStore, MemoryEntry, StoreMetadata
from .episodic import EpisodicMemory
from .semantic import SemanticMemory
from .skills import SkillMemory
from .goals import GoalMemory
from .personality import PersonalityMemory
from .reflection import ReflectionMemory
from .performance import PerformanceMemory
from .task_features import TaskFeatureMemory
from .consistency import ConsistencyMemory
from .experience import ExperienceMemory
from typing import Any, Dict, List, Optional, Tuple
import json
import time
import os
import threading


STORE_CLASSES = {
    "episodic": EpisodicMemory,
    "semantic": SemanticMemory,
    "skills": SkillMemory,
    "goals": GoalMemory,
    "personality": PersonalityMemory,
    "reflection": ReflectionMemory,
    "performance": PerformanceMemory,
    "task_features": TaskFeatureMemory,
    "consistency": ConsistencyMemory,
    "experience": ExperienceMemory,
}


class MemoryManager:
    def __init__(self, base_path: Optional[str] = None, max_entries: int = 100000):
        self._base_path = base_path or os.path.expanduser("~/.nicto/neural/memory")
        os.makedirs(self._base_path, exist_ok=True)
        self._max_entries = max_entries
        self._stores: Dict[str, MemoryStore] = {}
        self._access_times: Dict[str, Dict[str, float]] = {}
        self._lock = threading.Lock()
        self._init_stores()

    def _init_stores(self) -> None:
        for name, cls in STORE_CLASSES.items():
            store = cls(store_name=name, base_path=self._base_path)
            if name == "experience" and hasattr(store, "set_max_entries"):
                store.set_max_entries(self._max_entries)
            self._stores[name] = store
            self._access_times[name] = {}

    @property
    def stores(self) -> Dict[str, MemoryStore]:
        return dict(self._stores)

    def get_store(self, store_type: str) -> Optional[MemoryStore]:
        return self._stores.get(store_type)

    def store(
        self,
        key: str,
        value: Any,
        store_type: str = "semantic",
        metadata: Optional[Dict] = None,
    ) -> str:
        store = self._stores.get(store_type)
        if not store:
            raise ValueError(f"Unknown store type: {store_type}. Available: {list(self._stores.keys())}")
        with self._lock:
            result = store.store(key, value, metadata)
            self._access_times[store_type][key] = time.time()
            self._check_eviction(store, store_type)
        return result

    def query(
        self,
        query_text: str,
        store_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> Dict[str, List[Dict]]:
        types = store_types or list(self._stores.keys())
        results = {}
        with self._lock:
            for st in types:
                store = self._stores.get(st)
                if store:
                    try:
                        results[st] = store.query(query_text, limit)
                    except Exception:
                        results[st] = []
        return results

    def recall(self, key: str, store_type: str) -> Optional[Any]:
        store = self._stores.get(store_type)
        if not store:
            raise ValueError(f"Unknown store type: {store_type}")
        with self._lock:
            result = store.recall(key)
            if result is not None:
                self._access_times[store_type][key] = time.time()
        return result

    def forget(self, key: str, store_type: str) -> bool:
        store = self._stores.get(store_type)
        if not store:
            raise ValueError(f"Unknown store type: {store_type}")
        with self._lock:
            result = store.forget(key)
            if key in self._access_times.get(store_type, {}):
                del self._access_times[store_type][key]
        return result

    def _check_eviction(self, store: MemoryStore, store_type: str) -> None:
        if store.count() > self._max_entries:
            access = self._access_times.get(store_type, {})
            if len(access) > self._max_entries // 2:
                sorted_keys = sorted(access.items(), key=lambda x: x[1])
                to_remove = sorted_keys[:max(1, len(sorted_keys) // 10)]
                for key, _ in to_remove:
                    try:
                        store.forget(key)
                    except Exception:
                        pass
                    del access[key]

    def consolidate_all(self) -> Dict[str, float]:
        results = {}
        with self._lock:
            for name, store in self._stores.items():
                try:
                    t0 = time.time()
                    store.consolidate()
                    elapsed = time.time() - t0
                    results[name] = elapsed
                except Exception as e:
                    results[name] = -1.0
        return results

    def status(self) -> Dict[str, Dict]:
        results = {}
        with self._lock:
            for name, store in self._stores.items():
                try:
                    results[name] = {
                        "entry_count": store.count(),
                        "last_consolidated": store.metadata.last_consolidated,
                        "size_bytes": store.size_bytes(),
                    }
                except Exception as e:
                    results[name] = {"error": str(e)}
        return results

    def save_all(self, path: Optional[str] = None) -> str:
        save_path = path or os.path.join(self._base_path, "memory_manager_state.json")
        state = {
            "version": "1.0.0",
            "saved_at": time.time(),
            "stores": list(self._stores.keys()),
            "max_entries": self._max_entries,
            "store_counts": {name: store.count() for name, store in self._stores.items()},
            "access_times": self._access_times,
        }
        with open(save_path, "w") as f:
            json.dump(state, f, indent=2)
        for name, store in self._stores.items():
            try:
                store.consolidate()
            except Exception:
                pass
        return save_path

    def load_all(self, path: Optional[str] = None) -> bool:
        load_path = path or os.path.join(self._base_path, "memory_manager_state.json")
        if not os.path.exists(load_path):
            return False
        with open(load_path, "r") as f:
            state = json.load(f)
        stored_stores = state.get("stores", [])
        for name in stored_stores:
            if name not in self._stores:
                if name in STORE_CLASSES:
                    cls = STORE_CLASSES[name]
                    store = cls(store_name=name, base_path=self._base_path)
                    self._stores[name] = store
                    self._access_times[name] = {}
        self._max_entries = state.get("max_entries", self._max_entries)
        saved_access = state.get("access_times", {})
        for st, keys in saved_access.items():
            if st in self._access_times:
                self._access_times[st].update(keys)
        return True

    def close_all(self) -> None:
        with self._lock:
            for store in self._stores.values():
                try:
                    store.close()
                except Exception:
                    pass

    def __del__(self):
        self.close_all()
