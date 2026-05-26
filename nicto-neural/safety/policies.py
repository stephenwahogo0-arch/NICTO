"""Safety policies — rate limits, recursion guards, operational constraints."""

import time


class SafetyPolicies:
    """Rate limiting, recursion guards, and operational constraints."""

    def __init__(self):
        self._call_times: dict[str, list[float]] = {}
        self._recursion_depth: dict[str, int] = {}
        self._max_recursion = 50
        self._rate_limits: dict[str, tuple[int, float]] = {
            "think": (100, 60.0),
            "train": (10, 300.0),
            "deploy": (5, 600.0),
        }

    def check_rate_limit(self, operation: str) -> dict:
        """Check if operation exceeds rate limit."""
        if operation not in self._rate_limits:
            return {"allowed": True, "operation": operation}

        max_calls, window_seconds = self._rate_limits[operation]
        now = time.time()

        if operation not in self._call_times:
            self._call_times[operation] = []

        self._call_times[operation] = [
            t for t in self._call_times[operation]
            if now - t < window_seconds
        ]

        if len(self._call_times[operation]) >= max_calls:
            return {
                "allowed": False,
                "operation": operation,
                "reason": f"Rate limit exceeded: {max_calls} calls per {window_seconds}s",
                "retry_after": window_seconds - (now - self._call_times[operation][0]),
            }

        self._call_times[operation].append(now)
        return {"allowed": True, "operation": operation}

    def check_recursion(self, context_id: str) -> dict:
        """Guard against infinite recursion."""
        depth = self._recursion_depth.get(context_id, 0)
        if depth >= self._max_recursion:
            return {
                "allowed": False,
                "reason": f"Recursion depth {depth} exceeds limit {self._max_recursion}",
                "depth": depth,
            }
        self._recursion_depth[context_id] = depth + 1
        return {"allowed": True, "depth": depth + 1}

    def reset_recursion(self, context_id: str) -> None:
        self._recursion_depth[context_id] = 0

    def set_rate_limit(
        self, operation: str, max_calls: int, window_seconds: float
    ) -> None:
        self._rate_limits[operation] = (max_calls, window_seconds)
