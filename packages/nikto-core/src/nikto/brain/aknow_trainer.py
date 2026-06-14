"""AKNOW# Seed Reinforcement Trainer

Trains the brain to use AKNOW# seed expansion as its primary knowledge source.
Maintains a cache of question->seed mappings that produce high-quality output.
Reinforces successful seeds and deprecates low-quality ones.
"""
import json
import os
import time
from typing import Dict, List, Optional, Tuple

DEFAULT_TRAINER_PATH = os.path.join(os.path.expanduser("~"), ".nikto", "aknow_seed_cache.json")


class SeedRecord:
    __slots__ = ("question", "seed", "domain", "quality_score", "hit_count", "miss_count", "last_used", "word_count")

    def __init__(self, question: str, seed: int, domain: str = "general"):
        self.question = question
        self.seed = seed
        self.domain = domain
        self.quality_score = 0.5
        self.hit_count = 0
        self.miss_count = 0
        self.last_used = 0.0
        self.word_count = 0

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "seed": self.seed,
            "domain": self.domain,
            "quality_score": self.quality_score,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "last_used": self.last_used,
            "word_count": self.word_count,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SeedRecord":
        r = cls(d["question"], d["seed"], d.get("domain", "general"))
        r.quality_score = d.get("quality_score", 0.5)
        r.hit_count = d.get("hit_count", 0)
        r.miss_count = d.get("miss_count", 0)
        r.last_used = d.get("last_used", 0.0)
        r.word_count = d.get("word_count", 0)
        return r


class AknowSeedTrainer:
    def __init__(self, cache_path: str = None):
        self._cache_path = cache_path or DEFAULT_TRAINER_PATH
        self._seeds: Dict[int, SeedRecord] = {}
        self._question_map: Dict[str, int] = {}
        self._domain_stats: Dict[str, Dict] = {}
        self._training_count = 0
        self._os = os
        self._load()

    # ---- public API ----

    def train_on_question(self, question: str, seed: int, domain: str = "general",
                          output_text: str = "", feedback: float = None) -> SeedRecord:
        record = self._seeds.get(seed)
        if record is None:
            record = SeedRecord(question, seed, domain)
            self._seeds[seed] = record
            self._question_map[question.lower().strip()] = seed

        record.last_used = time.time()
        record.question = question
        record.domain = domain
        record.word_count = len(output_text.split())

        quality = feedback if feedback is not None else self._evaluate_quality(output_text)
        record.quality_score = (record.quality_score * record.hit_count + quality) / (record.hit_count + 1)

        if quality >= 0.4:
            record.hit_count += 1
        else:
            record.miss_count += 1

        self._update_domain_stats(domain, quality)
        self._training_count += 1
        return record

    def find_best_seed(self, question: str, domain: str = "general") -> Optional[int]:
        q_lower = question.lower().strip()
        if q_lower in self._question_map:
            seed = self._question_map[q_lower]
            record = self._seeds.get(seed)
            if record and record.quality_score >= 0.3:
                return seed

        domain_seeds = [s for s, r in self._seeds.items()
                        if r.domain == domain and r.quality_score >= 0.3]
        if domain_seeds:
            best = max(domain_seeds, key=lambda s: self._seeds[s].quality_score)
            return best

        return None

    def get_quality(self, seed: int) -> float:
        record = self._seeds.get(seed)
        return record.quality_score if record else 0.0

    def get_best_seed_for_domain(self, domain: str) -> Optional[int]:
        domain_seeds = [s for s, r in self._seeds.items()
                        if r.domain == domain and r.quality_score >= 0.3]
        if domain_seeds:
            return max(domain_seeds, key=lambda s: self._seeds[s].quality_score)
        return None

    def get_recommended_seed(self, question: str, fact_seed: Optional[int] = None) -> int:
        domain = "general"
        q_lower = question.lower().strip()

        if q_lower in self._question_map:
            seed = self._question_map[q_lower]
            record = self._seeds.get(seed)
            if record and record.quality_score >= 0.4:
                return seed

        if fact_seed is not None:
            if fact_seed in self._seeds:
                record = self._seeds[fact_seed]
                record.hit_count += 1
                record.last_used = time.time()
                return fact_seed
            self._seeds[fact_seed] = SeedRecord(question, fact_seed, domain)
            self._question_map[q_lower] = fact_seed
            return fact_seed

        return fact_seed if fact_seed is not None else hash(question) & ((1 << 64) - 1)

    def reinforce(self, seed: int, quality: float):
        record = self._seeds.get(seed)
        if record:
            record.quality_score = (record.quality_score * record.hit_count + quality) / (record.hit_count + 1)
            record.hit_count += 1
            record.last_used = time.time()

    def get_stats(self) -> Dict:
        return {
            "total_trained_seeds": len(self._seeds),
            "training_runs": self._training_count,
            "domains": list(self._domain_stats.keys()),
            "avg_quality": sum(r.quality_score for r in self._seeds.values()) / max(len(self._seeds), 1),
            "high_quality_seeds": sum(1 for r in self._seeds.values() if r.quality_score >= 0.7),
        }

    # ---- internals ----

    def _evaluate_quality(self, text: str) -> float:
        if not text or len(text.strip()) < 10:
            return 0.0
        words = text.split()
        word_count = len(words)
        if word_count < 5:
            return 0.1
        if word_count < 20:
            return 0.3
        if word_count < 50:
            return 0.5
        if word_count < 100:
            return 0.7
        if word_count < 200:
            return 0.85
        return 1.0

    def _update_domain_stats(self, domain: str, quality: float):
        if domain not in self._domain_stats:
            self._domain_stats[domain] = {"count": 0, "total_quality": 0.0, "best_quality": 0.0}
        s = self._domain_stats[domain]
        s["count"] += 1
        s["total_quality"] += quality
        if quality > s["best_quality"]:
            s["best_quality"] = quality

    # ---- persistence ----

    def _load(self):
        try:
            if self._os.path.exists(self._cache_path):
                with open(self._cache_path, "r") as f:
                    data = json.load(f)
                for entry in data.get("seeds", []):
                    record = SeedRecord.from_dict(entry)
                    self._seeds[record.seed] = record
                    self._question_map[record.question.lower().strip()] = record.seed
                for domain, stats in data.get("domain_stats", {}).items():
                    self._domain_stats[domain] = stats
                self._training_count = data.get("training_count", 0)
        except (json.JSONDecodeError, IOError, KeyError):
            pass

    def save(self):
        try:
            os.makedirs(os.path.dirname(self._cache_path), exist_ok=True)
            data = {
                "seeds": [r.to_dict() for r in self._seeds.values()],
                "domain_stats": self._domain_stats,
                "training_count": self._training_count,
            }
            with open(self._cache_path, "w") as f:
                json.dump(data, f, indent=2)
        except (IOError, OSError):
            pass
