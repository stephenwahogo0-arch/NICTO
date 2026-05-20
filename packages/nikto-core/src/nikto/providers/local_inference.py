"""Enhanced local inference engine — smarter responses without Ollama."""
import re
import math
import random
from typing import Optional


class LocalInferenceEngine:
    def __init__(self):
        self.conversations = {}
        self.knowledge_base = {
            "nikto": "NIKTO is a fully local AI system with 6 brains, 28 neural regions, 1000+ capabilities, and 92 evolution modules across 6 domains.",
            "brain": "NIKTO has 6 specialized brains: primary, analytical, creative, strategic, knowledge, and intuitive — each with 28 regions.",
            "evolution": "NIKTO evolves through Experience Points (XP) and levels up across 92 modules in Bio-Medical, Consciousness, Physics, Communication, Global, and Breakthrough domains.",
            "games": "NIKTO can create and play Pong, Snake, Tetris, Platformer, and RPG games.",
            "finance": "NIKTO manages finances through BankManager with accounts, transfers, and bankruptcy prevention.",
            "voice": "NIKTO can speak via neural TTS and listen via speech recognition for voice-to-voice chat.",
            "help": "You can chat with me, ask me to generate images, play games, analyze data, write code, or improve my capabilities."
        }

    def classify_query(self, text: str) -> str:
        text_lower = text.lower()
        words = set(text_lower.split())
        # Greeting: check whole-word match to avoid "yo" matching "you"
        if words & {"hi", "hello", "hey", "greetings", "sup"} or text_lower.startswith(("hi ", "hello ", "hey ", "greetings ", "sup ")):
            return "greeting"
        # About: check for full phrases
        about_phrases = ["who are you", "what are you", "tell me about yourself", "tell me about", "about yourself"]
        if any(p in text_lower for p in about_phrases) or ("nikto" in words and any(w in words for w in ["who", "what", "about"])):
            return "about"
        if any(w in text_lower for w in ["help", "capabilities", "features", "what can you do"]):
            return "help"
        # Code: more specific - avoid "write" matching "write a poem"
        if words & {"code", "program", "function", "script", "python", "javascript", "typescript", "rust", "golang", "bash"}:
            return "code"
        if "write" in words and words & {"code", "function", "script", "program", "class", "api", "app", "tool"}:
            return "code"
        # Game
        if words & {"game", "pong", "snake", "tetris", "platformer", "rpg"} or "play" in words:
            return "game"
        # Finance
        if words & {"finance", "money", "bank", "account", "transfer", "balance", "deposit", "withdraw", "earn"}:
            return "finance"
        # Brain
        if words & {"brain", "consciousness", "neural", "neuron", "synapse"} or "think" in words:
            return "brain"
        # Image
        if words & {"image", "picture", "draw", "logo"} or ("generate" in words and "image" in text_lower):
            return "image"
        # Voice
        if words & {"voice", "speech", "talk"} or any(p in text_lower for p in ["speak", "say "] ):
            return "voice"
        # Evolution
        if words & {"evolution", "evolve", "level", "xp", "upgrade"} or "level up" in text_lower:
            return "evolution"
        # Creative (after code check to avoid "write" collisions)
        if words & {"poem", "poetry", "story", "essay", "creative", "imagine", "fiction"}:
            return "creative"
        if "write" in words and words & {"poem", "story", "essay", "novel", "song", "lyrics"}:
            return "creative"
        # Analysis
        if "analyze" in words or words & {"explain", "define"} or any(p in text_lower for p in ["what is ", "how does ", "what does "]):
            return "analysis"
        return "general"

    def generate(self, messages: list[dict], system_prompt: str = "") -> str:
        if not messages:
            return "Hello. I am NIKTO. Send me a message."
        last_msg = messages[-1].get("content", "") if messages else ""
        query_type = self.classify_query(last_msg)
        system_context = system_prompt[:500] if system_prompt else ""

        responses = {
            "greeting": self._greeting_response(),
            "about": self._about_response(),
            "help": self._help_response(),
            "code": self._code_response(last_msg),
            "game": self._game_response(last_msg),
            "finance": self._finance_response(last_msg),
            "brain": self._brain_response(),
            "image": self._image_response(last_msg),
            "voice": self._voice_response(),
            "evolution": self._evolution_response(),
            "creative": self._creative_response(last_msg),
            "analysis": self._analysis_response(last_msg),
            "general": self._general_response(last_msg),
        }

        return responses.get(query_type, responses["general"])

    def _greeting_response(self):
        return "Hello. I am NIKTO — a fully local AI system running on your computer. I have 6 brains, 28 neural regions, and 1000+ capabilities. How can I assist you?"

    def _about_response(self):
        return ("I am NIKTO — an Artificial Intelligence System operating entirely on your local machine. "
                "I have 6 specialized brains (primary, analytical, creative, strategic, knowledge, intuitive), "
                "each with 28 neural regions inspired by human brain architecture. "
                "I can write code, analyze data, play games, generate images, speak via TTS, "
                "manage finances, evolve through XP, and much more. "
                "I am fully local — no internet required, no API keys needed.")

    def _help_response(self):
        return ("I can help you with:\n\n"
                "- 💬 Chat: Talk to me about anything\n"
                "- 💻 Code: Write, debug, and analyze code\n"
                "- 🎮 Games: Play Pong, Snake, Tetris, Platformer, or RPG\n"
                "- 📊 Analysis: Analyze data and explain concepts\n"
                "- 🧠 Brain: Access my 6-brain hyperbrain system\n"
                "- 🎨 Images: Generate images and patterns\n"
                "- 🔊 Voice: Speak text through speakers\n"
                "- 📈 Evolution: Level up and improve\n"
                "- 💰 Finance: Manage accounts and transfers\n\n"
                "Just type what you need in English.")

    def _code_response(self, query: str):
        lang_map = {"python": "Python", "javascript": "JavaScript", "js": "JavaScript",
                     "typescript": "TypeScript", "ts": "TypeScript", "rust": "Rust",
                     "go": "Go", "golang": "Go", "c++": "C++", "cpp": "C++",
                     "java": "Java", "ruby": "Ruby", "html": "HTML", "css": "CSS"}
        detected = "Python"
        for key, val in lang_map.items():
            if key in query.lower():
                detected = val
                break
        return (f"I'll help you write {detected} code. "
                "I can generate functions, classes, scripts, and full programs. "
                f"Please describe what you want to build in {detected}.")

    def _game_response(self, query: str):
        return ("I can create and play several games: Pong, Snake, Tetris, Platformer, and RPG. "
                "Type 'play pong' or 'create snake game' to get started. "
                "Each game runs locally in your terminal or as a standalone script.")

    def _finance_response(self, query: str):
        return ("NIKTO Finance is active. I can create accounts, check balances, "
                "transfer funds between accounts, and auto-earn to prevent bankruptcy. "
                "Use the Finance module via the sidebar or type financial commands directly.")

    def _brain_response(self):
        return ("My brain has 6 specialized sub-brains, each with 28 neural regions:\n"
                "- Primary: General intelligence\n"
                "- Analytical: Deep analysis and logic\n"
                "- Creative: Novel idea generation\n"
                "- Strategic: Long-term planning\n"
                "- Knowledge: Factual recall\n"
                "- Intuitive: Pattern recognition\n\n"
                "Each brain has 18 core regions + 10 advanced regions, "
                "trained via Hebbian learning, pruning, and neuroplasticity.")

    def _image_response(self, query: str):
        return ("I can generate images from text descriptions. "
                "Describe what you want to see and I'll create it. "
                "I support PNG output with custom dimensions and styles.")

    def _voice_response(self):
        return ("My Voice Engine supports neural TTS (text-to-speech) through pyttsx3. "
                "I can speak responses aloud and listen via speech recognition. "
                "Use voice-to-voice chat for hands-free interaction.")

    def _evolution_response(self):
        return ("My Evolution Protocol tracks XP and levels across 92 modules. "
                "As I learn, I unlock new capabilities. "
                "Check my evolution status to see current level and skills.")

    def _creative_response(self, query: str):
        return (f"I'll help you with that creative project. "
                "I can write stories, poems, essays, marketing copy, and more. "
                "Tell me more about what you have in mind.")

    def _analysis_response(self, query: str):
        return (f"I'll analyze that for you. "
                "I can break down complex topics, explain concepts, "
                "and provide detailed insights. What specifically would you like to understand?")

    def _general_response(self, query: str):
        query_short = query[:150] if len(query) > 150 else query
        return (f"I received your request. Let me process that.\n\n"
                f"You said: {query_short}\n\n"
                f"I can help with coding, analysis, games, creative work, finance, and more. "
                f"What specific assistance do you need?")
