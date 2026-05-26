"""Real knowledge engine — synthesizes knowledge from memory patterns."""
import json
import os
import time
from pathlib import Path
from typing import Optional


class KnowledgeEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or os.path.join(str(Path.home()), ".kyros", "knowledge"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_file = self.data_dir / "knowledge.json"
        self.knowledge = self._load()

    def _load(self) -> dict:
        if self.knowledge_file.exists():
            try:
                return json.loads(self.knowledge_file.read_text())
            except Exception:
                pass
        return {"topics": {}, "facts": [], "patterns": [], "last_updated": 0}

    def _save(self):
        self.knowledge["last_updated"] = time.time()
        self.knowledge_file.write_text(json.dumps(self.knowledge, indent=2))

    def add_fact(self, topic: str, fact: str, confidence: float = 0.5):
        if topic not in self.knowledge["topics"]:
            self.knowledge["topics"][topic] = []
        self.knowledge["topics"][topic].append({"fact": fact, "confidence": confidence, "added": time.time()})
        self.knowledge["facts"].append({"topic": topic, "fact": fact, "confidence": confidence})
        if len(self.knowledge["facts"]) > 10000:
            self.knowledge["facts"] = self.knowledge["facts"][-10000:]
        self._save()

    def add_pattern(self, pattern: str, category: str = "general"):
        self.knowledge["patterns"].append({"pattern": pattern, "category": category, "added": time.time()})
        if len(self.knowledge["patterns"]) > 5000:
            self.knowledge["patterns"] = self.knowledge["patterns"][-5000:]
        self._save()

    def query(self, topic: str, limit: int = 10) -> list:
        facts = self.knowledge.get("topics", {}).get(topic, [])
        return sorted(facts, key=lambda f: f["confidence"], reverse=True)[:limit]

    def search(self, query: str, limit: int = 10) -> list:
        query = query.lower()
        results = []
        for fact in self.knowledge.get("facts", []):
            if query in fact.get("fact", "").lower() or query in fact.get("topic", "").lower():
                results.append(fact)
        return sorted(results, key=lambda f: f["confidence"], reverse=True)[:limit]

    def get_topics(self) -> list:
        return list(self.knowledge.get("topics", {}).keys())

    def get_stats(self) -> dict:
        return {"topics": len(self.knowledge.get("topics", {})), "facts": len(self.knowledge.get("facts", [])),
                "patterns": len(self.knowledge.get("patterns", [])), "last_updated": self.knowledge.get("last_updated", 0)}

    def build_context_block(self, query: str, max_facts: int = 5) -> str:
        facts = self.search(query, max_facts)
        if not facts:
            return ""
        context = "\n".join(f"- {f['fact']}" for f in facts)
        return f"[Knowledge Context]\n{context}\n"
