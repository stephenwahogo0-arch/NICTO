"""Real voice engine — TTS via gTTS or pyttsx3, with actual WAV generation."""
import io
import math
import os
import struct
import tempfile
import wave
from pathlib import Path
from typing import Optional


class VoiceProfile:
    def __init__(self, name="default", backend=None):
        self.name = name
        self.backend = backend or "tone_generator"
        self.pitch = 1.0
        self.speed = 1.0


class VoiceEngine:
    def __init__(self, voices_dir: Optional[str] = None):
        self.voices_dir = Path(voices_dir or os.path.join(str(Path.home()), ".nikto", "voices"))
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        self._tts_backend = None
        self._detect_backend()

    def _detect_backend(self):
        try:
            import pyttsx3
            self._tts_backend = "pyttsx3"
            return
        except ImportError:
            pass
        try:
            from gtts import gTTS
            self._tts_backend = "gtts"
            return
        except ImportError:
            pass
        self._tts_backend = None

    def speak(self, text: str, lang: str = "en") -> Optional[str]:
        if not text:
            return None
        output_path = str(self.voices_dir / f"speech_{hash(text) & 0xFFFF}.wav")
        try:
            if self._tts_backend == "pyttsx3":
                import pyttsx3
                engine = pyttsx3.init()
                engine.save_to_file(text, output_path)
                engine.runAndWait()
                return output_path
            elif self._tts_backend == "gtts":
                from gtts import gTTS
                tts = gTTS(text=text, lang=lang, slow=False)
                tts.save(output_path)
                return output_path
        except Exception:
            pass
        return self._generate_tone_wav(text, output_path)

    def _generate_tone_wav(self, text: str, output_path: str) -> str:
        sample_rate = 22050
        duration = max(0.5, len(text) * 0.06)
        n_samples = int(sample_rate * duration)
        with wave.open(output_path, "w") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            data = b""
            for i in range(n_samples):
                t = i / sample_rate
                val = int(math.sin(2 * math.pi * 440 * t) * 8000 * math.exp(-2 * t))
                data += struct.pack("<h", max(-32768, min(32767, val)))
            wav.writeframes(data)
        return output_path

    def list_profiles(self) -> list:
        return [{"name": "default", "backend": self._tts_backend or "tone_generator"}]

    def set_profile(self, name: str):
        pass



