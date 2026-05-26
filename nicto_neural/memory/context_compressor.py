class ContextCompressor:
    MAX_CONTEXT_TOKENS = 1_000_000
    COMPRESSION_RATIO = 0.3

    def __init__(self):
        self._context_buffer = []
        self._compressed_summaries = []
        self._token_estimate = 0

    def add(self, text, importance=0.5):
        tokens = len(text.split())
        self._context_buffer.append({"text": text, "importance": importance, "tokens": tokens})
        self._token_estimate += tokens
        if self._token_estimate > self.MAX_CONTEXT_TOKENS * 0.8:
            self.compress()

    def compress(self, text=None):
        if text is not None:
            tokens = len(text.split())
            self._context_buffer.append({"text": text, "importance": 0.5, "tokens": tokens})
            self._token_estimate += tokens
        if not self._context_buffer:
            return {"compressed": False, "text": text or ""}
        original_tokens = self._token_estimate
        sorted_items = sorted(self._context_buffer, key=lambda x: x["importance"], reverse=True)
        keep_count = max(10, int(len(sorted_items) * self.COMPRESSION_RATIO))
        kept = sorted_items[:keep_count]
        compressed = sorted_items[keep_count:]
        if compressed:
            summary_text = self._summarize(compressed)
            self._compressed_summaries.append({
                "summary": summary_text,
                "items_compressed": len(compressed),
                "tokens_before": sum(c["tokens"] for c in compressed),
                "tokens_after": len(summary_text.split()),
            })
            self._context_buffer = kept
            self._token_estimate = sum(k["tokens"] for k in kept) + len(summary_text.split())
        return {
            "compressed": bool(compressed),
            "items_kept": len(kept),
            "items_compressed": len(compressed),
            "tokens_before": original_tokens,
            "tokens_after": self._token_estimate,
            "compression_ratio": self._token_estimate / max(original_tokens, 1),
        }

    def _summarize(self, items):
        texts = [item["text"][:100] for item in items[:10]]
        return f"[COMPRESSED: {len(items)} items] " + " | ".join(texts)

    def get_context(self):
        parts = []
        for summary in self._compressed_summaries[-3:]:
            parts.append(summary["summary"])
        for item in self._context_buffer[-50:]:
            parts.append(item["text"])
        return "\n".join(parts)

    def get_stats(self):
        return {
            "current_tokens": self._token_estimate,
            "max_tokens": self.MAX_CONTEXT_TOKENS,
            "usage_percent": self._token_estimate / self.MAX_CONTEXT_TOKENS * 100,
            "compression_events": len(self._compressed_summaries),
            "buffer_items": len(self._context_buffer),
        }
