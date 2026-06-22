"""ChromaDB-backed knowledge base with 12 collections and 400+ real knowledge entries."""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMA = True
except ImportError:
    chromadb = None
    Settings = None
    HAS_CHROMA = False
    logger.warning("chromadb not installed - knowledge base will run in fallback JSON mode")


INITIAL_KNOWLEDGE: dict[str, dict[str, dict]] = {}
_loaded = False


def _ensure_data():
    global _loaded
    if _loaded:
        return
    _load_knowledge_data()
    _loaded = True


def _load_knowledge_data():
    data_dir = Path(__file__).parent / "data"
    if not data_dir.exists():
        logger.warning("Knowledge data directory not found at %s", data_dir)
        return
    for fname in sorted(data_dir.glob("*.json")):
        col_name = fname.stem
        try:
            entries = json.loads(fname.read_text(encoding="utf-8"))
            INITIAL_KNOWLEDGE[col_name] = entries
            logger.debug("Loaded %d entries from %s", len(entries), fname.name)
        except Exception as e:
            logger.error("Failed to load %s: %s", fname, e)


class KnowledgeBase:
    def __init__(self, path: str = "~/.kyros/knowledge_db"):
        self.db_path = Path(path).expanduser()
        self.db_path.mkdir(parents=True, exist_ok=True)
        _ensure_data()
        self._chroma_ok = False
        if HAS_CHROMA:
            try:
                self._init_chromadb()
                self._chroma_ok = True
                return
            except Exception as exc:
                logger.warning("ChromaDB init failed (%s), using fallback", exc)
        self._init_fallback()

    def _init_chromadb(self):
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collections: dict[str, Any] = {}
        for col_name, entries in INITIAL_KNOWLEDGE.items():
            col = self._get_or_create_collection(col_name)
            existing = col.count()
            if existing == 0:
                for eid, edata in entries.items():
                    col.add(
                        ids=[eid],
                        documents=[edata["content"]],
                        metadatas=[{"category": edata["metadata"]["category"], "tags": ",".join(edata["metadata"]["tags"])}],
                    )
            self.collections[col_name] = col

    def _get_or_create_collection(self, name: str):
        try:
            return self.client.get_collection(name)
        except Exception:
            return self.client.create_collection(name)

    def _init_fallback(self):
        self.fallback_file = self.db_path / "knowledge_fallback.json"
        self.fallback_data: dict[str, Any] = {}
        if self.fallback_file.exists():
            try:
                self.fallback_data = json.loads(self.fallback_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        for col_name, entries in INITIAL_KNOWLEDGE.items():
            if col_name not in self.fallback_data:
                self.fallback_data[col_name] = {k: v["content"] for k, v in entries.items()}
        self.fallback_file.write_text(json.dumps(self.fallback_data, indent=2), encoding="utf-8")

    def add_entry(self, collection: str, id: str, content: str, metadata: dict):
        if self._chroma_ok:
            col = self.get_collection(collection)
            if col:
                col.add(
                    ids=[id],
                    documents=[content],
                    metadatas=[{"category": metadata.get("category", ""), "tags": ",".join(metadata.get("tags", []))}],
                )
        else:
            if collection not in self.fallback_data:
                self.fallback_data[collection] = {}
            self.fallback_data[collection][id] = content
            self.fallback_file.write_text(json.dumps(self.fallback_data, indent=2), encoding="utf-8")

    def search(self, collection: str, query: str, n_results: int = 5) -> list[dict]:
        if self._chroma_ok:
            col = self.get_collection(collection)
            if not col:
                return []
            results = col.query(query_texts=[query], n_results=n_results)
            output = []
            for i in range(len(results["ids"][0])):
                output.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0,
                })
            return output
        else:
            col_data = self.fallback_data.get(collection, {})
            query_lower = query.lower()
            results = []
            for eid, content in col_data.items():
                if query_lower in content.lower():
                    results.append({"id": eid, "content": content, "metadata": {}, "distance": 0})
            return results[:n_results]

    def get_collection(self, name: str):
        if self._chroma_ok:
            try:
                return self.client.get_collection(name)
            except Exception:
                return None
        return self.fallback_data.get(name, {})

    def list_collections(self) -> list[str]:
        if self._chroma_ok:
            cols = self.client.list_collections()
            return [c.name for c in cols]
        return list(self.fallback_data.keys())

    def get_knowledge(self, category: str, topic: str) -> Optional[str]:
        col = INITIAL_KNOWLEDGE.get(category, {})
        entry = col.get(topic)
        if entry:
            return entry["content"]
        if HAS_CHROMA:
            result = self.search(category, topic, n_results=1)
            if result:
                return result[0]["content"]
        return None


knowledge_base: Optional[KnowledgeBase] = None


def get_knowledge(category: str, topic: str) -> Optional[str]:
    global knowledge_base
    if knowledge_base is None:
        knowledge_base = KnowledgeBase()
    return knowledge_base.get_knowledge(category, topic)


def search_knowledge(query: str, n_results: int = 5) -> list[dict]:
    global knowledge_base
    if knowledge_base is None:
        knowledge_base = KnowledgeBase()
    all_results = []
    for col_name in INITIAL_KNOWLEDGE:
        results = knowledge_base.search(col_name, query, n_results)
        all_results.extend(results)
    all_results.sort(key=lambda r: r.get("distance", 0))
    return all_results[:n_results]


def get_knowledge_collection_names() -> list[str]:
    return list(INITIAL_KNOWLEDGE.keys())
