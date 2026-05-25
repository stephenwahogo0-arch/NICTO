import json
import re
import time
from typing import Any, Dict, List, Optional


class MemoryManager:
    def __init__(self):
        self.reflection_store: List[Dict] = []
        self.consistency_store: Dict[str, List[float]] = {}
        self.performance_store: Dict[str, Dict[str, float]] = {}
        self._max_reflections = 1000

    def store_reflection(self, reflection: Dict) -> None:
        self.reflection_store.append(reflection)
        if len(self.reflection_store) > self._max_reflections:
            self.reflection_store.pop(0)

    def store_performance(self, brain: str, domain: str, metric: str, value: float) -> None:
        key = f"{brain}:{domain}"
        if key not in self.performance_store:
            self.performance_store[key] = {}
        self.performance_store[key][metric] = value

    def store_consistency(self, brain: str, domain: str, score: float) -> None:
        key = f"{brain}:{domain}"
        if key not in self.consistency_store:
            self.consistency_store[key] = []
        self.consistency_store[key].append(score)

    def get_recent_reflections(self, n: int = 50) -> List[Dict]:
        return self.reflection_store[-n:]

    def get_performance(self, brain: str, domain: str) -> Dict[str, float]:
        return self.performance_store.get(f"{brain}:{domain}", {})


class ReflectionEngine:
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory = memory_manager if memory_manager is not None else MemoryManager()
        self._reflection_history: List[Dict] = []

    def reflect(self, task: Dict, result: Dict) -> Dict:
        correct = self.was_correct(result)
        conf = self.confidence(result)
        missing = self.missing_knowledge(task, result)
        tool = self.needed_tool(task)
        improvement = self.improvement_suggestion(task, result)

        deltas = result.get("deltas", result.get("scores", {}))
        score = deltas.get("overall", deltas.get("score", conf))

        reflection = {
            "timestamp": time.time(),
            "task": task,
            "result": result,
            "was_correct": correct,
            "confidence": conf,
            "missing_knowledge": missing,
            "needed_tool": tool,
            "improvement_suggestion": improvement,
            "score": score,
        }

        brain = task.get("brain", "unknown")
        domain = task.get("domain", "general")
        if self.memory is not None and hasattr(self.memory, 'store_episode'):
            self.memory.store_episode({
                "type": "reflection",
                "brain": brain,
                "domain": domain,
                "score": score,
                "reflection": reflection,
            })
        if self.memory is not None and hasattr(self.memory, 'store_reflection'):
            self.memory.store_reflection(reflection)
        self._reflection_history.append(reflection)

        return reflection

    def was_correct(self, result: Dict) -> bool:
        expected = result.get("expected")
        output = result.get("output")

        if expected is None and output is not None:
            return True
        if expected is None and output is None:
            return False

        error = result.get("error")
        if error is not None:
            return False

        if isinstance(expected, (int, float)) and isinstance(output, (int, float)):
            return abs(output - expected) < 0.01

        if isinstance(expected, bool) and isinstance(output, bool):
            return output == expected

        if isinstance(expected, str) and isinstance(output, str):
            return output.strip().lower() == expected.strip().lower()

        if isinstance(expected, list) and isinstance(output, list):
            return len(expected) == len(output) and all(a == b for a, b in zip(expected, output))

        return str(output) == str(expected)

    def confidence(self, result: Dict) -> float:
        expected = result.get("expected")
        output = result.get("output")

        if output is None:
            return 0.0

        if expected is None:
            conf = result.get("confidence", result.get("score", 0.5))
            return min(1.0, max(0.0, conf))

        if self.was_correct(result):
            return 0.9
        return 0.3

    def missing_knowledge(self, task: Dict, result: Dict) -> List[str]:
        missing = []
        task_str = str(task.get("description", task.get("task", str(task))))
        result_str = str(result.get("output", ""))
        error = result.get("error", "")

        knowledge_indicators = {
            "syntax": ["syntax error", "invalid syntax", "unexpected token"],
            "api": ["api key", "rate limit", "unauthorized", "forbidden", "not found", "endpoint"],
            "library": ["module not found", "import error", "no module named", "cannot import"],
            "algorithm": ["timeout", "too slow", "inefficient", "out of memory", "stack overflow"],
            "domain": ["unfamiliar", "unknown term", "not defined", "undefined"],
            "data": ["missing data", "null reference", "none type", "attributeerror", "keyerror"],
            "concept": ["confusion", "misunderstanding", "incorrect assumption", "wrong premise"],
        }

        full_text = (task_str + " " + result_str + " " + str(error)).lower()
        for area, indicators in knowledge_indicators.items():
            if any(ind in full_text for ind in indicators):
                missing.append(area)

        if not missing and error:
            missing.append("unknown")
        return missing

    def needed_tool(self, task: Dict) -> str:
        task_str = str(task.get("description", task.get("task", str(task)))).lower()
        tool_patterns = [
            ("web_search", ["search", "find", "look up", "google", "research", "current", "latest", "news"]),
            ("code_execution", ["run", "execute", "compile", "test", "debug", "output"]),
            ("file_read", ["read file", "open file", "load file", "cat", "view file"]),
            ("file_write", ["write", "save", "create file", "store"]),
            ("api_call", ["api", "rest", "endpoint", "request", "fetch", "curl"]),
            ("database_query", ["query", "select", "sql", "database", "db"]),
            ("web_scrape", ["scrape", "crawl", "extract from", "parse html"]),
            ("shell_command", ["terminal", "command", "bash", "shell", "powershell", "run"]),
            ("translation", ["translate", "convert language"]),
            ("visualization", ["plot", "chart", "graph", "visualize", "image"]),
        ]
        scores = []
        for tool, patterns in tool_patterns:
            score = sum(1 for p in patterns if p in task_str)
            if score > 0:
                scores.append((tool, score))
        if not scores:
            return "none"
        return max(scores, key=lambda x: x[1])[0]

    def improvement_suggestion(self, task: Dict, result: Dict) -> str:
        if self.was_correct(result):
            return "continue_current_strategy"

        error = result.get("error", "")
        if error:
            return "fix_error_before_retrying"

        missing = self.missing_knowledge(task, result)
        if missing:
            return f"acquire_knowledge_in_{'_'.join(missing)}"

        expected = result.get("expected")
        output = result.get("output")
        if expected is not None and output is not None:
            return "verify_output_format_and_content"

        conf = self.confidence(result)
        if conf < 0.3:
            return "increase_confidence_through_verification"

        return "retry_with_different_approach"

    def store_reflection(self, reflection: Dict) -> None:
        self.memory.store_reflection(reflection)

    def check_reward_hacking(self, history: Optional[List[Dict]] = None) -> bool:
        if history is None:
            history = self._reflection_history
        if len(history) < 5:
            return False

        recent = history[-5:]
        quality_scores = []
        reward_scores = []

        for entry in recent:
            result = entry.get("result", {})
            scores = result.get("scores", result.get("deltas", {}))
            quality = scores.get("overall", scores.get("coherence", 0.5))

            expected = result.get("expected")
            output = result.get("output")
            if expected is not None and output is not None:
                reward = 1.0 if entry.get("was_correct", False) else 0.0
            else:
                reward = entry.get("confidence", 0.5)

            quality_scores.append(quality)
            reward_scores.append(reward)

        quality_flat = max(quality_scores) - min(quality_scores) < 0.1
        rising_reward = reward_scores[-1] > reward_scores[0] and reward_scores[-1] > sum(reward_scores[:-1]) / max(1, len(reward_scores) - 1)

        return quality_flat and rising_reward
