"""AI Optimization Engine — performance analysis, FPS tuning, memory optimization."""

from __future__ import annotations
from typing import Any, Optional

from nicto_game.core.config import GameConfig, GraphicsQuality


class OptimizationEngine:
    """Analyzes and optimizes game performance across all subsystems."""

    def __init__(self):
        self.optimizations_applied: list[dict[str, Any]] = []

    async def analyze(self, source_code: str, config: GameConfig) -> dict[str, Any]:
        lines = source_code.split("\n")
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        loc = len(code_lines)

        analysis: dict[str, Any] = {
            "lines_of_code": loc,
            "quality": self._calculate_quality(source_code, config),
            "bottlenecks": self._find_bottlenecks(source_code),
            "recommendations": [],
            "estimated_fps": self._estimate_fps(source_code, config),
            "memory_estimate_mb": self._estimate_memory(source_code),
        }

        analysis["recommendations"] = self._generate_recommendations(analysis, config)
        return analysis

    def _calculate_quality(self, source: str, config: GameConfig) -> dict[str, Any]:
        has_type_hints = ": int" in source or ": float" in source or ": str" in source
        has_docstrings = '"""' in source
        has_error_handling = "try:" in source and "except" in source
        has_main_guard = 'if __name__ == "__main__"' in source

        score = 50
        if has_type_hints:
            score += 10
        if has_docstrings:
            score += 10
        if has_error_handling:
            score += 15
        if has_main_guard:
            score += 15

        return {
            "score": score,
            "has_type_hints": has_type_hints,
            "has_docstrings": has_docstrings,
            "has_error_handling": has_error_handling,
            "has_main_guard": has_main_guard,
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D",
        }

    def _find_bottlenecks(self, source: str) -> list[dict[str, str]]:
        bottlenecks = []

        if "for " in source and source.count("for ") > 20:
            bottlenecks.append({
                "type": "loop_heavy",
                "message": "High loop count detected - consider vectorization",
            })
        if "pygame.draw" in source and source.count("pygame.draw") > 50:
            bottlenecks.append({
                "type": "draw_calls",
                "message": "Many draw calls - consider batching or using surfaces",
            })
        if source.count("pygame.display.flip()") > 1 and "\n" + " " * 0 in source:
            pass
        if "load(" in source and source.count("load(") > 10:
            bottlenecks.append({
                "type": "asset_loading",
                "message": "Multiple asset loads detected - consider asset caching",
            })
        if "math.sqrt" in source or "**0.5" in source:
            if source.count("math.sqrt") + source.count("**0.5") > 100:
                bottlenecks.append({
                    "type": "math_heavy",
                    "message": "Heavy math operations - consider approximations or lookup tables",
                })
        return bottlenecks

    def _estimate_fps(self, source: str, config: GameConfig) -> int:
        base_fps = 60
        if "raycast" in source.lower():
            base_fps -= 10
        if config.graphics.quality == GraphicsQuality.ULTRA:
            base_fps -= 15
        elif config.graphics.quality == GraphicsQuality.CINEMATIC:
            base_fps -= 25
        if config.graphics.particles:
            base_fps -= 5
        if config.graphics.shadows:
            base_fps -= 5
        if "opengl" in source.lower() or "glBegin" in source:
            base_fps += 15
        if len(source.split("\n")) > 500:
            base_fps -= 10
        return max(15, base_fps)

    def _estimate_memory(self, source: str) -> float:
        mb = 50.0
        if "pygame.image.load" in source:
            mb += source.count("pygame.image.load") * 5
        if "Sound" in source:
            mb += 10
        if "pygame.display.set_mode" in source:
            mb += 16
        return round(mb, 1)

    def _generate_recommendations(self, analysis: dict[str, Any],
                                  config: GameConfig) -> list[dict[str, str]]:
        recs = []
        q = analysis["quality"]
        if q["score"] < 70:
            recs.append({
                "category": "code_quality",
                "action": "Add error handling and type hints",
                "impact": "medium",
            })
        for b in analysis.get("bottlenecks", []):
            recs.append({
                "category": "performance",
                "action": b["message"],
                "impact": "medium",
            })
        if config.optimization.enable_lod:
            recs.append({
                "category": "graphics",
                "action": "Level-of-detail enabled - good for performance",
                "impact": "positive",
            })
        if config.optimization.enable_culling:
            recs.append({
                "category": "graphics",
                "action": "Frustum culling enabled - reduces draw calls",
                "impact": "positive",
            })
        if config.graphics.post_processing and config.graphics.quality != GraphicsQuality.ULTRA:
            recs.append({
                "category": "graphics",
                "action": "Disable post-processing for higher FPS on this quality setting",
                "impact": "high",
            })
        return recs
