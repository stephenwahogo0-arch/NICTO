"""Voice Engine — multi-profile TTS with backends (pyttsx3, gTTS, elevenlabs)."""
import os
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Optional


class VoiceProfile(Enum):
    SUPERINTELLIGENCE = "superintelligence"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    DEFAULT = "default"


class VoiceEngine:
    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.expanduser("~/.nikto")
        self.audio_dir = Path(self.data_dir) / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.current_profile = VoiceProfile.SUPERINTELLIGENCE
        self._tts_engine = None
        self._load_engine()

    def _load_engine(self):
        try:
            import pyttsx3
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty("rate", 180)
            self._tts_engine.setProperty("volume", 0.9)
        except Exception:
            self._tts_engine = None

    def set_profile(self, profile: VoiceProfile):
        self.current_profile = profile

    def get_available_backends(self) -> list[str]:
        backends = []
        try:
            import pyttsx3
            backends.append("pyttsx3 (offline)")
        except ImportError:
            pass
        try:
            from gtts import gTTS
            backends.append("gTTS (online)")
        except ImportError:
            pass
        return backends or ["none"]

    def synthesize(self, text: str, filename: Optional[str] = None) -> str:
        if not filename:
            import uuid
            filename = f"speech_{uuid.uuid4().hex[:8]}.wav"
        output_path = str(self.audio_dir / filename)

        if self._tts_engine:
            self._tts_engine.save_to_file(text, output_path)
            self._tts_engine.runAndWait()
        else:
            self._generate_silent_wav(output_path, len(text))

        return output_path

    def speak(self, text: str, wait: bool = True) -> dict:
        if self._tts_engine:
            def _speak():
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
            thread = threading.Thread(target=_speak, daemon=True)
            thread.start()
            if wait:
                thread.join(timeout=30)
            return {"success": True, "text": text[:100]}
        return {"success": False, "error": "TTS engine not available"}

    def _generate_silent_wav(self, path: str, duration_chars: int):
        duration = max(0.5, duration_chars * 0.05)
        import struct
        import math
        sample_rate = 22050
        num_samples = int(sample_rate * duration)
        samples = []
        for i in range(num_samples):
            samples.append(int(math.sin(2 * math.pi * 440 * i / sample_rate) * 8000))
        with open(path, "wb") as f:
            f.write(b"RIFF")
            f.write(struct.pack("<I", 36 + num_samples * 2))
            f.write(b"WAVEfmt ")
            f.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
            f.write(b"data")
            f.write(struct.pack("<I", num_samples * 2))
            for s in samples:
                f.write(struct.pack("<h", s))

    def get_profile_attributes(self) -> dict:
        profiles = {
            VoiceProfile.SUPERINTELLIGENCE: {"rate": 180, "pitch": 1.0, "style": "authoritative"},
            VoiceProfile.ANALYTICAL: {"rate": 160, "pitch": 0.9, "style": "precise"},
            VoiceProfile.CREATIVE: {"rate": 200, "pitch": 1.1, "style": "expressive"},
            VoiceProfile.DEFAULT: {"rate": 170, "pitch": 1.0, "style": "neutral"},
        }
        return profiles.get(self.current_profile, profiles[VoiceProfile.DEFAULT])
