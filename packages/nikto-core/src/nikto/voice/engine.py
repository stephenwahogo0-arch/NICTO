import asyncio
import os
import tempfile
from typing import Optional


class NiktoVoice:
    def __init__(self):
        self._stt_available = False
        self._tts_available = False
        self._init_engines()

    def _init_engines(self):
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._microphone = sr.Microphone()
            self._stt_available = True
        except Exception:
            self._stt_available = False
        try:
            import pyttsx3
            self._tts_engine = pyttsx3.init()
            self._tts_available = True
        except Exception:
            self._tts_available = False

    async def listen(self) -> str:
        if not self._stt_available:
            return "[Voice] Speech recognition unavailable. Install speechrecognition and PyAudio."
        try:
            import speech_recognition as sr
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._recognizer.listen(source, timeout=5, phrase_time_limit=15)
            text = self._recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return "[Voice] Could not understand audio"
        except Exception as e:
            return f"[Voice Error] {e}"

    async def speak(self, text: str, voice: str = "default"):
        if not self._tts_available:
            print(f"[Voice TTS] {text}")
            return
        loop = asyncio.get_event_loop()
        def _speak():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                voices = engine.getProperty("voices")
                if voice != "default" and voices:
                    for v in voices:
                        if voice.lower() in v.name.lower():
                            engine.setProperty("voice", v.id)
                            break
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"[TTS Error] {e}")
        await loop.run_in_executor(None, _speak)

    async def voice_chat_loop(self, agent):
        print("[NICTO Voice] Starting voice chat. Say 'exit' or 'quit' to stop.")
        while True:
            user_input = await self.listen()
            if not user_input:
                continue
            print(f"You: {user_input}")
            if user_input.lower() in ["exit", "quit", "stop"]:
                await self.speak("Goodbye.")
                break
            result = await agent.run(user_input)
            response = result.get("content", "")
            print(f"NICTO: {response}")
            await self.speak(response)

    async def transcribe_file(self, audio_path: str) -> str:
        if not self._stt_available:
            return "[Voice] Speech recognition unavailable."
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = r.record(source)
            return r.recognize_google(audio)
        except Exception as e:
            return f"[Transcription Error] {e}"

    def get_status(self) -> dict:
        return {
            "stt_available": self._stt_available,
            "tts_available": self._tts_available,
        }
