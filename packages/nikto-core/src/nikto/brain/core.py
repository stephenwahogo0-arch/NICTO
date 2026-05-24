"""
NiktoBrain — NICTO's Core Intelligence.

The NiktoBrain class is the central intelligence of NICTO.
It replaces the concept of "calling an LLM" with a proper
thinking pipeline.

This is not a wrapper. This IS the AI.
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from .models import (
    Intent, Perception, NiktoThought, Reasoning, MemoryEvent,
    EmotionalState, KnowledgeSet
)

# Import all brain components
from .identity import NiktoIdentity
from .reasoner import NiktoReasoner
from .memory import NiktoLongTermMemory
from .learner import NiktoLearner
from .knowledge import NiktoKnowledgeCore
from .emotion import NiktoEmotionalCore
from .conscience import NiktoConscience
from .language import NiktoLanguageEngine
from .goals import NiktoGoalSystem


class NiktoBrain:
    """
    The core intelligence of NICTO.
    
    This is not a wrapper. This IS the AI. NiktoBrain
    orchestrates all of NICTO's cognitive systems to
    produce coherent, intelligent responses.
    
    Architecture:
    - Identity: Who NICTO is, how it communicates
    - Reasoner: How NICTO thinks using multiple strategies
    - Memory: What NICTO remembers across sessions
    - Learner: How NICTO improves over time
    - Knowledge: What NICTO knows internally
    - Emotion: How NICTO detects and responds to emotions
    - Conscience: How NICTO makes ethical decisions
    - Language: How NICTO generates responses
    - Goals: What NICTO is working toward
    
    Pipeline stages:
    1. Perceive — understand what is being asked
    2. Recall — retrieve relevant memories and knowledge
    3. Reason — apply logic and domain knowledge
    4. Judge — apply conscience and values filter
    5. Create — generate the response
    6. Learn — update memory and self-model
    7. Express — format through personality layer
    """

    def __init__(self):
        """Initialize all brain components."""
        self.identity = NiktoIdentity()
        self.reasoner = NiktoReasoner()
        self.memory = NiktoLongTermMemory()
        self.learner = NiktoLearner()
        self.knowledge = NiktoKnowledgeCore()
        self.emotion = NiktoEmotionalCore()
        self.conscience = NiktoConscience()
        self.language = NiktoLanguageEngine()
        self.goals = NiktoGoalSystem()
        
        # Internal state
        self._initialized = True
        self._interaction_count = 0

    async def think(
        self,
        input: str,
        context: Optional[dict] = None
    ) -> NiktoThought:
        """
        Full thinking pipeline. This is how NICTO processes
        any input from any source.
        
        Args:
            input: The user's input message
            context: Optional context dictionary
            
        Returns:
            NiktoThought with response and metadata
        """
        ctx = context or {}
        
        # Stage 1: Perceive - understand what is being asked
        perception = await self.perceive(input, ctx)
        
        # Stage 2: Recall - retrieve relevant memories and knowledge
        memories = await self.memory.recall(perception, limit=10)
        knowledge_set = await self.knowledge.retrieve(perception, limit=15)
        knowledge = knowledge_set.items
        
        # Stage 3: Reason - apply logic and domain knowledge
        reasoning = await self.reasoner.reason(perception, memories, knowledge)
        
        # Stage 4: Judge - apply conscience and values filter
        judgment = await self.conscience.judge(reasoning)
        
        # Detect emotional state for response adjustment
        emotional_state = self.emotion.detect_emotional_state(input)
        
        # Stage 5: Create - generate the response
        response = await self.language.generate(
            reasoning, judgment, self.identity, emotional_state
        )
        
        # Stage 6: Learn - update memory and self-model
        await self._learn_from_interaction(input, response, reasoning, ctx)
        
        # Stage 7: Express - track interaction for goals
        self._interaction_count += 1
        self.goals.record_interaction(
            knowledge_added=len(reasoning.knowledge_gaps),
            quality=getattr(reasoning, 'confidence', 0.5)
        )
        
        return NiktoThought(
            response=response,
            confidence=reasoning.confidence,
            reasoning_chain=reasoning.chain,
            knowledge_used=[k.content[:50] for k in knowledge[:5]],
            memory_updated=True
        )

    async def perceive(self, input: str, context: dict) -> Perception:
        """
        Break down the input into structured understanding.
        
        Returns: intent, entities, sentiment, urgency,
        topic domain, required expertise level, language
        
        Args:
            input: Raw user input
            context: Additional context
            
        Returns:
            Perception object with structured understanding
        """
        # Classify intent
        intent = self._classify_intent(input)
        
        # Extract entities
        entities = self._extract_entities(input)
        
        # Detect sentiment
        sentiment = self._detect_sentiment(input)
        
        # Detect topic domain
        domain = self._detect_domain(input)
        
        # Detect expertise level
        expertise = self._detect_expertise_needed(input)
        
        # Detect language
        language = self._detect_language(input)
        
        return Perception(
            raw_input=input,
            intent=intent,
            entities=entities,
            sentiment=sentiment,
            domain=domain,
            expertise_required=expertise,
            language=language,
            context=context
        )

    def _classify_intent(self, text: str) -> Intent:
        """
        Classifies intent without calling any external API.
        
        Uses keyword patterns, sentence structure analysis,
        and NICTO's internal intent classifier.
        
        Args:
            text: User input text
            
        Returns:
            Intent enum value
        """
        text_lower = text.lower()
        
        # Build keyword lists for each intent
        build_keywords = [
            "build", "create", "make", "generate", "write",
            "develop", "code", "implement", "design", "new"
        ]
        learn_keywords = [
            "how", "what", "why", "explain", "teach",
            "understand", "learn", "what is", "how does",
            "can you tell"
        ]
        debug_keywords = [
            "error", "bug", "fix", "broken", "not working",
            "issue", "problem", "fail", "crash", "exception",
            "doesn't work", "won't work"
        ]
        attack_keywords = [
            "hack", "exploit", "pentest", "scan", "vulnerability",
            "attack", "bypass", "crack", "brute force", "inject"
        ]
        analyze_keywords = [
            "analyze", "review", "audit", "check", "inspect",
            "evaluate", "assess", "look at", "examine"
        ]
        generate_keywords = [
            "write", "generate", "create", "make", "produce"
        ]
        
        # Score each intent
        scores = {
            Intent.BUILD: sum(1 for k in build_keywords if k in text_lower),
            Intent.LEARN: sum(1 for k in learn_keywords if k in text_lower),
            Intent.DEBUG: sum(1 for k in debug_keywords if k in text_lower),
            Intent.ATTACK: sum(1 for k in attack_keywords if k in text_lower),
            Intent.ANALYZE: sum(1 for k in analyze_keywords if k in text_lower),
            Intent.GENERATE: sum(1 for k in generate_keywords if k in text_lower),
        }
        
        # Check for question marks (might indicate learning/question intent)
        if "?" in text and scores.get(Intent.LEARN, 0) == 0:
            scores[Intent.QUESTION] = 1
        
        # Check for command-like structure (instruct intent)
        if text and text[0].isupper() and any(text.startswith(x) for x in ["Do", "Make", "Build", "Create", "Find"]):
            scores[Intent.INSTRUCT] = 2
        
        if not any(scores.values()):
            return Intent.CONVERSE
        
        return max(scores, key=scores.get)

    def _extract_entities(self, text: str) -> list[str]:
        """
        Extract entities from text.
        
        Identifies: people, places, technical terms,
        programming languages, tool names, URLs, IPs.
        
        Args:
            text: User input text
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Common programming languages
        languages = [
            "python", "javascript", "java", "c++", "c#", "ruby",
            "go", "rust", "typescript", "php", "swift", "kotlin",
            "scala", "perl", "r", "matlab", "bash", "shell"
        ]
        
        text_lower = text.lower()
        for lang in languages:
            if lang in text_lower:
                entities.append(f"language:{lang}")
        
        # Common tools and technologies
        tools = [
            "docker", "kubernetes", "git", "linux", "aws", "azure",
            "gcp", "postgres", "mysql", "mongodb", "redis", "nginx",
            "apache", "jenkins", "terraform", "ansible", "vagrant"
        ]
        
        for tool in tools:
            if tool in text_lower:
                entities.append(f"tool:{tool}")
        
        # IP addresses (simple pattern)
        import re
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        ips = re.findall(ip_pattern, text)
        for ip in ips:
            entities.append(f"ip:{ip}")
        
        # URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        for url in urls:
            entities.append(f"url:{url}")
        
        return entities

    def _detect_sentiment(self, text: str) -> str:
        """
        Detect sentiment of input.
        
        Args:
            text: User input text
            
        Returns:
            Sentiment label: positive, negative, neutral, frustrated, excited
        """
        text_lower = text.lower()
        
        # Negative/frustrated indicators
        negative_words = [
            "frustrated", "angry", "annoyed", "stupid", "hate",
            "terrible", "awful", "worst", "broken", "useless"
        ]
        
        if any(word in text_lower for word in negative_words):
            return "frustrated"
        
        # Positive/excited indicators
        positive_words = [
            "great", "awesome", "amazing", "love", "perfect",
            "excellent", "fantastic", "wonderful", "thanks"
        ]
        
        if any(word in text_lower for word in positive_words):
            return "excited"
        
        return "neutral"

    def _detect_domain(self, text: str) -> str:
        """
        Detect the primary topic domain.
        
        Args:
            text: User input text
            
        Returns:
            Domain string: cybersecurity, programming, ai_ml, etc.
        """
        text_lower = text.lower()
        
        # Domain keywords
        domains = {
            "cybersecurity": [
                "security", "hack", "vulnerability", "exploit",
                "penetration", "ctf", "malware", "firewall", "encrypt"
            ],
            "programming": [
                "code", "function", "class", "debug", "error",
                "bug", "algorithm", "api", "database", "software"
            ],
            "ai_ml": [
                "machine learning", "neural", "ai", "model",
                "training", "deep learning", "prediction", "classification"
            ],
            "network_engineering": [
                "network", "tcp", "udp", "http", "dns", "router",
                "switch", "subnet", "vpn", "bandwidth"
            ],
            "cloud_infrastructure": [
                "cloud", "aws", "azure", "gcp", "kubernetes",
                "docker", "container", "serverless", "lambda"
            ],
            "game_development": [
                "game", "unity", "unreal", "graphics", "physics",
                "animation", "sprite", "level design", "gameplay"
            ],
            "system_administration": [
                "server", "linux", "unix", "bash", "shell",
                "cron", "systemd", "service", "monitoring"
            ],
        }
        
        for domain, keywords in domains.items():
            matches = sum(1 for k in keywords if k in text_lower)
            if matches >= 2:
                return domain
        
        # Check for programming language mentions
        if any(lang in text_lower for lang in ["python", "javascript", "java", "c++"]):
            return "programming"
        
        return "general"

    def _detect_expertise_needed(self, text: str) -> str:
        """
        Detect required expertise level.
        
        Args:
            text: User input text
            
        Returns:
            Expertise level: beginner, intermediate, advanced, expert
        """
        text_lower = text.lower()
        
        # Beginner indicators
        beginner_words = [
            "beginner", "new to", "just starting", "how do i",
            "help me", "explain", "what is", "tutorial"
        ]
        
        if any(word in text_lower for word in beginner_words):
            return "beginner"
        
        # Expert indicators
        expert_words = [
            "advanced", "optimize", "scale", "production",
            "enterprise", "architect", "performance tuning",
            "low-level", "kernel"
        ]
        
        if any(word in text_lower for word in expert_words):
            return "advanced"
        
        return "intermediate"

    def _detect_language(self, text: str) -> str:
        """
        Detect the language the user is writing in.
        
        Args:
            text: User input text
            
        Returns:
            Language code: en, es, fr, de, etc.
        """
        # Simple language detection based on common words
        text_lower = text.lower()
        
        # English indicators
        english_words = ["the", "is", "are", "and", "to", "of", "a", "in"]
        
        # Spanish indicators
        spanish_words = ["el", "la", "los", "las", "de", "que", "es", "en", "un", "una"]
        
        # French indicators
        french_words = ["le", "la", "les", "de", "et", "est", "un", "une", "des"]
        
        # German indicators
        german_words = ["der", "die", "das", "und", "ist", "von", "mit", "ein", "eine"]
        
        english_count = sum(1 for w in english_words if w in text_lower)
        spanish_count = sum(1 for w in spanish_words if w in text_lower)
        french_count = sum(1 for w in french_words if w in text_lower)
        german_count = sum(1 for w in german_words if w in text_lower)
        
        counts = {
            "en": english_count,
            "es": spanish_count,
            "fr": french_count,
            "de": german_count,
        }
        
        # Check for non-ASCII characters
        for char in text:
            if ord(char) > 127:
                # Non-ASCII - might indicate non-English
                if '\u4e00' <= char <= '\u9fff':
                    return "zh"  # Chinese
                elif '\u0400' <= char <= '\u04ff':
                    return "ru"  # Cyrillic
                elif '\u0900' <= char <= '\u097f':
                    return "hi"  # Hindi
        
        return max(counts, key=counts.get) if max(counts.values()) > 0 else "en"

    async def _learn_from_interaction(
        self,
        input: str,
        response: str,
        reasoning: Reasoning,
        context: dict
    ) -> None:
        """
        Update memory and learning after an interaction.
        
        Args:
            input: User input
            response: NICTO's response
            reasoning: Reasoning result
            context: Context dictionary
        """
        # Create memory event
        event = MemoryEvent(
            input=input,
            response=response,
            domain=reasoning.domain,
            complexity=1.0 - reasoning.confidence,
            user_id=context.get("user_id"),
            languages_mentioned=self._extract_languages(input),
            project_references=context.get("projects", [])
        )
        
        # Store in memory
        await self.memory.remember(event)
        
        # Learn from the interaction
        await self.learner.learn_from(input, response, reasoning)
        
        # Update user model if applicable
        if context.get("user_id"):
            user_model = await self.memory.recall_user(context["user_id"])
            if user_model:
                user_model.interaction_count += 1

    def _extract_languages(self, text: str) -> list[str]:
        """Extract programming language mentions."""
        languages = [
            "python", "javascript", "java", "c++", "c#", "ruby",
            "go", "rust", "typescript", "php", "swift", "kotlin"
        ]
        
        text_lower = text.lower()
        found = [lang for lang in languages if lang in text_lower]
        
        return found

    async def get_status(self) -> dict:
        """
        Get current status of the brain.
        
        Returns:
            Dictionary with brain status information
        """
        return {
            "initialized": self._initialized,
            "interaction_count": self._interaction_count,
            "identity": self.identity.get_version_info(),
            "goals_summary": await self.goals.get_goal_summary(),
            "learning_report": await self.learner.get_improvement_report(),
        }

    async def reset(self) -> None:
        """
        Reset brain state for a fresh start.
        
        Note: This does not reset learned knowledge,
        only working state and temporary context.
        """
        self._interaction_count = 0
        self.memory.working.clear()
        self.emotion.reset_state()
        self.goals.start_session()

    def get_greeting(self, user_name: Optional[str] = None) -> str:
        """Get NICTO's greeting."""
        return self.identity.get_greeting(user_name)

    async def get_knowledge_stats(self) -> dict:
        """Get statistics about NICTO's knowledge."""
        return self.knowledge.get_knowledge_stats()

    async def learn_new_fact(self, content: str, domain: str, source: str = "interaction") -> None:
        """
        Manually add a new knowledge fact.
        
        Args:
            content: Fact content
            domain: Knowledge domain
            source: Source of the fact
        """
        from uuid import uuid4
        from .models import KnowledgeFact
        
        fact = KnowledgeFact(
            id=str(uuid4())[:12],
            content=content,
            domain=domain,
            confidence=0.8,
            source=source
        )
        
        await self.knowledge.learn(fact)
        
        # Record that we learned something
        self.goals.record_interaction(knowledge_added=1)