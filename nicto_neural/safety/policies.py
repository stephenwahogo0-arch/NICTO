import time
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class RateLimit:
    max_calls: int
    window_seconds: float
    calls: List[float] = field(default_factory=list)


class PolicyEngine:
    def __init__(self):
        self._rate_limits: Dict[str, RateLimit] = {}
        self._default_recursion_depth = 10
        self._default_max_iterations = 100
        self._memory_protection_enabled = True

        self._set_default_limits()

    def _set_default_limits(self):
        self._rate_limits["*:*"] = RateLimit(max_calls=100, window_seconds=60.0)
        self._rate_limits["brain:think"] = RateLimit(max_calls=50, window_seconds=60.0)
        self._rate_limits["memory:store"] = RateLimit(max_calls=100, window_seconds=60.0)
        self._rate_limits["execution:shell"] = RateLimit(max_calls=10, window_seconds=60.0)

    def enforce(self, action: str, params: Dict = None) -> Tuple[bool, str]:
        action_key = action
        if action_key in self._rate_limits:
            allowed, reason = self._check_rate_limit(action_key)
            if not allowed:
                return False, reason
        wild_key = "*:*"
        if wild_key in self._rate_limits:
            allowed, reason = self._check_rate_limit(wild_key)
            if not allowed:
                return False, reason
        return True, "ok"

    def _check_rate_limit(self, key: str) -> Tuple[bool, str]:
        limit = self._rate_limits.get(key)
        if limit is None:
            return True, "ok"
        now = time.time()
        limit.calls = [c for c in limit.calls if now - c < limit.window_seconds]
        if len(limit.calls) >= limit.max_calls:
            return False, f"Rate limit exceeded for {key}: {limit.max_calls} per {limit.window_seconds}s"
        limit.calls.append(now)
        return True, "ok"

    def check_rate_limit(self, actor: str, action: str) -> bool:
        key = f"{actor}:{action}"
        allowed, _ = self._check_rate_limit(key)
        return allowed

    def check_recursion_depth(self, depth: int) -> bool:
        return depth <= self._default_recursion_depth

    def check_iterations(self, iteration: int) -> bool:
        return iteration <= self._default_max_iterations

    def set_recursion_depth(self, depth: int):
        self._default_recursion_depth = max(1, depth)

    def set_max_iterations(self, max_iter: int):
        self._default_max_iterations = max(1, max_iter)

    def check_memory_protection(self, store_type: str, size_bytes: int, max_bytes: int = 1073741824) -> bool:
        if not self._memory_protection_enabled:
            return True
        return size_bytes <= max_bytes

    def set_memory_protection(self, enabled: bool):
        self._memory_protection_enabled = enabled