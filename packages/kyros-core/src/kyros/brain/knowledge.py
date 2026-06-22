import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional
from kyros.brain.models import Belief, KnowledgeLevel


class NiktoKnowledgeCore:

    def __init__(self):
        self.facts = {}
        self.concepts = {}
        self.beliefs = {}
        self.relations = {}
        self.certainty_threshold = 0.6

    def add_fact(self, fact: str, source: str = "inference", confidence: float = 0.8) -> str:
        fid = hashlib.sha256(fact.encode()).hexdigest()[:16]
        self.facts[fid] = {
            "statement": fact,
            "source": source,
            "confidence": max(0.0, min(1.0, confidence)),
            "verified": False,
            "created": datetime.now(timezone.utc).isoformat(),
            "id": fid,
        }
        return fid

    def add_concept(self, name: str, definition: str, attributes: dict = None) -> str:
        cid = hashlib.sha256(name.encode()).hexdigest()[:16]
        self.concepts[cid] = {
            "name": name,
            "definition": definition,
            "attributes": attributes or {},
            "created": datetime.now(timezone.utc).isoformat(),
            "id": cid,
        }
        return cid

    def add_belief(self, statement: str, confidence: float = 0.5, source: str = "inference") -> str:
        belief = Belief(statement=statement, confidence=confidence, source=source)
        self.beliefs[belief.id] = belief
        return belief.id

    def relate(self, source_id: str, relation: str, target_id: str):
        key = (source_id, relation, target_id)
        self.relations[key] = {"strength": 0.8, "created": datetime.now(timezone.utc).isoformat()}

    def query(self, query_str: str) -> list:
        results = []
        q = query_str.lower()
        for fid, fact in self.facts.items():
            if q in fact["statement"].lower():
                results.append(fact)
        for cid, concept in self.concepts.items():
            if q in concept["name"].lower() or q in concept["definition"].lower():
                results.append(concept)
        return results

    def verify(self, fact_id: str, source: str = "cross_reference") -> bool:
        if fact_id in self.facts:
            self.facts[fact_id]["verified"] = True
            self.facts[fact_id]["source"] = source
            self.facts[fact_id]["confidence"] = min(1.0, self.facts[fact_id]["confidence"] + 0.1)
            return True
        return False

    def infer(self, premise_ids: list, conclusion: str) -> Optional[str]:
        if not premise_ids:
            return None
        avg_conf = sum(self.facts.get(pid, {}).get("confidence", 0) for pid in premise_ids) / len(premise_ids)
        infer_conf = avg_conf * 0.9
        if infer_conf >= self.certainty_threshold:
            return self.add_fact(conclusion, source="inference", confidence=infer_conf)
        return None

    def get_knowledge_graph(self, center_id: str, depth: int = 2) -> dict:
        graph = {"nodes": {}, "edges": []}
        visited = set()

        def traverse(nid, d):
            if nid in visited or d <= 0:
                return
            visited.add(nid)
            if nid in self.facts:
                graph["nodes"][nid] = {"type": "fact", "data": self.facts[nid]}
            for (s, r, t), rel in self.relations.items():
                if s == nid:
                    graph["edges"].append({"source": s, "relation": r, "target": t, "strength": rel["strength"]})
                    traverse(t, d - 1)
                elif t == nid:
                    graph["edges"].append({"source": s, "relation": r, "target": t, "strength": rel["strength"]})
                    traverse(s, d - 1)

        traverse(center_id, depth)
        return graph

    def export(self) -> dict:
        return {
            "facts": {k: v for k, v in self.facts.items()},
            "concepts": {k: v for k, v in self.concepts.items()},
            "beliefs": {k: b.to_dict() for k, b in self.beliefs.items()},
            "relations": {f"{s} -> {r} -> {t}": v for (s, r, t), v in self.relations.items()},
        }

    def save(self) -> dict:
        return {
            "facts": self.facts,
            "concepts": self.concepts,
            "beliefs": {k: b.to_dict() for k, b in self.beliefs.items()},
            "relations": {f"{s}|{r}|{t}": v for (s, r, t), v in self.relations.items()},
            "certainty_threshold": self.certainty_threshold,
        }

    def load(self, data: dict):
        self.facts = {k: v for k, v in data.get("facts", {}).items()}
        self.concepts = {k: v for k, v in data.get("concepts", {}).items()}
        self.beliefs = {}
        for k, bd in data.get("beliefs", {}).items():
            self.beliefs[k] = Belief(**bd)
        self.relations = {}
        for key, v in data.get("relations", {}).items():
            parts = key.split("|")
            if len(parts) == 3:
                self.relations[(parts[0], parts[1], parts[2])] = v
        self.certainty_threshold = data.get("certainty_threshold", 0.6)

    def merge(self, other: "NiktoKnowledgeCore"):
        self.facts.update(other.facts)
        self.concepts.update(other.concepts)
        self.beliefs.update(other.beliefs)
        self.relations.update(other.relations)
