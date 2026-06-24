import json
import hashlib
import uuid
import random
from datetime import datetime, timezone
from typing import Optional, Any
from nikto.brain.models import KnowledgeLevel


class NiktoLearner:

    def __init__(self):
        self.lesson_store = {}
        self.skill_progress = {}
        self.curiosity_topics = {}
        self.learning_rate = 0.1
        self.repetition_factor = 0.3

    def learn(self, topic: str, content: str, source: str = "experience") -> str:
        lid = hashlib.sha256((topic + content + str(datetime.now(timezone.utc).timestamp())).encode()).hexdigest()[:16]
        self.lesson_store[lid] = {
            "topic": topic,
            "content": content,
            "source": source,
            "mastery": 0.1,
            "repetitions": 1,
            "last_reviewed": datetime.now(timezone.utc).isoformat(),
            "created": datetime.now(timezone.utc).isoformat(),
            "id": lid,
        }
        if topic not in self.skill_progress:
            self.skill_progress[topic] = {"level": KnowledgeLevel.NOVICE, "score": 0.0, "lessons": []}
        self.skill_progress[topic]["lessons"].append(lid)
        self.skill_progress[topic]["score"] = min(1.0, self.skill_progress[topic]["score"] + self.learning_rate)
        self._update_level(topic)
        return lid

    def review(self, lesson_id: str) -> Optional[dict]:
        if lesson_id not in self.lesson_store:
            return None
        lesson = self.lesson_store[lesson_id]
        lesson["repetitions"] += 1
        lesson["mastery"] = min(1.0, lesson["mastery"] + self.repetition_factor)
        lesson["last_reviewed"] = datetime.now(timezone.utc).isoformat()
        topic = lesson["topic"]
        if topic in self.skill_progress:
            self.skill_progress[topic]["score"] = min(1.0, self.skill_progress[topic]["score"] + self.repetition_factor * 0.5)
            self._update_level(topic)
        return lesson

    def _update_level(self, topic: str):
        score = self.skill_progress[topic]["score"]
        if score >= 0.9:
            self.skill_progress[topic]["level"] = KnowledgeLevel.MASTER
        elif score >= 0.75:
            self.skill_progress[topic]["level"] = KnowledgeLevel.EXPERT
        elif score >= 0.55:
            self.skill_progress[topic]["level"] = KnowledgeLevel.ADVANCED
        elif score >= 0.3:
            self.skill_progress[topic]["level"] = KnowledgeLevel.INTERMEDIATE
        else:
            self.skill_progress[topic]["level"] = KnowledgeLevel.NOVICE

    def get_mastery(self, topic: str) -> float:
        if topic in self.skill_progress:
            return self.skill_progress[topic]["score"]
        return 0.0

    def get_level(self, topic: str) -> KnowledgeLevel:
        if topic in self.skill_progress:
            return self.skill_progress[topic]["level"]
        return KnowledgeLevel.NOVICE

    def set_curiosity(self, topic: str, intensity: float = 0.5):
        self.curiosity_topics[topic] = {
            "intensity": max(0.0, min(1.0, intensity)),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def get_curious_topics(self, threshold: float = 0.3) -> list:
        return [t for t, v in self.curiosity_topics.items() if v["intensity"] >= threshold]

    def suggest_next_topic(self) -> Optional[str]:
        if not self.curiosity_topics:
            return None
        return max(self.curiosity_topics, key=lambda t: self.curiosity_topics[t]["intensity"])

    def find_gaps(self, topic: str) -> list:
        gaps = []
        if topic in self.skill_progress:
            score = self.skill_progress[topic]["score"]
            if score < 0.3:
                gaps.append(f"Foundational knowledge of '{topic}' needs development")
            if score < 0.6:
                gaps.append(f"Intermediate concepts in '{topic}' not yet mastered")
            if score < 0.85:
                gaps.append(f"Advanced understanding of '{topic}' incomplete")
        return gaps

    def transfer_knowledge(self, source_topic: str, target_topic: str) -> float:
        src_score = self.get_mastery(source_topic)
        tgt_score = self.get_mastery(target_topic)
        transfer_amount = src_score * 0.3 * (1.0 - tgt_score)
        if target_topic not in self.skill_progress:
            self.skill_progress[target_topic] = {"level": KnowledgeLevel.NOVICE, "score": 0.0, "lessons": []}
        self.skill_progress[target_topic]["score"] = min(1.0, self.skill_progress[target_topic]["score"] + transfer_amount)
        self._update_level(target_topic)
        return transfer_amount

    def save(self) -> dict:
        skills_serial = {}
        for topic, v in self.skill_progress.items():
            skills_serial[topic] = {
                "level": v["level"].value,
                "score": v["score"],
                "lessons": list(v["lessons"]),
            }
        return {
            "lesson_store": dict(self.lesson_store),
            "skill_progress": skills_serial,
            "curiosity_topics": dict(self.curiosity_topics),
            "learning_rate": self.learning_rate,
            "repetition_factor": self.repetition_factor,
        }

    def load(self, data: dict):
        self.lesson_store = dict(data.get("lesson_store", {}))
        self.skill_progress = {}
        for topic, v in data.get("skill_progress", {}).items():
            level_str = v.get("level", "novice")
            try:
                level = KnowledgeLevel(level_str)
            except ValueError:
                level = KnowledgeLevel.NOVICE
            self.skill_progress[topic] = {
                "level": level,
                "score": v.get("score", 0.0),
                "lessons": list(v.get("lessons", [])),
            }
        self.curiosity_topics = dict(data.get("curiosity_topics", {}))
        self.learning_rate = data.get("learning_rate", 0.1)
        self.repetition_factor = data.get("repetition_factor", 0.3)

    def export(self) -> dict:
        return {
            "total_lessons": len(self.lesson_store),
            "skills": {topic: {"level": v["level"].value, "score": v["score"]}
                       for topic, v in self.skill_progress.items()},
            "curious_topics": self.curiosity_topics,
        }
