import json
import math
from datetime import datetime, timezone
from typing import Optional
from nikto.brain.models import EmotionType, EmotionalState


class NiktoEmotionalCore:

    def __init__(self):
        self.current_state = EmotionalState()
        self.emotion_decay = 0.05
        self.mood_baseline = 0.0
        self.emotional_memory = []
        self.max_history = 100
        self.triggers = {}

    def update(self, stimulus: str, intensity: float = 0.3,
               emotion_type: EmotionType = EmotionType.NEUTRAL):
        if intensity <= 0.0:
            return

        self.current_state.primary_emotion = emotion_type
        self.current_state.intensity = min(1.0, self.current_state.intensity + intensity)
        self.current_state.timestamp = datetime.now(timezone.utc).isoformat()

        valence_map = {
            EmotionType.JOY: 0.8, EmotionType.SADNESS: -0.7, EmotionType.ANGER: -0.5,
            EmotionType.FEAR: -0.6, EmotionType.SURPRISE: 0.3, EmotionType.TRUST: 0.6,
            EmotionType.ANTICIPATION: 0.4, EmotionType.CURIOSITY: 0.5, EmotionType.CONFUSION: -0.2,
            EmotionType.NEUTRAL: 0.0,
        }
        arousal_map = {
            EmotionType.JOY: 0.6, EmotionType.SADNESS: 0.3, EmotionType.ANGER: 0.9,
            EmotionType.FEAR: 0.8, EmotionType.SURPRISE: 0.7, EmotionType.TRUST: 0.3,
            EmotionType.ANTICIPATION: 0.5, EmotionType.CURIOSITY: 0.6, EmotionType.CONFUSION: 0.4,
            EmotionType.NEUTRAL: 0.0,
        }

        self.current_state.valence = valence_map.get(emotion_type, 0.0)
        self.current_state.arousal = arousal_map.get(emotion_type, 0.0)

        self.emotional_memory.append({
            "stimulus": stimulus,
            "state": self.current_state.to_dict(),
        })
        if len(self.emotional_memory) > self.max_history:
            self.emotional_memory.pop(0)

        self._update_triggers(stimulus, emotion_type)

    def _update_triggers(self, stimulus: str, emotion: EmotionType):
        key = stimulus.lower()
        if key not in self.triggers:
            self.triggers[key] = {}
        self.triggers[key][emotion.value] = self.triggers[key].get(emotion.value, 0) + 1

    def decay(self):
        decay_factor = 1.0 - self.emotion_decay
        self.current_state.intensity *= decay_factor
        self.current_state.valence *= decay_factor
        self.current_state.arousal *= decay_factor
        if self.current_state.intensity < 0.01:
            self.current_state = EmotionalState()
            self.current_state.valence = self.mood_baseline

    def get_dominant_emotion(self) -> EmotionType:
        return self.current_state.primary_emotion

    def get_emotional_influence(self) -> float:
        return self.current_state.intensity * 0.3 + abs(self.current_state.valence) * 0.4 + self.current_state.arousal * 0.3

    def predict_response(self, stimulus: str) -> Optional[EmotionType]:
        key = stimulus.lower()
        if key in self.triggers:
            return max(self.triggers[key], key=self.triggers[key].get)
        return None

    def regulate(self, strategy: str = "deep_breath"):
        strategies = {
            "deep_breath": 0.3,
            "reframe": 0.5,
            "distraction": 0.2,
            "acceptance": 0.4,
        }
        reduction = strategies.get(strategy, 0.1)
        self.current_state.intensity = max(0.0, self.current_state.intensity - reduction)
        self.current_state.arousal = max(0.0, self.current_state.arousal - reduction * 0.5)

    def save(self) -> dict:
        return {
            "current_state": self.current_state.to_dict(),
            "emotion_decay": self.emotion_decay,
            "mood_baseline": self.mood_baseline,
            "emotional_memory": [{"stimulus": e["stimulus"], "state": e["state"]} for e in self.emotional_memory],
            "triggers": self.triggers,
        }

    def load(self, data: dict):
        cs = data.get("current_state", {})
        self.current_state = EmotionalState(
            primary_emotion=EmotionType(cs.get("primary_emotion", "neutral")),
            intensity=cs.get("intensity", 0.0),
            valence=cs.get("valence", 0.0),
            arousal=cs.get("arousal", 0.0),
            timestamp=cs.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )
        self.emotion_decay = data.get("emotion_decay", 0.05)
        self.mood_baseline = data.get("mood_baseline", 0.0)
        self.emotional_memory = data.get("emotional_memory", [])[:self.max_history]
        self.triggers = data.get("triggers", {})

    def export(self) -> dict:
        return {
            "current_state": self.current_state.to_dict(),
            "mood_baseline": self.mood_baseline,
            "history_length": len(self.emotional_memory),
            "triggers": self.triggers,
        }
