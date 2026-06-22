"""Real synthetic data engine — generates structured training data from templates."""
import json
import random
import time
from pathlib import Path
from typing import Optional


DOMAINS = ["python", "javascript", "math", "science", "history", "security", "networking", "database"]
ACTIONS = ["implement", "explain", "debug", "optimize", "refactor", "test", "document", "design"]


class SyntheticEngine:
    def __init__(self, output_dir: Optional[str] = None, agent=None):
        self.output_dir = Path(output_dir or "/tmp/nikto_synthetic")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.agent = agent

    def generate_dataset(self, n_samples: int = 10, domain: str = None) -> list:
        samples = []
        domain = domain or random.choice(DOMAINS)
        for i in range(n_samples):
            instruction = self._generate_instruction(domain)
            response = self._generate_response(domain, instruction)
            samples.append({"id": f"syn_{i}_{int(time.time())}", "domain": domain,
                            "instruction": instruction, "response": response})
        output_path = self.output_dir / f"dataset_{domain}_{int(time.time())}.json"
        output_path.write_text(json.dumps(samples, indent=2))
        return samples

    def _generate_instruction(self, domain: str) -> str:
        action = random.choice(ACTIONS)
        templates = {
            "python": [
                f"{action} a function that processes JSON data",
                f"{action} a REST API endpoint for user authentication",
                f"{action} a decorator that measures execution time",
                f"{action} a class for handling file I/O operations",
            ],
            "javascript": [
                f"{action} a React component for a todo list",
                f"{action} an async function that fetches API data",
                f"{action} a closure-based counter module",
            ],
            "math": [
                f"{action} the solution to a quadratic equation",
                f"{action} a proof for the Pythagorean theorem",
                f"{action} the derivative of f(x) = x^3 + 2x^2 - 5x + 1",
            ],
            "security": [
                f"{action} input sanitization for SQL injection prevention",
                f"{action} a password hashing utility using bcrypt",
                f"{action} CSRF protection middleware",
            ],
        }
        choices = templates.get(domain, [f"{action} a {domain} task"])
        return random.choice(choices)

    def _generate_response(self, domain: str, instruction: str) -> str:
        if self.agent and hasattr(self.agent, 'run_sync'):
            try:
                return self.agent.run_sync(f"Provide solution for: {instruction}")
            except Exception:
                pass
        return f"Solution for {instruction}: [Generated content for {domain} task]"
