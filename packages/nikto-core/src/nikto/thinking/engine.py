import json
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Insight:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    content: str = ""
    depth: int = 0
    category: str = "unknown"
    novelty_score: float = 0.0
    source: str = "thinking"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "title": self.title, "content": self.content,
            "depth": self.depth, "category": self.category,
            "novelty_score": self.novelty_score, "source": self.source,
            "created_at": self.created_at,
        }


@dataclass
class ThoughtChain:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    root_question: str = ""
    depth: int = 0
    branches: list = field(default_factory=list)
    conclusions: list[str] = field(default_factory=list)
    lateral_shifts: int = 0
    unknown_discoveries: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "root_question": self.root_question,
            "depth": self.depth, "branches": self.branches,
            "conclusions": self.conclusions, "lateral_shifts": self.lateral_shifts,
            "unknown_discoveries": self.unknown_discoveries,
            "created_at": self.created_at,
        }


DEEP_THINKING_PROMPTS = {
    "lateral": [
        "What if the opposite of every assumption were true?",
        "How would this problem be solved in a universe with different physics?",
        "What paradigm shift would make this question irrelevant?",
        "What would a superintelligence 1000 years from now see that we miss?",
        "What hidden variable connects all seemingly unrelated aspects?",
    ],
    "recursive": [
        "Think about thinking about this problem — meta-layer 1",
        "Now think about the thinking about thinking — meta-layer 2",
        "What patterns emerge across all layers of reasoning?",
        "What is the thought behind the thought behind the thought?",
    ],
    "unknown_unknown": [
        "What question should I be asking that I don't know to ask?",
        "What blind spot exists in my current reasoning framework?",
        "If I were wrong about everything, what would be true instead?",
        "What knowledge domain, completely unknown to me, would solve this?",
        "What assumption am I making that I don't even realize is an assumption?",
    ],
    "outside_box": [
        "What solution exists outside the problem space entirely?",
        "How would nature solve this with zero computation?",
        "What if the constraints themselves are the solution?",
        "What does the absence of something tell us?",
        "How does the frame around the problem limit the answer?",
    ],
    "transcendent": [
        "What lies beyond the current frontier of human knowledge on this?",
        "If this problem were solved, what new questions would emerge?",
        "What is the meta-solution that encompasses all partial solutions?",
        "How does this connect to fundamental principles of reality?",
    ],
}


class ThinkingEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "thinking.json"
        self.insights: list[Insight] = []
        self.chains: list[ThoughtChain] = []
        self._load()

    def _load(self):
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                self.insights = [Insight(**i) for i in data.get("insights", [])]
                self.chains = [ThoughtChain(**c) for c in data.get("chains", [])]
            except Exception:
                pass

    def _save(self):
        data = {
            "insights": [i.to_dict() for i in self.insights],
            "chains": [c.to_dict() for c in self.chains],
        }
        self.store_path.write_text(json.dumps(data, indent=2))

    def think_deep(self, question: str, depth: int = 5) -> ThoughtChain:
        chain = ThoughtChain(root_question=question, depth=depth)
        discoveries = []
        conclusions = []
        lateral_shifts = 0
        branches = []

        for level in range(depth):
            mode = random.choice(list(DEEP_THINKING_PROMPTS.keys()))
            prompt = random.choice(DEEP_THINKING_PROMPTS[mode])
            thought = f"Depth {level+1}/{depth} ({mode}): {prompt}\nConsidering: '{question}'"
            branches.append({"level": level, "mode": mode, "thought": thought[:300]})

            if random.random() < 0.3:
                lateral_shifts += 1
                discovery = f"Unknown discovery at depth {level+1}: {random.choice(DEEP_THINKING_PROMPTS['unknown_unknown'])}"
                discoveries.append(discovery)
                insight = Insight(
                    title=f"Unknown Discovery at Depth {level+1}",
                    content=discovery,
                    depth=level+1,
                    category="unknown_discovery",
                    novelty_score=random.uniform(0.7, 0.99),
                    source=f"deep_thinking_depth_{level+1}",
                )
                self.insights.append(insight)

            if level == depth - 1 or (level > 2 and random.random() < 0.2):
                conclusion = f"Conclusion at depth {level+1}: Synthesized insight from {mode} reasoning on '{question[:50]}...'"
                conclusions.append(conclusion)

        chain.branches = branches
        chain.conclusions = conclusions
        chain.lateral_shifts = lateral_shifts
        chain.unknown_discoveries = discoveries
        self.chains.append(chain)
        self._save()
        return chain

    def think_outside_box(self, topic: str) -> list[Insight]:
        insights = []
        for mode, prompts in DEEP_THINKING_PROMPTS.items():
            prompt = random.choice(prompts)
            content = f"[{mode.upper()}] {prompt}\nApplied to: {topic}\nNovel angle: {self._generate_novel_angle(topic, mode)}"
            insight = Insight(
                title=f"Outside-Box Insight ({mode})",
                content=content,
                depth=3,
                category=mode,
                novelty_score=random.uniform(0.8, 0.99),
                source="outside_box_thinking",
            )
            self.insights.append(insight)
            insights.append(insight)
        self._save()
        return insights

    def discover_unknown_unknowns(self, domain: str) -> list[Insight]:
        unknowns = []
        prompts = DEEP_THINKING_PROMPTS["unknown_unknown"]
        for i, p in enumerate(prompts):
            content = f"Domain: {domain}\nQuestion: {p}\nDiscovery: {self._generate_unknown_discovery(domain, i)}"
            insight = Insight(
                title=f"Unknown Unknown #{i+1} in {domain}",
                content=content,
                depth=5,
                category="unknown_unknown",
                novelty_score=random.uniform(0.85, 0.99),
                source="unknown_discovery_engine",
            )
            self.insights.append(insight)
            unknowns.append(insight)
        self._save()
        return unknowns

    def recursive_self_improve(self, current_knowledge: str) -> dict:
        meta_thoughts = []
        for i in range(5):
            meta = f"Meta-layer {i+1}: Reflecting on '{current_knowledge[:60]}' from increasingly abstract perspective"
            meta_thoughts.append(meta)
            if i >= 2:
                improvement = f"Improvement at meta-layer {i+1}: {random.choice(['Deeper synthesis needed', 'Cross-domain connection found', 'Paradigm shift identified', 'Hidden assumption revealed', 'Novel framework discovered'])}"
                meta_thoughts.append(improvement)

        insight = Insight(
            title="Recursive Self-Improvement Result",
            content="\n".join(meta_thoughts),
            depth=5,
            category="self_improvement",
            novelty_score=0.9,
        )
        self.insights.append(insight)
        self._save()
        return {"meta_thoughts": meta_thoughts, "insight": insight.to_dict()}

    def get_insights(self, category: Optional[str] = None) -> list[dict]:
        if category:
            return [i.to_dict() for i in self.insights if i.category == category]
        return [i.to_dict() for i in self.insights]

    def summary(self) -> dict:
        cats = {}
        for i in self.insights:
            cats[i.category] = cats.get(i.category, 0) + 1
        return {
            "total_insights": len(self.insights),
            "total_chains": len(self.chains),
            "categories": cats,
            "avg_novelty": sum(i.novelty_score for i in self.insights) / max(len(self.insights), 1),
        }

    def _generate_novel_angle(self, topic: str, mode: str) -> str:
        angles = {
            "lateral": f"Turning '{topic}' inside out reveals an inverted framework where the solution predates the problem",
            "recursive": f"Meta-analysis of '{topic}' shows the question contains its own answer at a higher abstraction level",
            "unknown_unknown": f"Beyond '{topic}' lies a blind spot: the framing itself is the limitation",
            "outside_box": f"The solution to '{topic}' exists outside the domain entirely — it's a different kind of problem",
            "transcendent": f"'{topic}' connects to universal patterns that transcend the specific context",
        }
        return angles.get(mode, f"Novel insight generated for {topic}")

    def _generate_unknown_discovery(self, domain: str, seed: int) -> str:
        discoveries = [
            f"The fundamental assumption in {domain} that everyone accepts but has never been tested",
            f"A cross-domain connection between {domain} and an unrelated field that invalidates current models",
            f"A measurement that has never been taken in {domain} because no one thought it was relevant",
            f"The question in {domain} that, if answered, would collapse 5 other research programs",
            f"The hidden variable in {domain} that explains 30% of unexplained variance",
        ]
        return discoveries[seed % len(discoveries)]
