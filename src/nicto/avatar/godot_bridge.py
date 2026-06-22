"""Avatar engine — Godot 4 bindings with ASCII fallback."""
from __future__ import annotations
from typing import Optional


class EmotionalState:
    def __init__(self, valence: float = 0.0, arousal: float = 0.5):
        self.valence = max(-1.0, min(1.0, valence))
        self.arousal = max(0.0, min(1.0, arousal))


class _GodotAvatar:
    def __init__(self):
        self._emotion = EmotionalState()
        self._gaze = (0.0, 0.0, 0.0)
        self._ready = False

    def set_emotion(self, valence: float, arousal: float):
        self._emotion = EmotionalState(valence, arousal)

    def look_at_user(self, x: float, y: float, z: float):
        self._gaze = (x, y, z)

    def speak_with_lipsync(self, text: str, audio_buffer: bytes = b""):
        pass


class _WebAvatarRenderer:
    def set_emotion(self, valence: float, arousal: float):
        pass

    def look_at(self, x: float, y: float, z: float):
        pass

    def speak(self, text: str, voice: str = "default"):
        pass


class _TextAvatar:
    """ASCII/Unicode fallback for terminals."""
    FACES = {
        "neutral": "( ·_·)",
        "happy": "(◕‿◕)",
        "sad": "(︶︹︶)",
        "excited": "(☆▽☆)",
        "thinking": "(◔_◔)",
    }

    def __init__(self):
        self._valence = 0.0
        self._arousal = 0.5

    def set_emotion(self, valence: float, arousal: float):
        self._valence = valence
        self._arousal = arousal
        face = "happy" if valence > 0.3 else "sad" if valence < -0.3 else "excited" if arousal > 0.8 else "neutral"
        print(f"  Avatar: {self.FACES.get(face, self.FACES['neutral'])}")

    def look_at(self, x: float, y: float, z: float):
        print(f"  Avatar gazes toward ({x:.1f}, {y:.1f}, {z:.1f})")

    def speak(self, text: str, voice: str = "default"):
        print(f"  Avatar says: {text[:120]}..." if len(text) > 120 else f"  Avatar says: {text}")


class Avatar:
    """Avatar engine with automatic backend selection."""

    def __init__(self, backend: str = "auto"):
        self.backend = backend
        if backend == "godot":
            try:
                self._impl = _GodotAvatar()
            except Exception:
                self._impl = _TextAvatar()
        elif backend == "web":
            self._impl = _WebAvatarRenderer()
        else:
            self._impl = _TextAvatar()

    def set_emotion(self, valence: float, arousal: float):
        self._impl.set_emotion(valence, arousal)

    def look_at(self, x: float, y: float, z: float):
        self._impl.look_at(x, y, z)

    def speak(self, text: str, voice: str = "default"):
        self._impl.speak(text, voice)
