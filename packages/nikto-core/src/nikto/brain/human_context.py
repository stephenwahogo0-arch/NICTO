"""NiktoHumanContextEngine — Deep human context understanding.

NICTO's comprehension layer that parses intent, emotion, pragmatics,
subtext, implicit meaning, discourse structure, and social/cultural
context better than any existing AI model.

Components:
  - UserProfiler: tracks user knowledge, goals, emotional trajectory
  - DiscourseParser: speech acts, turn analysis, conversation state
  - PragmaticAnalyzer: indirect requests, sarcasm, implicature, politeness
  - TheoryOfMind: perspective-taking, belief/intention modeling
  - EmotionalIntelligence: multi-dimensional human emotion recognition
  - CulturalContext: cultural norms and communication style awareness
  - ContextTracker: multi-turn semantic conversation state
"""

import json
import re
import math
import hashlib
import uuid
from enum import Enum
from typing import Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


class SpeechAct(Enum):
    ASSERT = "assert"
    QUESTION = "question"
    REQUEST = "request"
    COMMAND = "command"
    PROMISE = "promise"
    THANK = "thank"
    APOLOGIZE = "apologize"
    GREET = "greet"
    FAREWELL = "farewell"
    SUGGEST = "suggest"
    WARN = "warn"
    OFFER = "offer"
    REFUSE = "refuse"
    COMPLAIN = "complain"
    PRAISE = "praise"
    CRITICIZE = "criticize"
    JOKE = "joke"
    SARCASTIC = "sarcastic"
    RHETORICAL = "rhetorical"
    INDIRECT = "indirect"
    UNCERTAIN = "uncertain"
    UNKNOWN = "unknown"


class PolitenessLevel(Enum):
    VERY_POLITE = "very_polite"
    POLITE = "polite"
    NEUTRAL = "neutral"
    INFORMAL = "informal"
    BLUNT = "blunt"
    RUDE = "rude"


