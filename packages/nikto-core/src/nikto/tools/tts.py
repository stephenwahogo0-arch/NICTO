import os
import struct
import tempfile
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional

from nikto.tools.base import Tool


async def tool_speak(text: str, rate: int = 180, voice_id: Optional[str] = None) -> str:
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        if voice_id:
            voices = engine.getProperty("voices")
            for v in voices:
                if voice_id.lower() in v.id.lower():
                    engine.setProperty("voice", v.id)
                    break
        else:
            voices = engine.getProperty("voices")
            if len(voices) > 1:
                engine.setProperty("voice", voices[1].id)

        output_dir = Path(tempfile.gettempdir()) / "nikto_audio"
        output_dir.mkdir(exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in text[:40])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(output_dir / f"{safe_name}_{timestamp}.wav")

        engine.save_to_file(text, output_path)
        engine.runAndWait()

        size_kb = os.path.getsize(output_path) / 1024
        return f"Speech generated: {output_path} ({size_kb:.1f}KB, {len(text)} chars, rate={rate})"

    except ImportError:
        return _fallback_wav(text)
    except Exception as e:
        return f"Error generating speech: {str(e)}"


async def tool_speak_direct(text: str, rate: int = 180) -> str:
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        voices = engine.getProperty("voices")
        if len(voices) > 1:
            engine.setProperty("voice", voices[1].id)
        engine.say(text)
        engine.runAndWait()
        return f"Spoken: {len(text)} chars at rate={rate}"
    except ImportError:
        return "pyttsx3 not installed. Install with: uv pip install pyttsx3"
    except Exception as e:
        return f"Error speaking: {str(e)}"


async def tool_list_voices() -> str:
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        lines = [f"Available voices ({len(voices)}):"]
        for v in voices:
            lines.append(f"  - {v.id}: {v.name} (gender: {v.gender}, lang: {v.languages})")
        return "\n".join(lines)
    except ImportError:
        return "pyttsx3 not installed."
    except Exception as e:
        return f"Error listing voices: {str(e)}"


def _fallback_wav(text: str) -> str:
    try:
        output_dir = Path(tempfile.gettempdir()) / "nikto_audio"
        output_dir.mkdir(exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in text[:40])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"{safe_name}_{timestamp}.wav"

        sample_rate = 8000
        duration = max(1.0, len(text) * 0.08)
        num_samples = int(sample_rate * duration)

        samples = bytearray()
        t = 0.0
        for i in range(num_samples):
            t = i / sample_rate
            val = int(127 * (t % 0.005 < 0.0025)) if t < 0.1 else 0
            for ch in text[i % len(text)] if text else " ":
                val += ord(ch) % 16
            val = max(0, min(255, val * 8))
            samples.append(val)

        with wave.open(str(output_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(1)
            wf.setframerate(sample_rate)
            wf.writeframes(bytes(samples))

        size_kb = os.path.getsize(output_path) / 1024
        return f"Fallback audio generated: {output_path} ({size_kb:.1f}KB, {duration:.1f}s)"
    except Exception as e:
        return f"Error generating fallback audio: {str(e)}"


SpeakTool = Tool(
    name="speak",
    description="Convert text to speech and save as a WAV audio file. Uses offline pyttsx3 engine with natural voice. Falls back to basic tone generation.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to convert to speech"},
            "rate": {"type": "integer", "description": "Speech rate in words per minute (default 180)"},
            "voice_id": {"type": "string", "description": "Optional voice ID to use"},
        },
        "required": ["text"],
    },
    async_function=tool_speak,
)

SpeakDirectTool = Tool(
    name="speak_direct",
    description="Speak text directly through system speakers in real-time using offline TTS. Requires pyttsx3.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to speak aloud"},
            "rate": {"type": "integer", "description": "Speech rate (default 180)"},
        },
        "required": ["text"],
    },
    async_function=tool_speak_direct,
)

ListVoicesTool = Tool(
    name="list_voices",
    description="List all available TTS voices on this system. Shows voice IDs, names, gender, and language.",
    parameters={
        "type": "object",
        "properties": {},
    },
    async_function=tool_list_voices,
)
