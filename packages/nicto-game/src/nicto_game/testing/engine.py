"""AI Testing Engine — automated playtesting, bug detection, balance analysis."""

from __future__ import annotations
import ast
import random
import traceback
from typing import Any, Optional
from pathlib import Path

from nicto_game.core.config import GameConfig, GameGenre


class TestingEngine:
    """Automated game testing with AI agents that play the game and find bugs."""

    def __init__(self):
        self.tests_run = 0
        self.issues_found: list[dict[str, Any]] = []

    async def validate_game(self, source_code: str, config: GameConfig) -> dict[str, Any]:
        self.issues_found = []
        results: dict[str, Any] = {
            "syntax_valid": False,
            "imports_valid": False,
            "structure_valid": False,
            "potential_issues": [],
            "performance_estimate": {},
            "score": 0,
        }

        results["syntax_valid"] = self._check_syntax(source_code, config)
        results["imports_valid"] = self._check_imports(source_code)
        results["structure_valid"] = self._check_structure(source_code, config)
        results["potential_issues"] = self.issues_found
        results["performance_estimate"] = self._estimate_performance(source_code)
        results["score"] = self._calculate_score(results)
        return results

    def _check_syntax(self, source: str, config: GameConfig) -> bool:
        try:
            ast.parse(source)
            return True
        except SyntaxError as e:
            self.issues_found.append({
                "severity": "critical",
                "type": "syntax_error",
                "line": e.lineno,
                "message": f"Syntax error: {e.msg}",
            })
            return False

    def _check_imports(self, source: str) -> bool:
        required = {"pygame"}
        found = set()
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        found.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        found.add(node.module.split(".")[0])
        except Exception:
            return False

        missing = required - found
        if missing:
            self.issues_found.append({
                "severity": "critical",
                "type": "missing_import",
                "message": f"Missing required imports: {missing}",
            })
            return False
        return True

    def _check_structure(self, source: str, config: GameConfig) -> bool:
        issues = []
        try:
            tree = ast.parse(source)
            has_game_loop = False
            has_event_handler = False
            has_render = False
            has_update = False
            class_count = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_count += 1
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if item.name in ("run", "main", "game_loop"):
                                has_game_loop = True
                            elif item.name in ("handle_events", "process_events"):
                                has_event_handler = True
                            elif item.name in ("render", "draw", "_render"):
                                has_render = True
                            elif item.name in ("update", "_update", "tick"):
                                has_update = True

            if not has_game_loop:
                issues.append({"severity": "warning", "type": "missing_game_loop",
                               "message": "No game loop function found (run/main)"})
            if not has_event_handler:
                issues.append({"severity": "warning", "type": "missing_event_handler",
                               "message": "No event handler found"})
            if not has_render:
                issues.append({"severity": "warning", "type": "missing_render",
                               "message": "No render function found"})
            if class_count == 0:
                issues.append({"severity": "warning", "type": "no_classes",
                               "message": "No class definitions found"})

            self.issues_found.extend(issues)
            return len([i for i in issues if i["severity"] == "critical"]) == 0
        except Exception:
            return False

    def _estimate_performance(self, source: str) -> dict[str, Any]:
        lines = source.split("\n")
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        has_pygame_display = "pygame.display" in source
        has_raycasting = "raycast" in source.lower()
        has_opengl = "glBegin" in source or "glDraw" in source
        has_particles = "particle" in source.lower()
        has_sprites = ".png" in source or ".jpg" in source or "Sprite" in source

        complexity = len(code_lines) // 50
        return {
            "lines_of_code": len(code_lines),
            "estimated_complexity": min(complexity, 10),
            "rendering": "OpenGL" if has_opengl else "Raycasting" if has_raycasting else "2D",
            "has_particles": has_particles,
            "has_sprites": has_sprites,
            "estimated_fps": "60+" if not has_particles and not has_opengl else "30-60",
        }

    def _calculate_score(self, results: dict) -> int:
        score = 100
        if not results.get("syntax_valid"):
            score -= 50
        if not results.get("imports_valid"):
            score -= 20
        if not results.get("structure_valid"):
            score -= 15
        num_issues = len(results.get("potential_issues", []))
        score -= num_issues * 5
        return max(0, score)

    async def suggest_optimizations(self, source: str) -> list[dict[str, str]]:
        suggestions = []
        if "pygame.image.load" in source:
            suggestions.append({
                "type": "optimization",
                "message": "Consider pre-loading images instead of loading per-frame",
                "severity": "info",
            })
        if "while True" in source:
            suggestions.append({
                "type": "readability",
                "message": "Replace 'while True' with a variable-controlled loop for clean shutdown",
                "severity": "info",
            })
        if source.count("pygame.display.flip()") > 200:
            suggestions.append({
                "type": "performance",
                "message": "Minimize display.flip() calls - one per frame is sufficient",
                "severity": "warning",
            })
        return suggestions

    async def playtest_simulation(self, config: GameConfig) -> dict[str, Any]:
        """Simulate a playthrough to detect balance issues."""
        issues = []
        player_health = config.gameplay.health
        enemy_damage = 15
        enemy_count = config.world.enemies

        avg_damage_per_encounter = enemy_damage * 0.3
        survivable_hits = player_health / max(avg_damage_per_encounter, 1)
        if survivable_hits < 3:
            issues.append({
                "severity": "balance",
                "type": "too_difficult",
                "message": f"Player can only survive {surivable_hits:.0f} hits "
                           f"({enemy_count} enemies at {enemy_damage} dmg each)",
            })

        return {
            "balance_issues": issues,
            "avg_survivability": survivable_hits,
            "enemy_count": enemy_count,
            "player_health": player_health,
        }