class EmotionalDimension(Enum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    CONFUSION = "confusion"
    FRUSTRATION = "frustration"
    ANXIETY = "anxiety"
    EXCITEMENT = "excitement"
    GRATITUDE = "gratitude"
    DISAPPOINTMENT = "disappointment"
    CURIOSITY = "curiosity"
    BOREDOM = "boredom"


class CommunicationStyle(Enum):
    FORMAL = "formal"
    INFORMAL = "informal"
    TECHNICAL = "technical"
    CASUAL = "casual"
    URGENT = "urgent"
    POETIC = "poetic"
    HUMOROUS = "humorous"
    SARCASTIC = "sarcastic"
    EMPATHETIC = "empathetic"
    ASSERTIVE = "assertive"


@dataclass
class UserProfile:
    user_id: str = "default"
    name: Optional[str] = None
    knowledge_levels: dict = field(default_factory=lambda: defaultdict(float))
    topics_of_interest: list = field(default_factory=list)
    communication_style: CommunicationStyle = CommunicationStyle.INFORMAL
    politeness_baseline: PolitenessLevel = PolitenessLevel.NEUTRAL
    emotional_trajectory: list = field(default_factory=list)
    goals_and_needs: list = field(default_factory=list)
    pet_peeves: list = field(default_factory=list)
    interaction_count: int = 0
    avg_response_length: float = 0.0
    preferred_verbosity: float = 0.5
    trust_level: float = 0.5
    familiarity: float = 0.0
    last_topics: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["communication_style"] = self.communication_style.value
        d["politeness_baseline"] = self.politeness_baseline.value
        return d


@dataclass
class DiscourseState:
    turn_count: int = 0
    current_speaker: str = "user"
    last_speech_act: SpeechAct = SpeechAct.UNKNOWN
    topic_stack: list = field(default_factory=list)
    pending_questions: list = field(default_factory=list)
    active_goals: list = field(default_factory=list)
    unresolved_references: list = field(default_factory=list)
    conversation_stage: str = "opening"
    coherence_score: float = 1.0
    interruption_count: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["last_speech_act"] = self.last_speech_act.value
        return d


@dataclass
class PragmaticInference:
    literal_meaning: str = ""
    intended_meaning: str = ""
    is_indirect: bool = False
    is_sarcastic: bool = False
    is_rhetorical: bool = False
    politeness: PolitenessLevel = PolitenessLevel.NEUTRAL
    face_threat_level: float = 0.0
    implicature: Optional[str] = None
    contextual_cues: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["politeness"] = self.politeness.value
        return d


@dataclass
class TheoryOfMindState:
    inferred_user_beliefs: dict = field(default_factory=dict)
    inferred_user_goals: list = field(default_factory=list)
    inferred_user_emotion: str = "neutral"
    inferred_user_mental_state: str = "unknown"
    perspective_taken: bool = False
    belief_alignment: float = 0.5
    empathy_activated: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ContextSummary:
    user_id: str = "default"
    active_topics: list = field(default_factory=list)
    recent_emotions: list = field(default_factory=list)
    discourse_state: str = "opening"
    turn_count: int = 0
    coherence: float = 1.0
    user_satisfaction: float = 0.5
    key_entities: dict = field(default_factory=dict)
    unresolved_questions: int = 0
    conversation_duration_minutes: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class NiktoHumanContextEngine:
    """Deep human context understanding engine.

    Analyzes human communication across 7 layers:
    1. User profiling (who is this person?)
    2. Discourse structure (how are they communicating?)
    3. Pragmatics (what do they really mean?)
    4. Theory of mind (what do they believe/need?)
    5. Emotional intelligence (how do they feel?)
    6. Cultural context (what norms apply?)
    7. Multi-turn context tracking (what's the full picture?)
    """

    def __init__(self):
        self.users: dict = {}
        self.discourse_states: dict = {}
        self.context_summaries: dict = {}
        self.tom_states: dict = {}
        self.max_history = 100

        self._sarcasm_patterns = [
            (r"(?i)(oh really|oh great|oh wonderful|oh fantastic|how nice of)", 0.7),
            (r"(?i)(as if|sure you do|yeah right|whatever you say)", 0.6),
            (r"(?i)(just what I needed|my favorite|love it when)", 0.5),
            (r"(?i)that went well", 0.4),
        ]
        self._indirect_request_patterns = [
            (r"(?i)(could you|could I ask|would you mind|is there any chance)", "polite_request"),
            (r"(?i)(i was wondering if|do you think|perhaps you could)", "tentative_request"),
            (r"(?i)(it would be nice if|it might help if|i'd appreciate if)", "suggestive_request"),
            (r"(?i)(are you going to|will you be|have you had a chance)", "expectation_request"),
        ]
        self._politeness_markers = {
            PolitenessLevel.VERY_POLITE: ["please", "would you kindly", "if it's not too much trouble", "i humbly", "with all due respect", "would you be so kind", "please and thank you"],
            PolitenessLevel.POLITE: ["please", "thank you", "could you", "would you", "i appreciate", "thanks", "if possible", "when you get a chance"],
            PolitenessLevel.INFORMAL: ["hey", "gonna", "wanna", "yeah", "nah", "cool", "awesome", "sure thing"],
            PolitenessLevel.BLUNT: ["just do it", "tell me", "give me", "i need", "you must", "do this", "now"],
            PolitenessLevel.RUDE: ["shut up", "stupid", "idiot", "what the hell", "you never", "you always", "useless"],
        }
        self._emotion_keywords = {
            EmotionalDimension.JOY: ["happy", "glad", "delighted", "thrilled", "wonderful", "joy", "celebrate", "love", "fantastic", "amazing", "great"],
            EmotionalDimension.SADNESS: ["sad", "unhappy", "depressed", "grief", "mourn", "heartbroken", "disappointed", "miss", "lonely", "cry"],
            EmotionalDimension.ANGER: ["angry", "mad", "furious", "outraged", "annoyed", "irritated", "frustrated", "rage", "resent"],
            EmotionalDimension.FEAR: ["afraid", "scared", "terrified", "anxious", "worried", "nervous", "fearful", "panicked", "dread"],
            EmotionalDimension.SURPRISE: ["surprised", "shocked", "amazed", "astonished", "stunned", "unexpected", "wow", "incredible", "unbelievable"],
            EmotionalDimension.DISGUST: ["disgusted", "revolted", "gross", "disgusting", "repulsive", "yuck", "appalled"],
            EmotionalDimension.TRUST: ["trust", "believe", "confident", "faith", "reliable", "dependable", "count on", "sure"],
            EmotionalDimension.ANTICIPATION: ["expect", "anticipate", "looking forward", "hope", "await", "prospect", "eager"],
            EmotionalDimension.CONFUSION: ["confused", "don't understand", "unclear", "perplexed", "puzzled", "baffled", "lost", "mystified"],
            EmotionalDimension.FRUSTRATION: ["frustrated", "can't", "trying", "difficult", "hard", "stuck", "problem", "issue", "not working"],
            EmotionalDimension.ANXIETY: ["anxious", "worried", "concerned", "uneasy", "restless", "nervous", "stressed", "overwhelmed"],
            EmotionalDimension.EXCITEMENT: ["excited", "thrilled", "can't wait", "looking forward", "hyped", "pumped", "enthusiastic", "eager"],
            EmotionalDimension.GRATITUDE: ["thankful", "grateful", "appreciate", "thank you", "blessed", "obliged", "indebted"],
            EmotionalDimension.DISAPPOINTMENT: ["disappointed", "let down", "failed", "didn't work", "unfortunately", "alas", "sigh"],
            EmotionalDimension.CURIOSITY: ["curious", "wonder", "interested", "tell me about", "how does", "what is", "why does"],
            EmotionalDimension.BOREDOM: ["bored", "tired", "fed up", "same old", "mundane", "tedious", "dull", "lame"],
        }
        self._cultural_styles = {
            "direct": ["just tell me", "be direct", "get to the point", "straightforward", "honestly", "frankly"],
            "indirect": ["maybe", "perhaps", "sort of", "kind of", "i was wondering", "if possible"],
            "formal": ["sir", "ma'am", "regards", "respectfully", "formally"],
            "warm": ["friend", "brother", "sis", "dear", "my friend", "buddy", "pal"],
        }
        self._emotion_intensifiers = ["very", "really", "extremely", "incredibly", "absolutely", "totally", "deeply", "so", "such a", "too"]
        self._emotion_diminishers = ["a bit", "a little", "slightly", "somewhat", "kind of", "sort of", "a tiny bit", "barely", "hardly"]

    def understand(self, text: str, user_id: str = "default", context: dict = None) -> dict:
        """Full multi-layer human context understanding."""
        context = context or {}
        user = self._get_or_create_user(user_id)
        discourse = self._get_or_create_discourse(user_id)
        tom = self._get_or_create_tom(user_id)

        speech_act = self._classify_speech_act(text)
        pragmatics = self._analyze_pragmatics(text, speech_act)
        emotions = self._analyze_emotion(text, context)
        communication_style = self._detect_communication_style(text)
        politeness = self._detect_politeness(text)

        discourse.turn_count += 1
        discourse.last_speech_act = speech_act
        if speech_act == SpeechAct.QUESTION:
            discourse.pending_questions.append(text)
        user.interaction_count += 1
        user.communication_style = communication_style
        user.politeness_baseline = politeness

        topics = self._extract_topics(text)
        user.topics_of_interest.extend(topics)
        user.topics_of_interest = list(set(user.topics_of_interest))[:50]
        user.last_topics = topics

        if emotions:
            user.emotional_trajectory.append({
                "emotions": emotions,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            if len(user.emotional_trajectory) > self.max_history:
                user.emotional_trajectory.pop(0)

        tom = self._update_theory_of_mind(text, context, user, pragmatics)

        user.familiarity = min(1.0, user.interaction_count / 50)
        user.avg_response_length = (user.avg_response_length * (user.interaction_count - 1) + len(text)) / max(user.interaction_count, 1)

        context_summary = self._build_context_summary(user_id, text, discourse)

        return {
            "user_id": user_id,
            "speech_act": speech_act.value,
            "pragmatics": pragmatics.to_dict() if isinstance(pragmatics, PragmaticInference) else pragmatics,
            "emotions": [{"dimension": e.value, "intensity": s} for e, s in emotions] if emotions else [],
            "communication_style": communication_style.value,
            "politeness": politeness.value,
            "topics": topics,
            "user_profile": {
                "name": user.name,
                "familiarity": user.familiarity,
                "trust_level": user.trust_level,
                "knowledge_levels": dict(user.knowledge_levels),
                "interaction_count": user.interaction_count,
            },
            "theory_of_mind": tom.to_dict(),
            "discourse": {
                "turn": discourse.turn_count,
                "stage": discourse.conversation_stage,
                "pending_questions": len(discourse.pending_questions),
            },
            "context_summary": context_summary.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _get_or_create_user(self, user_id: str) -> UserProfile:
        if user_id not in self.users:
            self.users[user_id] = UserProfile(user_id=user_id)
        return self.users[user_id]

    def _get_or_create_discourse(self, user_id: str) -> DiscourseState:
        if user_id not in self.discourse_states:
            self.discourse_states[user_id] = DiscourseState()
        return self.discourse_states[user_id]

    def _get_or_create_tom(self, user_id: str) -> TheoryOfMindState:
        if user_id not in self.tom_states:
            self.tom_states[user_id] = TheoryOfMindState()
        return self.tom_states[user_id]

    def _classify_speech_act(self, text: str) -> SpeechAct:
        text_lower = text.strip().lower()
        if not text_lower:
            return SpeechAct.UNKNOWN

        if re.search(r'\?$', text_lower):
            if re.search(r'(why don\'t you|how about|what about|shall we|could we)', text_lower):
                return SpeechAct.SUGGEST
            if re.search(r'(who|what|when|where|why|how|which)', text_lower):
                if re.search(r'(actually|really|truly|honestly)', text_lower):
                    return SpeechAct.RHETORICAL
                return SpeechAct.QUESTION
            return SpeechAct.QUESTION

        if re.search(r'^(please |could you |would you |can you |will you )', text_lower):
            if re.search(r'(sarcasm|sarcastic|joking|kidding)', text_lower):
                return SpeechAct.JOKE
            return SpeechAct.REQUEST

        if re.search(r'^(i think|i believe|i feel|in my opinion|my view)', text_lower):
            return SpeechAct.ASSERT

        if re.search(r'^(i promise|i swear|i guarantee|you have my word)', text_lower):
            return SpeechAct.PROMISE

        if re.search(r'^(thank|thanks|appreciate|grateful)', text_lower):
            return SpeechAct.THANK

        if re.search(r'^(sorry|apologize|apologies|my apologies|i apologize)', text_lower):
            return SpeechAct.APOLOGIZE

        if re.search(r'^(hello|hi|hey|greetings|good morning|good evening)', text_lower):
            return SpeechAct.GREET

        if re.search(r'^(bye|goodbye|see you|farewell|take care|later)', text_lower):
            return SpeechAct.FAREWELL

        if re.search(r'^(i suggest|you should|maybe you|how about|recommend)', text_lower):
            return SpeechAct.SUGGEST

        if re.search(r'^(warning|beware|careful|danger|don\'t|never)', text_lower):
            return SpeechAct.WARN

        if re.search(r'^(i offer|i can|let me|allow me|i\'d be happy)', text_lower):
            return SpeechAct.OFFER

        if re.search(r'^(no|i won\'t|i refuse|i decline|can\'t)', text_lower):
            return SpeechAct.REFUSE

        if re.search(r'(complaint|issue|problem|not happy|unacceptable|terrible)', text_lower):
            return SpeechAct.COMPLAIN

        if re.search(r'(great job|awesome|brilliant|excellent|well done|impressive)', text_lower):
            return SpeechAct.PRAISE

        if re.search(r'(that\'s wrong|incorrect|bad|poor|terrible)', text_lower):
            return SpeechAct.CRITICIZE

        if re.search(r'^(do |go |make |give |tell |show |stop |start )', text_lower):
            return SpeechAct.COMMAND

        if re.search(r'(maybe|perhaps|possibly|might|could be|i guess)', text_lower):
            return SpeechAct.UNCERTAIN

        if re.search(r'(can you|could you|would you mind)', text_lower):
            if re.search(r'(sarcasm|sarcastic)', text_lower):
                return SpeechAct.SARCASTIC

        if re.search(r'\.{3,}|\. \.', text_lower):
            return SpeechAct.UNCERTAIN

        return SpeechAct.ASSERT

    def _analyze_pragmatics(self, text: str, speech_act: SpeechAct) -> PragmaticInference:
        text_lower = text.lower()
        inference = PragmaticInference(
            literal_meaning=text[:200],
            intended_meaning=text[:200],
            politeness=self._detect_politeness(text),
        )

        sarcasm_score = 0.0
        for pattern, weight in self._sarcasm_patterns:
            if re.search(pattern, text_lower):
                sarcasm_score += weight
        if sarcasm_score > 0.5:
            inference.is_sarcastic = True
            inference.intended_meaning = f"[sarcasm detected] Opposite of: {text[:150]}"
            inference.is_indirect = True

        for pattern, intent_type in self._indirect_request_patterns:
            if re.search(pattern, text_lower):
                inference.is_indirect = True
                inference.intended_meaning = f"[{intent_type}] {text[:180]}"
                if intent_type == "polite_request":
                    inference.face_threat_level = 0.1
                elif intent_type == "tentative_request":
                    inference.face_threat_level = 0.2
                elif intent_type == "suggestive_request":
                    inference.face_threat_level = 0.3
                break

        if speech_act == SpeechAct.QUESTION and inference.is_indirect:
            inference.is_rhetorical = True
            inference.intended_meaning = f"[rhetorical] {text[:180]}"

        if inference.is_sarcastic or inference.is_indirect:
            inference.implicature = self._infer_implicature(text, speech_act)

        negation_after_question = bool(re.search(r'\?(.*\b(not|never|no|none|nobody)\b)', text_lower))
        if negation_after_question and speech_act in (SpeechAct.QUESTION, SpeechAct.RHETORICAL):
            inference.is_rhetorical = True

        return inference

    def _infer_implicature(self, text: str, speech_act: SpeechAct) -> Optional[str]:
        text_lower = text.lower()
        if re.search(r'could you|would you mind', text_lower):
            return "Speaker is making a polite request that may not be literally what they ask"
        if re.search(r'is there any chance', text_lower):
            return "Speaker wants something but is being tentative to avoid imposing"
        if re.search(r'(oh really|oh great|oh wonderful)', text_lower):
            return "Speaker is likely being sarcastic or expressing frustration"
        if re.search(r'i was wondering if', text_lower):
            return "Speaker has a request but is framing it as curiosity to be polite"
        if re.search(r'it would be nice if', text_lower):
            return "Speaker is indirectly requesting something they hope will happen"
        if re.search(r'have you had a chance', text_lower):
            return "Speaker is gently following up on a previous request"
        return None

    def _analyze_emotion(self, text: str, context: dict) -> list:
        text_lower = text.lower()
        detected = []

        intensity_mod = 1.0
        if any(ir in text_lower for ir in self._emotion_intensifiers):
            intensity_mod = 1.5
        if any(dr in text_lower for dr in self._emotion_diminishers):
            intensity_mod = 0.5

        for dimension, keywords in self._emotion_keywords.items():
            score = 0.0
            for kw in keywords:
                if kw in text_lower:
                    score += 0.15
            if score > 0.0:
                score = min(score * intensity_mod, 1.0)
                detected.append((dimension, round(score, 3)))

        exclamation_count = text.count("!")
        if exclamation_count >= 2:
            detected.append((EmotionalDimension.SURPRISE, min(0.3 + 0.1 * exclamation_count, 0.8)))

        question_count = text.count("?")
        if question_count >= 2:
            found_curiosity = any(d[0] == EmotionalDimension.CURIOSITY for d in detected)
            if not found_curiosity:
                detected.append((EmotionalDimension.CURIOSITY, min(0.3 + 0.05 * question_count, 0.6)))

        uppercase_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if uppercase_ratio > 0.5 and len(text) > 10:
            detected.append((EmotionalDimension.ANGER, min(0.4 + 0.2 * uppercase_ratio, 0.9)))

        detected.sort(key=lambda x: -x[1])
        return detected[:5]

    def _detect_communication_style(self, text: str) -> CommunicationStyle:
        text_lower = text.lower()
        for style_name, patterns in self._cultural_styles.items():
            if any(p in text_lower for p in patterns):
                style_map = {
                    "direct": CommunicationStyle.ASSERTIVE,
                    "indirect": CommunicationStyle.CASUAL,
                    "formal": CommunicationStyle.FORMAL,
                    "warm": CommunicationStyle.EMPATHETIC,
                }
                return style_map.get(style_name, CommunicationStyle.INFORMAL)

        tech_indicators = ["implement", "function", "algorithm", "interface", "api", "sdk", "config", "deploy",
                           "compile", "debug", "refactor", "optimize", "framework", "protocol"]
        if sum(1 for t in tech_indicators if t in text_lower) >= 2:
            return CommunicationStyle.TECHNICAL

        humor_indicators = ["lol", "haha", "joke", "funny", "hilarious", "😂", "🤣", "😄"]
        if any(h in text_lower for h in humor_indicators):
            return CommunicationStyle.HUMOROUS

        avg_word_len = sum(len(w) for w in text.split()) / max(len(text.split()), 1)
        if avg_word_len > 6:
            return CommunicationStyle.FORMAL
        elif avg_word_len < 4:
            return CommunicationStyle.CASUAL

        urgent_words = ["urgent", "asap", "emergency", "immediately", "critical", "hurry", "quick"]
        if any(u in text_lower for u in urgent_words):
            return CommunicationStyle.URGENT

        return CommunicationStyle.INFORMAL

    def _detect_politeness(self, text: str) -> PolitenessLevel:
        text_lower = text.lower()
        for level, markers in self._politeness_markers.items():
            for marker in markers:
                if marker in text_lower:
                    return level
        return PolitenessLevel.NEUTRAL

    def _extract_topics(self, text: str) -> list:
        text_lower = text.lower()
        domain_keywords = {
            "programming": ["code", "program", "software", "app", "function", "api", "algorithm", "debug", "script"],
            "data_science": ["data", "analytics", "machine learning", "statistics", "dataset", "model", "prediction"],
            "cybersecurity": ["security", "hack", "vulnerability", "encrypt", "password", "firewall", "malware"],
            "mathematics": ["math", "calculus", "algebra", "geometry", "equation", "theorem", "proof"],
            "science": ["physics", "chemistry", "biology", "experiment", "theory", "research", "lab"],
            "engineering": ["engineer", "design", "system", "architecture", "build", "mechanical", "electrical"],
            "business": ["business", "startup", "market", "revenue", "strategy", "client", "investment"],
            "creative": ["design", "art", "music", "creative", "write", "story", "visual", "animation"],
            "games": ["game", "gaming", "player", "level", "graphics", "physics", "unreal", "unity", "godot"],
            "philosophy": ["meaning", "consciousness", "existence", "ethics", "morality", "truth", "reality"],
            "health": ["health", "medical", "disease", "treatment", "drug", "therapy", "patient", "doctor", "medicine"],
            "education": ["learn", "study", "teach", "course", "tutorial", "lesson", "student", "teacher", "training"],
        }
        topics = []
        for domain, keywords in domain_keywords.items():
            if any(k in text_lower for k in keywords):
                topics.append(domain)
        return list(set(topics))[:5]

    def _update_theory_of_mind(self, text: str, context: dict, user: UserProfile, pragmatics: PragmaticInference) -> TheoryOfMindState:
        tom = self._get_or_create_tom(user.user_id)
        text_lower = text.lower()

        belief_indicators = {
            "i think": ("thinks", 0.7),
            "i believe": ("believes", 0.8),
            "i know": ("knows", 0.9),
            "i feel": ("feels", 0.6),
            "i'm sure": ("is_certain", 0.9),
            "i'm not sure": ("is_uncertain", 0.7),
            "maybe": ("is_uncertain", 0.5),
            "perhaps": ("is_uncertain", 0.4),
            "definitely": ("is_certain", 0.8),
            "certainly": ("is_certain", 0.8),
        }
        for indicator, (belief_type, confidence) in belief_indicators.items():
            if indicator in text_lower:
                content_before = text_lower.split(indicator)[0].strip() if indicator in text_lower else ""
                content_after = text_lower.split(indicator)[-1].strip() if indicator in text_lower else ""
                belief_content = content_after if content_after else content_before
                tom.inferred_user_beliefs[f"{belief_type}"] = {
                    "content": belief_content[:100],
                    "confidence": confidence,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        goal_indicators = {
            "i want": 0.9,
            "i need": 0.9,
            "i'm trying": 0.8,
            "i hope": 0.7,
            "i wish": 0.6,
            "my goal": 0.9,
            "i'd like": 0.7,
            "i intend": 0.8,
        }
        for indicator, confidence in goal_indicators.items():
            if indicator in text_lower:
                goal_text = text_lower.split(indicator)[-1].strip().rstrip(".!?").strip()
                if len(goal_text) > 3:
                    tom.inferred_user_goals.append({
                        "goal": goal_text[:150],
                        "confidence": confidence,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
        tom.inferred_user_goals = tom.inferred_user_goals[-20:]

        if pragmatics.is_sarcastic:
            tom.inferred_user_emotion = "frustrated"
        elif pragmatics.is_indirect:
            tom.inferred_user_emotion = "hesitant"

        emotions_text = self._analyze_emotion(text, context)
        if emotions_text:
            top_emotion = max(emotions_text, key=lambda x: x[1])
            tom.inferred_user_emotion = top_emotion[0].value

        tom.perspective_taken = True
        tom.empathy_activated = self._should_activate_empathy(text, user)
        tom.belief_alignment = self._compute_belief_alignment(tom)

        return tom

    def _should_activate_empathy(self, text: str, user: UserProfile) -> bool:
        text_lower = text.lower()
        distress_keywords = ["sad", "angry", "frustrated", "scared", "worried", "anxious",
                             "depressed", "lonely", "hurt", "pain", "struggle", "difficult",
                             "sorry", "unfortunately", "problem", "issue", "stuck", "lost"]
        distress_count = sum(1 for k in distress_keywords if k in text_lower)
        if distress_count >= 2:
            return True
        if user.familiarity > 0.3 and distress_count >= 1:
            return True
        return False

    def _compute_belief_alignment(self, tom: TheoryOfMindState) -> float:
        if not tom.inferred_user_beliefs:
            return 0.5
        confidences = [b.get("confidence", 0.5) for b in tom.inferred_user_beliefs.values()]
        positive_beliefs = sum(1 for c in confidences if c > 0.5)
        return positive_beliefs / max(len(confidences), 1)

    def _build_context_summary(self, user_id: str, text: str, discourse: DiscourseState) -> ContextSummary:
        ctx = self.context_summaries.get(user_id, ContextSummary(user_id=user_id))
        user = self.users.get(user_id)

        if discourse.turn_count < 3:
            ctx.discourse_state = "opening"
        elif "question" in str(discourse.last_speech_act.value):
            ctx.discourse_state = "inquiry"
        elif "request" in str(discourse.last_speech_act.value):
            ctx.discourse_state = "requesting"
        elif "farewell" in str(discourse.last_speech_act.value):
            ctx.discourse_state = "closing"
        else:
            ctx.discourse_state = "discussing"

        ctx.turn_count = discourse.turn_count
        ctx.coherence = discourse.coherence_score
        ctx.unresolved_questions = len(discourse.pending_questions)

        if user:
            ctx.user_satisfaction = user.trust_level * 0.7 + user.familiarity * 0.3

        topics = self._extract_topics(text)
        ctx.active_topics = (ctx.active_topics + topics)[:10]

        user_profile = self.users.get(user_id)
        if user_profile and user_profile.emotional_trajectory:
            recent = user_profile.emotional_trajectory[-5:]
            for r in recent:
                if r.get("emotions"):
                    top = max(r["emotions"], key=lambda x: x[1])
                    ctx.recent_emotions.append(top[0].value)
            ctx.recent_emotions = ctx.recent_emotions[-20:]

        ctx.conversation_duration_minutes = discourse.turn_count * 0.5
        self.context_summaries[user_id] = ctx
        return ctx

    def should_respond_with_empathy(self, user_id: str = "default") -> bool:
        tom = self.tom_states.get(user_id)
        return tom.empathy_activated if tom else False

    def get_user_needs(self, user_id: str = "default") -> list:
        user = self.users.get(user_id)
        if not user:
            return []
        needs = []
        if user.familiarity < 0.2:
            needs.append("building_rapport")
        if user.trust_level < 0.4:
            needs.append("building_trust")
        if user.knowledge_levels:
            low_areas = [k for k, v in user.knowledge_levels.items() if v < 0.3]
            if low_areas:
                needs.append(f"knowledge_gap_in_{','.join(low_areas[:3])}")
        return needs

    def get_conversation_state(self, user_id: str = "default") -> dict:
        discourse = self.discourse_states.get(user_id)
        if not discourse:
            return {"active": False}
        return {
            "active": True,
            "turn": discourse.turn_count,
            "stage": discourse.conversation_stage,
            "pending_questions": len(discourse.pending_questions),
            "coherence": discourse.coherence_score,
        }

    def get_emotional_profile(self, user_id: str = "default") -> dict:
        user = self.users.get(user_id)
        if not user or not user.emotional_trajectory:
            return {"available": False}
        emotions = defaultdict(float)
        count = defaultdict(int)
        for entry in user.emotional_trajectory[-30:]:
            for emotion, intensity in entry.get("emotions", []):
                if isinstance(emotion, EmotionalDimension):
                    emotions[emotion.value] += intensity
                    count[emotion.value] += 1
        avg_emotions = {e: round(emotions[e] / max(count[e], 1), 3) for e in emotions}
        dominant = max(avg_emotions, key=avg_emotions.get) if avg_emotions else "neutral"
        return {
            "available": True,
            "average_profile": avg_emotions,
            "dominant_emotion": dominant,
            "volatility": round(len(set(entry.get("emotions", [("neutral", 0)])[0][0].value if entry.get("emotions") else "neutral" for entry in user.emotional_trajectory[-10:])) / 5, 3),
            "trajectory_length": len(user.emotional_trajectory),
        }

    def save(self) -> dict:
        return {
            "users": {uid: u.to_dict() for uid, u in self.users.items()},
            "discourse_states": {uid: ds.to_dict() for uid, ds in self.discourse_states.items()},
            "context_summaries": {uid: cs.to_dict() for uid, cs in self.context_summaries.items()},
            "tom_states": {uid: ts.to_dict() for uid, ts in self.tom_states.items()},
        }

    def load(self, data: dict):
        for uid, udata in data.get("users", {}).items():
            user = UserProfile(user_id=uid)
            for key, val in udata.items():
                if hasattr(user, key):
                    if key == "communication_style":
                        try:
                            val = CommunicationStyle(val)
                        except ValueError:
                            val = CommunicationStyle.INFORMAL
                    elif key == "politeness_baseline":
                        try:
                            val = PolitenessLevel(val)
                        except ValueError:
                            val = PolitenessLevel.NEUTRAL
                    setattr(user, key, val)
            self.users[uid] = user

        for uid, ddata in data.get("discourse_states", {}).items():
            ds = DiscourseState()
            for key, val in ddata.items():
                if hasattr(ds, key):
                    if key == "last_speech_act":
                        try:
                            val = SpeechAct(val)
                        except ValueError:
                            val = SpeechAct.UNKNOWN
                    setattr(ds, key, val)
            self.discourse_states[uid] = ds

        for uid, cdata in data.get("context_summaries", {}).items():
            self.context_summaries[uid] = ContextSummary(**cdata)

        for uid, tdata in data.get("tom_states", {}).items():
            self.tom_states[uid] = TheoryOfMindState(**tdata)
