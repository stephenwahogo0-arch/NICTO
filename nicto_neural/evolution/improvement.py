import random
import time
from typing import Dict, List, Optional


class ImprovementEngine:
    def __init__(self, memory_manager=None):
        self.memory = memory_manager
        self.domains = ["general", "coding", "reasoning", "math", "language", "security", "knowledge"]

    def generate_tasks(self, reflections: List[Dict]) -> List[Dict]:
        tasks = []
        tasks.extend(self.generate_from_mistakes(reflections))
        if self.memory:
            all_reflections = self.memory.get_reflections(500)
            failed = [r for r in all_reflections if not r.get("was_successful", True)]
            tasks.extend(self.generate_from_mistakes(failed))
            corrections = self.memory.get_user_corrections(200)
            tasks.extend(self.generate_from_user_feedback(corrections))
        tasks.extend(self.generate_from_gaps([d for d in self.domains]))
        return self.prioritize_improvements(tasks)

    def generate_from_mistakes(self, mistake_reflections: List[Dict]) -> List[Dict]:
        tasks = []
        domain_count = {}
        for ref in mistake_reflections:
            domain = ref.get("task_domain", "general")
            domain_count[domain] = domain_count.get(domain, 0) + 1
            task = {
                "input": ref.get("task_input", ""),
                "expected": ref.get("expected", ""),
                "domain": domain,
                "difficulty": ref.get("difficulty", 1),
                "source_reflection": "mistake",
                "error_type": ref.get("error_type", "unknown"),
                "source_index": len(tasks),
            }
            if task["input"] and task["expected"]:
                tasks.append(task)
                if len(tasks) >= 200:
                    break
        if not tasks:
            for domain in self.domains:
                for i in range(3):
                    tasks.append({
                        "input": f"Improve {domain} understanding: example {i}",
                        "expected": f"Correct {domain} answer for example {i}",
                        "domain": domain,
                        "difficulty": 1,
                        "source_reflection": "generated_gap",
                        "error_type": "knowledge_gap",
                        "source_index": len(tasks),
                    })
        return tasks

    def generate_from_gaps(self, missing_knowledge: List[str]) -> List[Dict]:
        tasks = []
        for i, gap in enumerate(missing_knowledge[:50]):
            for j in range(2):
                tasks.append({
                    "input": f"Learn about {gap}: question {j}",
                    "expected": f"Knowledge about {gap} for question {j}",
                    "domain": gap if gap in self.domains else "general",
                    "difficulty": 1,
                    "source_reflection": "knowledge_gap",
                    "error_type": "missing_knowledge",
                    "source_index": i * 2 + j,
                })
        return tasks

    def generate_from_user_feedback(self, corrections: List[Dict]) -> List[Dict]:
        tasks = []
        for corr in corrections[:100]:
            task = {
                "input": corr.get("input", corr.get("original_input", "")),
                "expected": corr.get("corrected_output", corr.get("expected", "")),
                "domain": corr.get("domain", "general"),
                "difficulty": corr.get("difficulty", 1),
                "source_reflection": "user_correction",
                "error_type": "user_corrected",
                "source_index": len(tasks),
            }
            if task["input"] and task["expected"]:
                tasks.append(task)
        return tasks

    def prioritize_improvements(self, tasks: List[Dict]) -> List[Dict]:
        if not tasks:
            return []
        priority_order = []
        mistake_tasks = [t for t in tasks if t.get("source_reflection") == "mistake"]
        correction_tasks = [t for t in tasks if t.get("source_reflection") == "user_correction"]
        gap_tasks = [t for t in tasks if t.get("source_reflection") == "knowledge_gap"]
        generated_tasks = [t for t in tasks if t.get("source_reflection") == "generated_gap"]

        random.shuffle(mistake_tasks)
        random.shuffle(correction_tasks)
        random.shuffle(gap_tasks)
        random.shuffle(generated_tasks)

        priority_order.extend(mistake_tasks[:100])
        priority_order.extend(correction_tasks[:50])
        priority_order.extend(gap_tasks[:50])
        priority_order.extend(generated_tasks[:50])

        for t in priority_order:
            t.setdefault("_priority_rank", 0)
        for idx, t in enumerate(priority_order):
            t["_priority_rank"] = idx

        for t in priority_order:
            t["priority"] = max(1, 10 - t.get("_priority_rank", 0) // 25)

        return priority_order[:200]
