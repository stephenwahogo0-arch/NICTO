"""Multi-process brain — runs regions in parallel child processes, bypassing GIL."""
import json
import multiprocessing
import os
import time
import uuid
from multiprocessing import shared_memory
from pathlib import Path
from typing import Any, Optional

import numpy as np


class ParallelRegion:
    """A region that runs in its own child process with its own GIL."""

    def __init__(self, name: str, description: str, func=None):
        self.name = name
        self.description = description
        self.func = func
        self.activations = 0

    def process(self, input_data: str, context: Optional[dict] = None) -> dict:
        self.activations += 1
        if self.func:
            return self.func(input_data, context or {})
        return {"region": self.name, "processed": True, "activations": self.activations}


def _region_worker(region_name: str, input_text: str, shm_name: str, shm_size: int, result_event):
    """Target function for each child process — runs one region."""
    try:
        region = ParallelRegion(region_name, f"Worker for {region_name}")
        ctx = {}
        result = region.process(input_text, ctx)
        result_bytes = json.dumps(result).encode("utf-8")
        try:
            existing_shm = shared_memory.SharedMemory(name=shm_name)
            data = result_bytes[:shm_size]
            existing_shm.buf[:len(data)] = data
            existing_shm.buf[len(data):shm_size] = b" " * (shm_size - len(data))
            existing_shm.close()
        except Exception:
            pass
    except Exception as e:
        try:
            existing_shm = shared_memory.SharedMemory(name=shm_name)
            err_bytes = json.dumps({"error": str(e)}).encode("utf-8")
            existing_shm.buf[:len(err_bytes)] = err_bytes
            existing_shm.close()
        except Exception:
            pass
    finally:
        if result_event:
            result_event.set()


class MultiprocessBrain:
    """Brain that spawns parallel child processes, each with its own GIL.

    Uses multiprocessing.shared_memory to pass results back without disk I/O.
    """

    def __init__(self, max_workers: Optional[int] = None):
        self.session_id = uuid.uuid4().hex[:12]
        self.birth_time = time.time()
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.regions = self._init_regions()
        self._active_processes: dict[str, multiprocessing.Process] = {}
        self.data_dir = Path(os.path.expanduser("~/.nikto/brain"))
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _init_regions(self) -> dict[str, ParallelRegion]:
        return {
            "reasoning": ParallelRegion("reasoning", "Logical reasoning and analysis", self._reason),
            "memory": ParallelRegion("memory", "Store and retrieve conversation memory"),
            "planning": ParallelRegion("planning", "Break tasks into steps", self._plan),
            "creativity": ParallelRegion("creativity", "Generate novel ideas and responses"),
            "evaluation": ParallelRegion("evaluation", "Evaluate response quality", self._evaluate),
        }

    def _reason(self, text: str, ctx: dict) -> dict:
        return {"type": "reasoning", "input_length": len(text), "complexity": len(text.split())}

    def _plan(self, text: str, ctx: dict) -> dict:
        steps = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if len(s.strip()) > 10]
        return {"steps": steps[:5] if steps else ["process_request"], "count": min(len(steps), 5) if steps else 1}

    def _evaluate(self, text: str, ctx: dict) -> dict:
        return {"confidence": min(1.0, len(text) / 500), "length_ok": len(text) > 10}

    def think(self, input_text: str, context: Optional[dict] = None) -> dict:
        """Run all regions in parallel child processes.

        Each region gets its own OS process with its own GIL.
        Results are passed back via shared memory segments.
        """
        ctx = context or {}
        processes = {}
        result_events = {}
        shm_segments = {}

        for name, region in self.regions.items():
            shm = shared_memory.SharedMemory(create=True, size=4096)
            shm_segments[name] = shm
            event = multiprocessing.Event()
            result_events[name] = event

            proc = multiprocessing.Process(
                target=_region_worker,
                args=(name, input_text, shm.name, 4096, event),
                daemon=True,
            )
            proc.start()
            processes[name] = proc

        results = {}
        for name in self.regions:
            event = result_events[name]
            event.wait(timeout=15.0)
            shm = shm_segments[name]
            raw = bytes(shm.buf[:4096]).rstrip(b" \x00")
            try:
                results[name] = json.loads(raw.decode("utf-8", errors="replace"))
            except (json.JSONDecodeError, ValueError):
                results[name] = {"region": name, "processed": True, "note": "no_result"}
            processes[name].join(timeout=2.0)
            shm.close()
            shm.unlink()

        return {
            "regions": results,
            "session_id": self.session_id,
            "parallelism": "process",
            "workers": len(processes),
        }

    @staticmethod
    def compute_parallel(func, items: list[Any], max_workers: Optional[int] = None) -> list:
        """Generic parallel compute using multiprocessing pool."""
        n_workers = max_workers or multiprocessing.cpu_count()
        with multiprocessing.Pool(processes=n_workers) as pool:
            results = pool.map(func, items)
        return results

    @staticmethod
    def compute_chunked(func, items: list[Any], chunk_size: int = 4) -> list:
        """Lazy evaluation — only processes subset at a time to prevent CPU overload."""
        results = []
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            with multiprocessing.Pool(processes=min(len(chunk), multiprocessing.cpu_count())) as pool:
                chunk_results = pool.map(func, chunk)
                results.extend(chunk_results)
        return results

    def get_summary(self) -> dict:
        return {
            "regions": list(self.regions.keys()),
            "region_count": len(self.regions),
            "max_workers": self.max_workers,
            "session_id": self.session_id,
        }
