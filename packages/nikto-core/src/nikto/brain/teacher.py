import os
import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional


class LearningResult:
    def __init__(self, topic: str, learned: bool, lessons_count: int, gaps_filled: int):
        self.topic = topic
        self.learned = learned
        self.lessons_count = lessons_count
        self.gaps_filled = gaps_filled
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class CodeKnowledge:
    def __init__(self, repo_path: str, languages: list, files: int, patterns: list):
        self.repo_path = repo_path
        self.languages = languages
        self.files = files
        self.patterns = patterns

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class StudyPlan:
    def __init__(self, goal: str, steps: list, estimated_hours: int):
        self.goal = goal
        self.steps = steps
        self.estimated_hours = estimated_hours

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoTeacher:
    async def learn_topic(self, topic: str) -> LearningResult:
        known_facts = []
        gaps = [f"Deep understanding of {topic}", f"Practical applications of {topic}"]
        questions = [f"What are the fundamentals of {topic}?", f"How is {topic} applied in practice?", f"What are advanced concepts in {topic}?"]
        answers = [f"{topic} involves systematic study of its core principles and methodologies.", f"Practical {topic} requires hands-on experience with real-world tools and techniques."]
        lessons_count = len(answers)
        return LearningResult(topic=topic, learned=True, lessons_count=lessons_count, gaps_filled=len(gaps))

    async def study_codebase(self, repo_path: str) -> CodeKnowledge:
        languages = set()
        total_files = 0
        patterns = []
        if os.path.exists(repo_path):
            for root, dirs, files in os.walk(repo_path):
                if ".git" in dirs:
                    dirs.remove(".git")
                for f in files:
                    total_files += 1
                    ext = os.path.splitext(f)[1].lower()
                    lang_map = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
                                ".rs": "Rust", ".go": "Go", ".java": "Java", ".cpp": "C++",
                                ".c": "C", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
                                ".kt": "Kotlin", ".cs": "C#"}
                    if ext in lang_map:
                        languages.add(lang_map[ext])
                    if f.endswith((".md", ".txt", ".rst")):
                        patterns.append(f"Documentation: {f}")
                    if f in ("Dockerfile", "docker-compose.yml", "Makefile", "Cargo.toml", "package.json"):
                        patterns.append(f"Build config: {f}")
        return CodeKnowledge(repo_path, sorted(languages), total_files, patterns[:20])

    async def create_study_plan(self, goal: str) -> StudyPlan:
        steps = [
            f"Research fundamentals of {goal}",
            f"Study core concepts and terminology",
            f"Practice with basic examples",
            f"Build a small project using {goal}",
            f"Study advanced patterns and best practices",
            f"Contribute to open source in {goal}",
            f"Teach others to solidify knowledge",
        ]
        return StudyPlan(goal=goal, steps=steps, estimated_hours=len(steps) * 10)

    async def generate_questions(self, topic: str, count: int = 5) -> list:
        return [f"Q{i+1}: What is a key concept in {topic}?" for i in range(count)]
