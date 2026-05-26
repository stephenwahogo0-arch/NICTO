import json
import os
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional


class NiktoConversationMemory:
    """Persistent conversation history across sessions."""

    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(os.path.expanduser("~"), ".nikto", "conversations")
        os.makedirs(self.storage_dir, exist_ok=True)
        self._cache = {}

    def _user_path(self, user_id: str) -> str:
        safe = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        return os.path.join(self.storage_dir, f"{safe}.jsonl")

    async def save_message(self, user_id: str, role: str, content: str, metadata: dict = None):
        path = self._user_path(user_id)
        entry = {
            "id": hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._cache.pop(user_id, None)

    async def get_history(self, user_id: str, limit: int = 50, since: str = None) -> list:
        path = self._user_path(user_id)
        if not os.path.exists(path):
            return []
        messages = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                msg = json.loads(line)
                if since and msg.get("timestamp", "") < since:
                    continue
                messages.append(msg)
        return messages[-limit:]

    async def search_history(self, user_id: str, query: str) -> list:
        messages = await self.get_history(user_id, limit=1000)
        q = query.lower()
        return [m for m in messages if q in m.get("content", "").lower()]

    async def summarize_history(self, user_id: str) -> str:
        messages = await self.get_history(user_id, limit=200)
        if not messages:
            return "No conversation history."
        topics = set()
        word_count = 0
        for m in messages:
            words = m.get("content", "").split()
            word_count += len(words)
            if len(words) > 3:
                topics.add(words[0] if len(words) > 0 else "")
        return f"Conversation with {user_id}: {len(messages)} messages, ~{word_count} words. Topics include: {', '.join(list(topics)[:5])}."

    async def export_history(self, user_id: str, format: str = "json") -> str:
        messages = await self.get_history(user_id, limit=10000)
        if format == "json":
            return json.dumps(messages, indent=2, ensure_ascii=False)
        elif format == "txt":
            lines = []
            for m in messages:
                lines.append(f"[{m.get('timestamp', '')}] {m.get('role', '')}: {m.get('content', '')}")
            return "\n".join(lines)
        return json.dumps(messages, indent=2, ensure_ascii=False)

    async def delete_history(self, user_id: str):
        path = self._user_path(user_id)
        if os.path.exists(path):
            os.remove(path)
        self._cache.pop(user_id, None)
