"""
Infinite Context Engine for NIKTO.

Simulates effectively infinite context by compressing/ chunking
conversation history and tracking total tokens processed.
"""

from typing import Any, Optional


class InfiniteContextEngine:
    """Maintains a sliding window of context and a running token counter."""

    def __init__(self, max_tokens: int = 8192) -> None:
        self.max_tokens: int = max_tokens
        self.total_processed: int = 0
        self._buffer: list[dict[str, Any]] = []
        self._current_tokens: int = 0

    def add(self, text: str, metadata: Optional[dict[str, Any]] = None) -> int:
        """Add text to the context buffer and return estimated token count."""
        tokens = self._estimate_tokens(text)
        self.total_processed += tokens
        self._buffer.append({"text": text, "tokens": tokens, "metadata": metadata or {}})
        self._current_tokens += tokens
        self._maybe_compress()
        return tokens

    def compress(self, ratio: float = 0.5) -> dict[str, Any]:
        """Compress the context buffer (keep the most recent *ratio*)."""
        if not self._buffer:
            return {"compressed": 0, "remaining": 0}
        keep = max(1, int(len(self._buffer) * ratio))
        removed = self._buffer[:-keep]
        self._buffer = self._buffer[-keep:]
        removed_tokens = sum(r["tokens"] for r in removed)
        self._current_tokens -= removed_tokens
        return {"compressed": len(removed), "remaining": len(self._buffer)}

    def get_context(self, limit: Optional[int] = None) -> str:
        """Return concatenated context text."""
        texts = [entry["text"] for entry in self._buffer]
        combined = "\n".join(texts)
        if limit and len(combined) > limit:
            combined = combined[-limit:]
        return combined

    def stats(self) -> dict[str, Any]:
        """Return engine statistics."""
        return {
            "total_processed": self.total_processed,
            "buffer_length": len(self._buffer),
            "current_tokens": self._current_tokens,
            "max_tokens": self.max_tokens,
        }

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token estimate (characters / 4)."""
        return max(1, len(text) // 4)

    def _maybe_compress(self) -> None:
        if self._current_tokens > self.max_tokens:
            ratio = self.max_tokens / max(self._current_tokens, 1)
            self.compress(ratio)
