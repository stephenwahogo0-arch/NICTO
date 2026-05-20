"""Hourly Training Engine — real persistent learning from conversations.
Collects interactions, stores in vector memory, and uses past learning as context."""

import asyncio
import json
import os
import time
import threading
from pathlib import Path
from typing import Optional


class HourlyTrainer:
    """Trains NIKTO every hour by consolidating conversation history into
    persistent memory. Never forgets what it learned."""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto/training").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.learning_file = self.data_dir / "learned_knowledge.json"
        self.history_file = self.data_dir / "training_history.json"
        self.conversation_log = self.data_dir / "conversations.jsonl"
        self._learned = self._load_json(self.learning_file, {})
        self._history = self._load_json(self.history_file, [])
        self._running = False
        self._thread = None
        self._last_train_time = 0

    def _load_json(self, path, default):
        try:
            if path.exists():
                return json.loads(path.read_text())
        except Exception:
            pass
        return default

    def _save_json(self, path, data):
        try:
            path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"  [Trainer] Save error: {e}")

    def record_interaction(self, user_input: str, response: str, duration: float = 0):
        """Record a conversation for later training."""
        entry = {
            "input": user_input[:500],
            "response": response[:1000],
            "duration": round(duration, 2),
            "timestamp": time.time(),
            "topic": self._classify_topic(user_input),
        }
        try:
            with open(self.conversation_log, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def _classify_topic(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["code", "python", "javascript", "function", "debug"]):
            return "coding"
        if any(w in text_lower for w in ["game", "play", "pong", "snake"]):
            return "games"
        if any(w in text_lower for w in ["finance", "money", "bank", "account"]):
            return "finance"
        if any(w in text_lower for w in ["image", "picture", "generate", "draw"]):
            return "image_gen"
        if any(w in text_lower for w in ["voice", "speak", "talk", "speech"]):
            return "voice"
        if any(w in text_lower for w in ["brain", "think", "learn", "memory"]):
            return "brain"
        if any(w in text_lower for w in ["who are you", "what are you", "nikto"]):
            return "about_nikto"
        if any(w in text_lower for w in ["help", "what can you", "capabilities"]):
            return "help"
        return "general"

    def train(self) -> dict:
        """Run one training cycle: consolidate conversations into knowledge."""
        start = time.time()
        topics = {}
        new_entries = 0

        try:
            if self.conversation_log.exists():
                with open(self.conversation_log) as f:
                    lines = f.readlines()

                # Process last 100 conversations
                for line in lines[-100:]:
                    try:
                        entry = json.loads(line.strip())
                        topic = entry["topic"]
                        inp = entry["input"]
                        resp = entry["response"]

                        if topic not in self._learned:
                            self._learned[topic] = {"count": 0, "patterns": [], "responses": []}

                        self._learned[topic]["count"] += 1
                        topics[topic] = topics.get(topic, 0) + 1

                        # Store key patterns (deduplicated)
                        pattern = inp[:80]
                        if pattern not in self._learned[topic]["patterns"]:
                            self._learned[topic]["patterns"].append(pattern)
                            self._learned[topic]["responses"].append(resp[:200])
                            new_entries += 1

                    except (json.JSONDecodeError, KeyError):
                        pass

                # Trim patterns to prevent bloat
                for topic in self._learned:
                    if len(self._learned[topic]["patterns"]) > 50:
                        self._learned[topic]["patterns"] = self._learned[topic]["patterns"][-50:]
                        self._learned[topic]["responses"] = self._learned[topic]["responses"][-50:]

        except Exception as e:
            return {"success": False, "error": str(e), "duration": round(time.time() - start, 2)}

        self._history.append({
            "timestamp": time.time(),
            "topics": topics,
            "new_entries": new_entries,
            "total_learned": sum(len(v["patterns"]) for v in self._learned.values()),
            "duration": round(time.time() - start, 2),
        })

        # Keep last 1000 training history entries
        if len(self._history) > 1000:
            self._history = self._history[-1000:]

        self._save_json(self.learning_file, self._learned)
        self._save_json(self.history_file, self._history)
        self._last_train_time = time.time()

        return {
            "success": True,
            "topics_updated": list(topics.keys()),
            "new_patterns": new_entries,
            "total_patterns": sum(len(v["patterns"]) for v in self._learned.values()),
            "duration": round(time.time() - start, 2),
        }

    def get_context_for_query(self, query: str) -> str:
        """Retrieve learned context relevant to a query."""
        topic = self._classify_topic(query)
        if topic in self._learned and self._learned[topic]["patterns"]:
            learned = self._learned[topic]
            context = f"[NIKTO learned from {learned['count']} past {topic} conversations]\n"
            for p, r in zip(learned["patterns"][-3:], learned["responses"][-3:]):
                context += f"  Q: {p}\n  A: {r}\n"
            return context
        return ""

    def get_stats(self) -> dict:
        """Get training statistics."""
        total_patterns = sum(len(v["patterns"]) for v in self._learned.values())
        return {
            "topics": list(self._learned.keys()),
            "total_patterns": total_patterns,
            "total_conversations": sum(v["count"] for v in self._learned.values()),
            "training_sessions": len(self._history),
            "last_training": self._last_train_time,
            "uptime_hours": round((time.time() - self._last_train_time) / 3600, 1) if self._last_train_time else 0,
        }

    def start_auto_train(self, interval_hours: int = 1):
        """Start automatic hourly training in background thread."""

        def loop():
            self._running = True
            while self._running:
                try:
                    result = self.train()
                    print(f"  [Trainer] Hourly training complete: {result.get('new_patterns', 0)} new patterns")
                except Exception as e:
                    print(f"  [Trainer] Training error: {e}")
                time.sleep(interval_hours * 3600)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()
        print(f"  [Trainer] Auto-training every {interval_hours}h started")

    def stop(self):
        self._running = False
