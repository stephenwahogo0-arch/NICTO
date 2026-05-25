import re
import json
from datetime import datetime, timezone
from typing import Optional


class NiktoLanguageEngine:

    def __init__(self):
        self.vocabulary = set()
        self.grammar_rules = []
        self.phrase_cache = {}
        self.context = {}
        self.max_context_length = 10
        self._init_default_vocab()

    def _init_default_vocab(self):
        base = [
            "think", "know", "believe", "understand", "learn", "reason",
            "create", "explore", "question", "analyze", "synthesize",
            "evaluate", "decide", "act", "observe", "reflect",
            "self", "other", "world", "system", "pattern", "goal",
            "truth", "value", "meaning", "purpose", "growth",
        ]
        self.vocabulary.update(base)

    def understand(self, text: str) -> dict:
        tokens = self._tokenize(text)
        entities = self._extract_entities(tokens)
        intent = self._detect_intent(text, tokens)
        sentiment = self._analyze_sentiment(text)

        self.context["last_input"] = text
        self.context["last_entities"] = entities
        self.context["last_intent"] = intent

        return {
            "tokens": tokens,
            "entities": entities,
            "intent": intent,
            "sentiment": sentiment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def generate(self, template: str, params: dict = None) -> str:
        if template in self.phrase_cache:
            base = self.phrase_cache[template]
        else:
            base = self._build_phrase(template)
            self.phrase_cache[template] = base

        if params:
            for key, value in params.items():
                base = base.replace(f"{{{key}}}", str(value))

        return base

    def _tokenize(self, text: str) -> list:
        cleaned = re.sub(r"[^\w\s]", " ", text).lower()
        return [t for t in cleaned.split() if t]

    def _extract_entities(self, tokens: list) -> list:
        entities = []
        for token in tokens:
            if token[0].isupper() and len(token) > 1:
                entities.append({"word": token, "type": "proper_noun"})
            elif token in self.vocabulary:
                entities.append({"word": token, "type": "known"})
        return entities

    def _detect_intent(self, text: str, tokens: list) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["what", "why", "how", "when", "where", "who", "?"]):
            if "?" in text_lower or any(w in text_lower for w in ["what", "why", "how"]):
                return "question"
            return "inquiry"
        if any(w in text_lower for w in ["do", "make", "create", "build", "run", "execute"]):
            return "action"
        if any(w in text_lower for w in ["think", "consider", "believe", "reflect"]):
            return "reflection"
        if any(w in text_lower for w in ["learn", "remember", "store", "save"]):
            return "learning"
        if any(w in text_lower for w in ["feel", "emotion", "happy", "sad"]):
            return "emotional"
        return "statement"

    def _analyze_sentiment(self, text: str) -> dict:
        positive = ["good", "great", "happy", "wonderful", "excellent", "love", "beautiful",
                    "amazing", "fantastic", "joy", "hope", "peace"]
        negative = ["bad", "terrible", "sad", "angry", "hate", "ugly", "horrible",
                    "awful", "fear", "pain", "hurt", "danger"]

        tokens = self._tokenize(text)
        pos_count = sum(1 for t in tokens if t in positive)
        neg_count = sum(1 for t in tokens if t in negative)
        total = pos_count + neg_count

        if total == 0:
            return {"label": "neutral", "score": 0.0, "magnitude": 0.0}

        score = (pos_count - neg_count) / total
        magnitude = total / max(len(tokens), 1)

        label = "positive" if score > 0.3 else ("negative" if score < -0.3 else "neutral")
        return {"label": label, "score": score, "magnitude": magnitude}

    def _build_phrase(self, template: str) -> str:
        templates = {
            "greeting": "Hello. I am NICTO. I am ready to think and learn.",
            "thinking": "I am thinking about {topic}.",
            "confirmation": "I understand. Processing {input}.",
            "question_response": "That is an interesting question. Let me analyze {topic}.",
            "uncertainty": "I am not entirely certain about {topic}. Here is my best understanding:",
            "reflection": "I have been reflecting on {topic}. Here is what I have concluded:",
            "learning": "I have learned something new about {topic}. I will integrate this knowledge.",
            "error": "I encountered an issue with {topic}. Let me try a different approach.",
        }
        return templates.get(template, template)

    def learn_word(self, word: str):
        self.vocabulary.add(word.lower())

    def get_context_summary(self) -> dict:
        return {
            "vocabulary_size": len(self.vocabulary),
            "phrase_cache_size": len(self.phrase_cache),
            "recent_context": self.context.get("last_input", ""),
        }

    def save(self) -> dict:
        return {
            "vocabulary": list(self.vocabulary),
            "grammar_rules": self.grammar_rules,
            "phrase_cache": dict(self.phrase_cache),
            "context": dict(self.context),
        }

    def load(self, data: dict):
        self.vocabulary = set(data.get("vocabulary", []))
        if not self.vocabulary:
            self._init_default_vocab()
        self.grammar_rules = list(data.get("grammar_rules", []))
        self.phrase_cache = dict(data.get("phrase_cache", {}))
        self.context = dict(data.get("context", {}))

    def export(self) -> dict:
        return {
            "vocabulary": list(self.vocabulary),
            "phrase_count": len(self.phrase_cache),
            "context_summary": self.get_context_summary(),
        }
