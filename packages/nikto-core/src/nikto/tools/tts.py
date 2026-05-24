from nikto.tools.base import Tool


class SpeakTool(Tool):
    name = "speak"
    description = "Speak text using text-to-speech engine"

    async def execute(self, text: str, voice_id: str = "default", **kwargs) -> dict:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            return {"success": True, "text": text, "voice": voice_id, "length": len(text)}
        except Exception as e:
            return {"success": False, "error": str(e)}


class SpeakDirectTool(Tool):
    name = "speak_direct"
    description = "Speak text directly without voice selection"

    async def execute(self, text: str, **kwargs) -> dict:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            return {"success": True, "text": text, "spoken": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


class ListVoicesTool(Tool):
    name = "list_voices"
    description = "List available TTS voices"

    async def execute(self, **kwargs) -> dict:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            voice_list = [{"id": v.id, "name": v.name} for v in voices]
            return {"success": True, "voices": voice_list, "count": len(voice_list)}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def tool_speak(text: str) -> dict:
    tool = SpeakTool()
    return await tool.execute(text=text)


async def tool_list_voices() -> dict:
    tool = ListVoicesTool()
    return await tool.execute()
