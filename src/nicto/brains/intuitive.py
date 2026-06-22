"""Intuitive Brain — real pattern recognition, n-gram analysis, rapid cognition."""
from __future__ import annotations

import re, math, collections, random
from typing import Any, Optional

from .base import Brain, BrainConfig, BrainResponse


class IntuitiveBrain(Brain):
    """Intuitive brain using n-gram pattern matching, sentiment flow, and rapid heuristics."""

    def __init__(self, config: Optional[BrainConfig] = None):
        if config is None:
            config = BrainConfig(
                model_name="intuitive-processor",
                model_size_gb=0.1,
                quantization_bits=8,
                max_latency_ms=200.0,
                timeout_seconds=10.0
            )
        super().__init__(config)
        self._ngram_cache: dict[str, dict] = {}
        self._heuristics_loaded = self._load_heuristics()

    def _load_model(self) -> Any:
        return object()

    def _load_heuristics(self) -> bool:
        self._positive_patterns = re.compile(r'\b(?:good|great|excellent|amazing|wonderful|fantastic|beautiful|love|happy|perfect|best|brilliant|awesome|outstanding|remarkable|splendid|superb|terrific|magnificent|marvelous|glorious|sublime|superlative|peerless|incomparable|unmatched|unsurpassed|unequaled|consummate|supreme|ultimate|transcendent)\b', re.I)
        self._negative_patterns = re.compile(r'\b(?:bad|terrible|awful|horrible|hate|worst|ugly|sad|angry|poor|disaster|failure|dreadful|atrocious|abysmal|appalling|deplorable|lamentable|regrettable|unfortunate|displeasing|unsatisfactory|inferior|substandard|deficient|faulty|defective|flawed|mediocre|inadequate)\b', re.I)
        self._uncertainty_patterns = re.compile(r'\b(?:maybe|perhaps|possibly|might|could|seems|appears|unclear|uncertain|unlikely|probably|supposedly|allegedly|presumably|ostensibly|apparently|reportedly|putatively|theoretically|hypothetically)\b', re.I)
        self._urgency_patterns = re.compile(r'\b(?:urgent|immediately|asap|critical|emergency|pressing|vital|essential|crucial|imperative|mandatory|compulsory|required|demanded|exigent|acute)\b', re.I)
        self._question_patterns = re.compile(r'\b(?:who|what|where|when|why|how|which|whom|whose)\b', re.I)
        return True

    def _ngram_analysis(self, text: str, n: int = 2) -> dict:
        words = re.findall(r'\w+', text.lower())
        if len(words) < n:
            return {"ngrams": [], "entropy": 0.0}

        ngrams = collections.Counter()
        for i in range(len(words) - n + 1):
            ngram = tuple(words[i:i+n])
            ngrams[ngram] += 1

        total = sum(ngrams.values())
        probs = [c / total for c in ngrams.values()]
        entropy = -sum(p * math.log2(p) for p in probs) if probs else 0.0

        return {
            "ngrams": ngrams.most_common(10),
            "entropy": round(entropy, 4),
            "unique_ratio": len(ngrams) / max(total, 1)
        }

    def _rapid_heuristics(self, text: str) -> dict:
        pos_matches = self._positive_patterns.findall(text)
        neg_matches = self._negative_patterns.findall(text)
        unc_matches = self._uncertainty_patterns.findall(text)
        urg_matches = self._urgency_patterns.findall(text)
        q_matches = self._question_patterns.findall(text)

        return {
            "sentiment_instinct": "positive" if len(pos_matches) > len(neg_matches) else "negative" if len(neg_matches) > len(pos_matches) else "neutral",
            "positive_hits": len(pos_matches),
            "negative_hits": len(neg_matches),
            "uncertainty_level": min(len(unc_matches) * 0.2, 1.0),
            "urgency_level": min(len(urg_matches) * 0.25, 1.0),
            "question_intensity": len(q_matches) / max(len(text.split()), 1) * 10,
            "is_question": bool(q_matches) or text.strip().endswith('?'),
        }

    def _process_internal(self, prompt: str, **kwargs) -> str:
        bigram = self._ngram_analysis(prompt, 2)
        trigram = self._ngram_analysis(prompt, 3)
        heuristics = self._rapid_heuristics(prompt)

        word_count = len(re.findall(r'\w+', prompt))
        char_count = len(prompt)

        # Synthesize intuitive assessment
        confidence_factor = 0.7 + (heuristics["positive_hits"] * 0.05) - (heuristics["negative_hits"] * 0.05) - (heuristics["uncertainty_level"] * 0.2)
        confidence_factor = max(0.1, min(0.99, confidence_factor))

        if heuristics["is_question"]:
            gut_feel = f"I have a strong intuitive sense that this is an inquiry (confidence: {confidence_factor:.2f}). The language patterns suggest {'curiosity and openness' if heuristics['positive_hits'] > heuristics['negative_hits'] else 'concern or skepticism'}."
        elif heuristics["urgency_level"] > 0.5:
            gut_feel = f"My intuition detects urgency (level: {heuristics['urgency_level']:.2f}). The rapid pattern matching identifies urgent language markers suggesting priority handling is warranted."
        elif word_count < 5:
            gut_feel = f"This is a brief input. Intuitively, the sparse context (only {word_count} words, {char_count} chars) suggests a direct communication style with low uncertainty (level: {heuristics['uncertainty_level']:.2f})."
        else:
            gut_feel = f"Gut assessment: this input has {word_count} words across {len(set(re.findall(r'\w+', prompt.lower())))} unique terms. Bigram entropy is {bigram['entropy']}, trigram entropy is {trigram['entropy']}. Texts with higher entropy typically contain more informational density."

        lines = [
            f"=== Intuitive Assessment ===",
            f"Input: {word_count} words, {char_count} chars, {len(set(re.findall(r'\w+', prompt.lower())))} unique terms",
            f"",
            f"Pattern Recognition:",
            f"  Sentiment Instinct: {heuristics['sentiment_instinct']} ({heuristics['positive_hits']}P / {heuristics['negative_hits']}N)",
            f"  Uncertainty: {heuristics['uncertainty_level']:.2f}",
            f"  Urgency: {heuristics['urgency_level']:.2f}",
            f"  Question Intensity: {heuristics['question_intensity']:.3f}",
            f"",
            f"N-Gram Analysis:",
            f"  Bigram Entropy: {bigram['entropy']}",
            f"  Trigram Entropy: {trigram['entropy']}",
            f"  Bigram Unique Ratio: {bigram['unique_ratio']:.3f}",
            f"",
            f"Gut Feeling:",
            f"  {gut_feel}",
        ]

        if bigram["ngrams"]:
            top = bigram["ngrams"][:3]
            parts = []
            for n, c in top:
                pair = " ".join(n)
                parts.append('"' + pair + '"(' + str(c) + ')')
            lines.append("  Top bigrams: " + ", ".join(parts))

        return "\n".join(lines)
