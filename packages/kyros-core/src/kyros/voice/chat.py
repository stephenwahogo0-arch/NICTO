"""Voice-to-Voice Chat Engine — speak to KYROS, KYROS speaks back."""
import os
import tempfile
import wave
import pyaudio
import threading
import time


class VoiceChatEngine:
    def __init__(self, voice_engine=None):
        self.voice = voice_engine
        self.listening = False
        self._audio = pyaudio.PyAudio() if self._has_pyaudio() else None

    def _has_pyaudio(self):
        try:
            import pyaudio
            return True
        except ImportError:
            return False

    def listen(self, timeout=5):
        """Record from microphone, return transcribed text."""
        if not self._audio:
            return "Voice input requires pyaudio. Install: pip install pyaudio"
        chunk = 1024
        fmt = pyaudio.paInt16
        channels = 1
        rate = 16000
        self.listening = True
        stream = self._audio.open(format=fmt, channels=channels, rate=rate,
                                  input=True, frames_per_buffer=chunk)
        frames = []
        for _ in range(int(rate / chunk * timeout)):
            if not self.listening:
                break
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)
        stream.stop_stream(); stream.close()
        self.listening = False
        # Save to temp WAV for processing
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wf = wave.open(tmp.name, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(self._audio.get_sample_size(fmt))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        return tmp.name

    def speak(self, text):
        """Speak text using voice engine."""
        if self.voice:
            return self.voice.speak(text)
        return {"success": False, "error": "No voice engine"}

    def chat_cycle(self, text):
        """Full voice cycle: speak response, listen for reply."""
        self.speak(text)
        return self.listen()

    def stop(self):
        self.listening = False
        if self._audio:
            self._audio.terminate()
