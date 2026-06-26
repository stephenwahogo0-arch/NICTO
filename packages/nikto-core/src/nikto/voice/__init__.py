"""NIKTO Voice Module."""
from nikto.voice.engine import NiktoVoice

try:
    from nikto.voice.engine import VoiceEngine
except ImportError:
    VoiceEngine = None

__all__ = ["NiktoVoice", "VoiceEngine"]
