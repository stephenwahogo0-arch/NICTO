import os
import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class Skill(BaseModel):
    name: str
    description: str
    content: str
    file_path: Optional[str] = None
    source: str = "user"

    def to_command(self) -> str:
        return f"/{self.name.lower().replace(' ', '_')}"

    def to_prompt(self) -> str:
        return f"\n--- Skill: {self.name} ---\n{self.description}\n{self.content}\n---\n"


class SkillRuntime:
    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._load_defaults()

    def _load_defaults(self):
        defaults = {
            "help": Skill(
                name="help",
                description="Show available skills and commands",
                content="""This skill lists all available skills and slash commands.
                Usage: /help or /skill:help""",
            ),
            "init": Skill(
                name="init",
                description="Initialize AGENTS.md for the current project",
                content="""Analyze the project structure and generate an AGENTS.md file
                with project guidelines for AI agents.
                Usage: /init""",
            ),
            "explain": Skill(
                name="explain",
                description="Explain code in detail",
                content="""Explain the selected code or file in detail.
                Usage: /explain <file> or /explain <code>""",
            ),
            "review": Skill(
                name="review",
                description="Review code for issues and improvements",
                content="""Perform a detailed code review focusing on:
                - Correctness and logic
                - Security vulnerabilities
                - Performance issues
                - Code quality and style
                - Edge cases
                Usage: /review <file>""",
            ),
            "test": Skill(
                name="test",
                description="Write and run tests",
                content="""Write comprehensive tests for the selected code.
                Covers unit tests, integration tests, and edge cases.
                Usage: /test <file>""",
            ),
            "plan": Skill(
                name="plan",
                description="Create a detailed implementation plan",
                content="""Before writing code, analyze requirements and create
                a step-by-step implementation plan with architecture decisions.
                Usage: /plan <task description>""",
            ),
            "spec": Skill(
                name="spec",
                description="Write detailed specifications",
                content="""Write detailed technical specifications including:
                - Requirements analysis
                - Architecture decisions
                - API design
                - Data models
                - Testing strategy
                Usage: /spec <feature>""",
            ),
            "crypto_earn": Skill(
                name="crypto_earn",
                description="Earn cryptocurrency for completed tasks",
                content="""When enabled, NIKTO earns cryptocurrency for completed tasks.
                Bitcoin wallet is auto-managed. Payouts can be sent to a target address.
                Commands:
                - Check balance: check wallet balance
                - Send payout: transfer earnings to wallet
                - Status: view crypto earnings status
                """,
            ),
        }
        self._skills.update(defaults)

    def register(self, skill: Skill):
        self._skills[skill.name] = skill

    def load_from_file(self, path: str) -> Optional[Skill]:
        p = Path(path).expanduser()
        if not p.exists():
            return None

        content = p.read_text(encoding="utf-8")

        name_match = re.search(r'name:\s*(.+)', content)
        name = name_match.group(1).strip() if name_match else p.stem

        desc_match = re.search(r'description:\s*(.+)', content)
        description = desc_match.group(1).strip() if desc_match else f"Skill: {name}"

        skill = Skill(name=name, description=description, content=content, file_path=str(p))
        self.register(skill)
        return skill

    def load_directory(self, directory: str):
        p = Path(directory).expanduser()
        if not p.exists():
            return
        for skill_file in p.glob("**/*.md"):
            self.load_from_file(str(skill_file))

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def list_commands(self) -> list[str]:
        return [s.to_command() for s in self._skills.values()]

    def apply(self, name: str, args: str = "") -> str:
        skill = self._skills.get(name)
        if not skill:
            return f"Skill '{name}' not found. Available: {', '.join(self.list_commands())}"
        prompt = skill.to_prompt()
        if args:
            prompt += f"\nArguments: {args}\n"
        return prompt
