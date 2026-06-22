import json
import random
from typing import Dict, List, Optional, Tuple


class DatasetBuilder:
    def __init__(self, memory_manager=None):
        self.memory = memory_manager

    def build(self, sources: List[str] = None, max_examples: int = 10000) -> List[Dict]:
        if sources is None:
            sources = ["conversations", "task_history", "reflections", "tool_outputs", "user_corrections"]
        dataset = []
        for source in sources:
            if source == "conversations" and self.memory:
                dataset.extend(self.from_conversations(max_examples // len(sources)))
            elif source == "task_history" and self.memory:
                dataset.extend(self.from_task_history(max_examples // len(sources)))
            elif source == "reflections" and self.memory:
                dataset.extend(self.from_reflections(max_examples // len(sources)))
            elif source == "tool_outputs" and self.memory:
                dataset.extend(self.from_tool_outputs(max_examples // len(sources)))
            elif source == "user_corrections" and self.memory:
                dataset.extend(self.from_user_corrections(max_examples // len(sources)))
        random.shuffle(dataset)
        return dataset[:max_examples]

    def from_conversations(self, limit: int = 1000) -> List[Dict]:
        if not self.memory:
            return []
        conversations = self.memory.get_conversations(limit)
        dataset = []
        for conv in conversations:
            entry = {
                "input": conv.get("input", conv.get("message", "")),
                "output": conv.get("output", conv.get("response", "")),
                "expected": conv.get("expected", conv.get("response", "")),
                "domain": conv.get("domain", "general"),
                "brain_used": conv.get("brain_used", "default"),
                "score": conv.get("score", 0.0),
                "metadata": {
                    "source": "conversation",
                    "timestamp": conv.get("_timestamp", 0),
                    "user_id": conv.get("user_id", "unknown"),
                },
            }
            if entry["input"]:
                dataset.append(entry)
        return dataset

    def from_task_history(self, limit: int = 1000) -> List[Dict]:
        if not self.memory:
            return []
        tasks = self.memory.get_task_history(limit)
        dataset = []
        for task in tasks:
            entry = {
                "input": task.get("input", task.get("task", "")),
                "output": task.get("output", task.get("result", "")),
                "expected": task.get("expected", ""),
                "domain": task.get("domain", "general"),
                "brain_used": task.get("brain_used", "default"),
                "score": task.get("score", task.get("accuracy", 0.0)),
                "metadata": {
                    "source": "task_history",
                    "timestamp": task.get("_timestamp", 0),
                    "task_type": task.get("type", "unknown"),
                },
            }
            if entry["input"]:
                dataset.append(entry)
        return dataset

    def from_reflections(self, limit: int = 1000) -> List[Dict]:
        if not self.memory:
            return []
        reflections = self.memory.get_reflections(limit)
        dataset = []
        for ref in reflections:
            entry = {
                "input": ref.get("task_input", ""),
                "output": str(ref.get("actual", "")),
                "expected": str(ref.get("expected", "")),
                "domain": ref.get("task_domain", "general"),
                "brain_used": ref.get("brain_used", "default"),
                "score": ref.get("score", 0.0),
                "metadata": {
                    "source": "reflection",
                    "timestamp": ref.get("timestamp", ref.get("_timestamp", 0)),
                    "was_successful": ref.get("was_successful", False),
                    "error_type": ref.get("error_type"),
                    "difficulty": ref.get("difficulty", 0),
                },
            }
            if entry["input"]:
                dataset.append(entry)
        return dataset

    def from_tool_outputs(self, limit: int = 1000) -> List[Dict]:
        if not self.memory:
            return []
        outputs = self.memory.get_tool_outputs(limit)
        dataset = []
        for out in outputs:
            entry = {
                "input": out.get("command", out.get("input", "")),
                "output": out.get("output", out.get("result", "")),
                "expected": out.get("expected", ""),
                "domain": out.get("domain", "tool"),
                "brain_used": out.get("brain_used", "tool"),
                "score": out.get("score", 1.0),
                "metadata": {
                    "source": "tool_output",
                    "timestamp": out.get("_timestamp", 0),
                    "tool": out.get("tool", "unknown"),
                    "exit_code": out.get("exit_code", 0),
                },
            }
            if entry["input"]:
                dataset.append(entry)
        return dataset

    def from_user_corrections(self, limit: int = 1000) -> List[Dict]:
        if not self.memory:
            return []
        corrections = self.memory.get_user_corrections(limit)
        dataset = []
        for corr in corrections:
            entry = {
                "input": corr.get("input", corr.get("original_input", "")),
                "output": corr.get("corrected_output", corr.get("output", "")),
                "expected": corr.get("expected", corr.get("corrected_output", "")),
                "domain": corr.get("domain", "general"),
                "brain_used": corr.get("brain_used", "default"),
                "score": corr.get("score", 1.0),
                "metadata": {
                    "source": "user_correction",
                    "timestamp": corr.get("_timestamp", 0),
                    "correction_type": corr.get("correction_type", "unknown"),
                },
            }
            if entry["input"]:
                dataset.append(entry)
        return dataset

    def generate_jsonl(self, dataset: List[Dict], path: str) -> None:
        with open(path, "w") as f:
            for entry in dataset:
                f.write(json.dumps(entry) + "\n")

    def train_val_split(self, dataset: List[Dict], val_ratio: float = 0.2) -> Tuple[List[Dict], List[Dict]]:
        shuffled = list(dataset)
        random.shuffle(shuffled)
        split = int(len(shuffled) * (1 - val_ratio))
        return shuffled[:split], shuffled[split:]

    def augment(self, dataset: List[Dict]) -> List[Dict]:
        augmented = []
        for example in dataset:
            augmented.append(example)
            inp = example.get("input", "")
            out = example.get("output", "")
            if not inp:
                continue
            if len(inp.split()) > 3:
                words = inp.split()
                reordered = list(words)
                random.shuffle(reordered)
                para1 = " ".join(reordered)
                augmented.append({
                    **example,
                    "input": para1,
                    "metadata": {**example.get("metadata", {}), "augmented": True, "aug_type": "shuffle"},
                })
            if len(inp) > 20:
                prefix = inp[:len(inp)//2]
                para2 = prefix + " " + inp
                augmented.append({
                    **example,
                    "input": para2,
                    "metadata": {**example.get("metadata", {}), "augmented": True, "aug_type": "prefix_duplicate"},
                })
            if out and len(out.split()) > 2:
                out_words = out.split()
                random.shuffle(out_words)
                para3 = " ".join(out_words)
                augmented.append({
                    **example,
                    "output": para3,
                    "expected": para3,
                    "metadata": {**example.get("metadata", {}), "augmented": True, "aug_type": "output_shuffle"},
                })
        return augmented
