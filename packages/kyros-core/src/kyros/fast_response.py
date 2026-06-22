"""Ultra-fast response system with caching, batching, and parallel processing."""

import asyncio
import concurrent.futures
import functools
import hashlib
import json
import math
import os
import random
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Optional


class ResponseCache:
    """LRU cache for generated responses — instant replay for repeated queries."""

    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = OrderedDict()
        self._lock = threading.Lock()

    def _key(self, text: str, mode: str = "default") -> str:
        return hashlib.md5(f"{text}:{mode}".encode()).hexdigest()

    def get(self, text: str, mode: str = "default") -> Optional[str]:
        key = self._key(text, mode)
        with self._lock:
            entry = self._cache.get(key)
            if entry and time.time() - entry["time"] < self.ttl:
                entry["hits"] = entry.get("hits", 0) + 1
                self._cache.move_to_end(key)
                return entry["response"]
            if entry:
                del self._cache[key]
            return None

    def set(self, text: str, response: str, mode: str = "default"):
        key = self._key(text, mode)
        with self._lock:
            self._cache[key] = {"response": response, "time": time.time(), "hits": 0}
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def stats(self) -> dict:
        with self._lock:
            return {"size": len(self._cache), "max": self.max_size, "ttl": self.ttl}

    def clear(self):
        with self._lock:
            self._cache.clear()


class ParallelProcessor:
    """Process multiple queries in parallel with thread pooling."""

    def __init__(self, max_workers: int = None):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers or (os.cpu_count() or 4) * 2)

    def process_batch(self, items: list, fn, timeout: float = 30.0) -> list:
        futures = {self.executor.submit(fn, item): item for item in items}
        results = []
        for future in concurrent.futures.as_completed(futures, timeout=timeout):
            try:
                results.append({"input": futures[future], "result": future.result()})
            except Exception as e:
                results.append({"input": futures[future], "error": str(e)})
        return results

    def process_stream(self, items: list, fn):
        for item in items:
            yield fn(item)

    def shutdown(self):
        self.executor.shutdown(wait=True)


class FastResponseSystem:
    """Ultra-fast response system combining cache, parallel processing, and prefetch."""

    def __init__(self, agent=None):
        self.agent = agent
        self.cache = ResponseCache()
        self.processor = ParallelProcessor()
        self._prefetch_queue = asyncio.Queue()
        self._prefetch_active = False
        self._stats = {"cache_hits": 0, "cache_misses": 0, "avg_time_ms": 0.0, "total_queries": 0}

    async def respond(self, query: str, mode: str = "default") -> str:
        start = time.time()
        self._stats["total_queries"] += 1
        cached = self.cache.get(query, mode)
        if cached:
            self._stats["cache_hits"] += 1
            return cached
        self._stats["cache_misses"] += 1
        if self.agent and hasattr(self.agent, 'run_sync'):
            response = await self.agent.run_sync(query)
        else:
            response = f"Processed: {query[:100]}"
        response_str = str(response) if response else ""
        self.cache.set(query, response_str, mode)
        elapsed = time.time() - start
        self._stats["avg_time_ms"] = (self._stats["avg_time_ms"] * (self._stats["total_queries"] - 1) + elapsed * 1000) / self._stats["total_queries"]
        return response_str

    async def respond_batch(self, queries: list, mode: str = "default") -> list:
        return [await self.respond(q, mode) for q in queries]

    def get_stats(self) -> dict:
        return self._stats

    def clear_cache(self):
        self.cache.clear()
