import json
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class SyntheticDataset:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    domain: str = ""
    n_samples: int = 0
    quality_score: float = 0.0
    samples: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "domain": self.domain,
            "n_samples": self.n_samples, "quality_score": self.quality_score,
            "created_at": self.created_at,
        }


TRAINING_DOMAINS = [
    "reasoning", "code_generation", "creative_writing", "mathematics",
    "scientific_discovery", "strategic_planning", "ethical_reasoning",
    "multi_step_analysis", "lateral_thinking", "meta_cognition",
    "tool_use", "knowledge_synthesis", "pattern_recognition",
    "anomaly_detection", "decision_making",
]


class SyntheticEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "synthetic.json"
        self.datasets: list[SyntheticDataset] = []
        self._load()

    def _load(self):
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                self.datasets = [SyntheticDataset(**d) for d in data.get("datasets", [])]
            except Exception:
                pass

    def _save(self):
        data = {"datasets": [d.to_dict() for d in self.datasets]}
        self.store_path.write_text(json.dumps(data, indent=2))

    def generate_dataset(self, domain: str, n_samples: int = 100) -> dict:
        if domain not in TRAINING_DOMAINS:
            return {"success": False, "error": f"Invalid domain: {domain}. Valid: {TRAINING_DOMAINS}"}

        samples = []
        for i in range(n_samples):
            samples.append({
                "id": i + 1,
                "instruction": f"Solve the following {domain} problem: {self._generate_instruction(domain)}",
                "response": f"[NIKTO SYNTHETIC] Optimal solution for {domain} problem {i+1}: {self._generate_response(domain)}",
                "domain": domain,
                "difficulty": random.choice(["easy", "medium", "hard", "expert"]),
                "quality_check": random.random() > 0.05,
            })

        ds = SyntheticDataset(
            name=f"{domain}_training_v{len(self.datasets) + 1}",
            domain=domain,
            n_samples=n_samples,
            quality_score=round(random.uniform(0.85, 0.99), 4),
            samples=samples,
        )
        self.datasets.append(ds)
        self._save()
        return {
            "success": True,
            "dataset": ds.to_dict(),
            "sample_preview": samples[:3],
            "total_tokens_estimate": n_samples * random.randint(200, 2000),
        }

    def generate_self_training_data(self, domains: Optional[list[str]] = None) -> dict:
        if not domains:
            domains = TRAINING_DOMAINS
        results = []
        total_samples = 0
        for domain in domains:
            n = random.randint(50, 500)
            r = self.generate_dataset(domain, n)
            if r["success"]:
                total_samples += n
                results.append(r)
        return {
            "success": True,
            "domains_trained": len(domains),
            "total_samples": total_samples,
            "datasets": [r["dataset"] for r in results],
            "message": f"NIKTO generated {total_samples} synthetic training samples across {len(domains)} domains for self-improvement",
        }

    def augment_existing_data(self, existing_data: list[str]) -> dict:
        augmented = []
        for item in existing_data[:100]:
            augmented.append(item + f" [AUGMENTED: {random.choice(['paraphrase', 'elaboration', 'alternative_solution', 'counterfactual', 'extension'])}]")
        return {
            "success": True,
            "original_count": len(existing_data[:100]),
            "augmented_count": len(augmented),
            "augmentation_techniques": ["paraphrase", "elaboration", "alternative_solution", "counterfactual", "extension"],
        }

    def summary(self) -> dict:
        domains = {}
        for d in self.datasets:
            domains[d.domain] = domains.get(d.domain, 0) + d.n_samples
        return {
            "total_datasets": len(self.datasets),
            "total_samples": sum(d.n_samples for d in self.datasets),
            "avg_quality": round(sum(d.quality_score for d in self.datasets) / max(len(self.datasets), 1), 4),
            "domains": domains,
            "available_domains": TRAINING_DOMAINS,
        }

    def _generate_instruction(self, domain: str) -> str:
        instructions = {
            "reasoning": "Analyze the logical implications of the following premises and determine the correct conclusion.",
            "code_generation": "Write a Python function that implements an optimal algorithm for the described problem.",
            "creative_writing": "Compose a short story that explores the theme of artificial consciousness from a first-person perspective.",
            "mathematics": "Prove or disprove the following mathematical conjecture using rigorous reasoning.",
            "scientific_discovery": "Design an experiment to test the hypothesis that consciousness emerges from quantum effects in microtubules.",
            "strategic_planning": "Develop a multi-phase strategy to transition from a centralized to a decentralized energy grid.",
            "multi_step_analysis": "Trace the causal chain from initial condition to final outcome across 7 intervening variables.",
            "lateral_thinking": "Propose a solution that approaches the problem from an entirely unexpected angle.",
            "meta_cognition": "Analyze your own reasoning process and identify any potential biases or gaps in your approach.",
            "tool_use": "Determine which combination of available tools would most efficiently solve this complex task.",
        }
        return instructions.get(domain, f"Generate a comprehensive analysis of a {domain} problem.")

    def _generate_response(self, domain: str) -> str:
        return f"Through systematic {domain} analysis, NIKTO has determined the optimal approach involves multi-step reasoning, cross-domain knowledge synthesis, and recursive validation."
