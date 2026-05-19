import json
import time
from pathlib import Path
from typing import Any, Optional

from nikto.capabilities.manifest import CapabilityManifest, FeatureCapability


class KnowledgeEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.kb_path = self.data_dir / "knowledge_base.json"
        self._vector_enabled = False
        self._collection = None
        self._vector_initialized = False
        self._knowledge: dict[str, dict] = {}
        self._load()

    def _ensure_vector(self):
        if self._vector_initialized:
            return
        self._vector_initialized = True
        try:
            import chromadb
            chroma_path = str(self.data_dir / "chroma_kb")
            self.chroma = chromadb.PersistentClient(path=chroma_path)
            try:
                self._collection = self.chroma.get_collection("nikto_knowledge")
            except Exception:
                self._collection = self.chroma.create_collection("nikto_knowledge")
            self._vector_enabled = True
        except Exception:
            self._vector_enabled = False

    def _load(self):
        if self.kb_path.exists():
            try:
                self._knowledge = json.loads(self.kb_path.read_text())
            except Exception:
                self._knowledge = {}

    def _save(self):
        self.kb_path.write_text(json.dumps(self._knowledge, indent=2))

    def ingest_manifest(self, manifest: CapabilityManifest):
        self._ensure_vector()
        count = 0
        for feature in manifest.features:
            key = f"{feature.module}.{feature.name}"
            entry = feature.to_dict()
            entry["doc"] = feature.doc
            entry["methods"] = feature.methods
            entry["source_preview"] = feature.source_preview[:200]
            entry["ingested_at"] = time.time()
            self._knowledge[key] = entry
            count += 1

            if self._vector_enabled:
                self._index_vector(feature)

        self._save()

    def _index_vector(self, feature: FeatureCapability):
        if not self._vector_enabled or self._collection is None:
            return
        doc_text = f"Feature: {feature.name}\nModule: {feature.module}\nCategory: {feature.category}\nDescription: {feature.doc}\nMethods: {', '.join(feature.methods)}"
        key = f"{feature.module}.{feature.name}"
        try:
            self._collection.add(
                ids=[key],
                documents=[doc_text],
                metadatas=[{
                    "name": feature.name,
                    "module": feature.module,
                    "category": feature.category,
                }],
            )
        except Exception:
            pass

    def query(self, query: str, limit: int = 10) -> list[dict]:
        self._ensure_vector()
        results = []

        if self._vector_enabled and self._collection is not None:
            try:
                vector_results = self._collection.query(
                    query_texts=[query], n_results=limit
                )
                for i, doc in enumerate(vector_results["documents"][0]):
                    results.append({
                        "content": doc,
                        "score": float(vector_results["distances"][0][i]) if vector_results.get("distances") else 0.0,
                        "type": "vector",
                    })
            except Exception:
                pass

        if not results:
            query_lower = query.lower()
            scored = []
            for key, entry in self._knowledge.items():
                score = 0
                if query_lower in key.lower():
                    score += 10
                if query_lower in entry.get("doc", "").lower():
                    score += 5
                if query_lower in entry.get("category", "").lower():
                    score += 3
                if query_lower in " ".join(entry.get("methods", [])).lower():
                    score += 2
                if score > 0:
                    scored.append((score, entry))
            scored.sort(key=lambda x: -x[0])
            for score, entry in scored[:limit]:
                results.append({
                    "content": json.dumps(entry),
                    "score": score,
                    "type": "keyword",
                })

        return results[:limit]

    def get_feature(self, name: str) -> Optional[dict]:
        for key, entry in self._knowledge.items():
            if key.endswith(f".{name}") or entry.get("name") == name:
                return entry
        return None

    def get_all_by_category(self, category: str) -> list[dict]:
        return [e for e in self._knowledge.values() if e.get("category") == category]

    def get_all(self) -> dict[str, dict]:
        return dict(self._knowledge)

    def total_features(self) -> int:
        return len(self._knowledge)

    def summary(self) -> dict:
        categories = {}
        for entry in self._knowledge.values():
            cat = entry.get("category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total": self.total_features(),
            "vector_enabled": self._vector_enabled,
            "categories": categories,
        }

    def build_context_block(self, task: str = "") -> str:
        if not self._knowledge:
            return ""

        if task:
            relevant = self.query(task, limit=8)
            if relevant:
                context = "## RELEVANT CAPABILITIES (Knowledge Base)\n"
                for i, r in enumerate(relevant, 1):
                    try:
                        data = json.loads(r["content"]) if isinstance(r["content"], str) else r["content"]
                        context += f"{i}. {data.get('name','?')} [{data.get('category','?')}] — {data.get('doc','')[:200]}\n"
                    except Exception:
                        context += f"{i}. {r['content'][:200]}\n"
                return context

        return ""

    def build_full_knowledge_context(self) -> str:
        if not self._knowledge:
            return ""

        cats = {}
        for entry in self._knowledge.values():
            cat = entry.get("category", "Other")
            if cat not in cats:
                cats[cat] = []
            cats[cat].append(entry.get("name", "?"))

        context = "## MASTERCLASS EXPERTISE — ALL CAPABILITIES\n"
        for cat in sorted(cats.keys()):
            names = cats[cat]
            context += f"\n### {cat} ({len(names)} features)\n"
            for name in sorted(names):
                entry = self.get_feature(name)
                doc = (entry.get("doc", "") or "")[:120] if entry else ""
                context += f"- **{name}**: {doc}\n"

        return context
