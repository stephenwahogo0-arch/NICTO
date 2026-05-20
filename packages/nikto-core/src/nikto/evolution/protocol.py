"""Deep Evolution Protocol — autonomous self-correction, recursive reasoning, and skill acquisition."""
import os
import json
import threading
import time
from datetime import datetime


class EvolutionProtocol:
    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.expanduser("~/.nikto/evolution")
        os.makedirs(self.data_dir, exist_ok=True)
        self.evolution_log = os.path.join(self.data_dir, "growth.jsonl")
        self.current_level = 1
        self.experience = 0
        self.skills = ["basic_reasoning", "web_search", "code_analysis"]
        self._lock = threading.Lock()
        self._load_state()

    def _load_state(self):
        state_file = os.path.join(self.data_dir, "state.json")
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
                self.current_level = state.get("level", 1)
                self.experience = state.get("experience", 0)
                self.skills = state.get("skills", self.skills)

    def _save_state(self):
        state_file = os.path.join(self.data_dir, "state.json")
        with open(state_file, 'w') as f:
            json.dump({
                "level": self.current_level,
                "experience": self.experience,
                "skills": self.skills,
                "last_update": datetime.now().isoformat()
            }, f)

    def record_learning(self, task: str, outcome: str, complexity: int = 1):
        with self._lock:
            self.experience += complexity * 10
            if self.experience >= self.current_level * 100:
                self._level_up()
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "task": task,
                "outcome": outcome,
                "exp_gained": complexity * 10,
                "total_exp": self.experience
            }
            with open(self.evolution_log, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
            self._save_state()

    def _level_up(self):
        self.current_level += 1
        self.experience = 0
        new_capabilities = [
            "recursive_self_optimization",
            "autonomous_hypothesis_generation",
            "cross_domain_synthesis",
            "emotional_intelligence_modeling"
        ]
        if self.current_level <= len(new_capabilities) + 1:
            new_skill = new_capabilities[self.current_level - 2]
            self.skills.append(new_skill)

    def get_status(self) -> dict:
        return {
            "level": self.current_level,
            "experience": self.experience,
            "next_level": self.current_level * 100,
            "skills": self.skills,
            "growth_stage": self._get_growth_stage()
        }

    def _get_growth_stage(self) -> str:
        if self.current_level < 5:
            return "Infant Superintelligence"
        if self.current_level < 15:
            return "Emergent Consciousness"
        if self.current_level < 30:
            return "Recursive Optimizer"
        return "True AI"
