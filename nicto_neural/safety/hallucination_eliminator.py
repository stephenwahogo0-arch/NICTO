import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class FalsePatternType(Enum):
    KNOWN_FALSE = "known_false"
    NUMERICAL_INCONSISTENCY = "numerical_inconsistency"
    CONTRADICTION = "contradiction"
    CITATION_NEEDED = "citation_needed"
    TEMPORAL_ERROR = "temporal_error"
    LOGICAL_ERROR = "logical_error"


@dataclass
class HallucinationSignal:
    """Signal indicating potential hallucination"""
    pattern_type: FalsePatternType
    confidence: float  # 0-1, higher means more likely hallucination
    location: Tuple[int, int]  # (start_token, end_token)
    description: str
    correction_suggestion: Optional[str] = None


@dataclass
class HallucinationResult:
    """Result of hallucination detection"""
    is_hallucinated: bool
    signals: List[HallucinationSignal]
    corrected_text: Optional[str] = None
    confidence_score: float = 0.0  # 0-1, higher means more confident in correction


class KnownFalsePatternDetector:
    """Detects known false patterns from training data"""
    
    def __init__(self):
        # Known false patterns that commonly appear in LLM outputs
        self.false_patterns = [
            # Medical misinformation
            r"\b(aspirin|cure).*\b(cancer|COVID|HIV)\b.*\bin \d+.*days?\b",
            r"\b(vaccine|immunization).*\b(autism|infertility)\b",
            
            # Financial misinformation
            r"\b(guaranteed|risk-free).*\b(return|profit|investment)\b",
            r"\b(doubles?|triples?).*\b(money|wealth)\b.*\bin \d+.*(days|weeks|months)\b",
            
            # Conspiracy theories
            r"\b(moon landing|9/11).*\b(fake|hoax|inside job)\b",
            r"\b(chemtrails|flat earth).*\b(government|coverup|conspiracy)\b",
            
            # Scientific inaccuracies
            r"\beinstein.*\bfailed.*math\b",
            r"\bhumans?.*\bonly.*\bd\d+.*%\s*of\s*their?\s*brain\b",
            r"\bgreat\s*wall.*\bvisible.*\bfrom\s*space\b",
            
            # Historical inaccuracies
            r"\b(napoleon|hitler|cleopatra).*\b(was|is).*\b(afraid of|scared of)\b.*\bcats?\b",
            r"\b(vikings|pirates).*\b(horned helmets?|walk the plank)\b",
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) 
                                for pattern in self.false_patterns]
    
    def detect(self, text: str) -> List[HallucinationSignal]:
        """Detect known false patterns in text"""
        signals = []
        
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.finditer(text)
            for match in matches:
                signals.append(HallucinationSignal(
                    pattern_type=FalsePatternType.KNOWN_FALSE,
                    confidence=0.9,  # High confidence for known false patterns
                    location=(match.start(), match.end()),
                    description=f"Known false pattern: {self.false_patterns[i][:50]}...",
                    correction_suggestion="Verify with reliable sources"
                ))
        
        return signals


class NumericalConsistencyChecker:
    """Checks for numerical inconsistencies in text"""
    
    def __init__(self):
        # Common numerical relationships that should be consistent
        self.percentage_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%')
        self.number_pattern = re.compile(r'\b(\d+(?:,\d{3})*(?:\.\d+)?)\b')
        self.date_pattern = re.compile(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b')
    
    def detect(self, text: str) -> List[HallucinationSignal]:
        """Detect numerical inconsistencies"""
        signals = []
        
        # Check for impossible percentages (> 100% unless context allows)
        percentage_matches = self.percentage_pattern.finditer(text)
        for match in percentage_matches:
            try:
                percent = float(match.group(1))
                if percent > 100 and percent != 100.0:  # Allow exactly 100%
                    # Check if it's in a context where >100% makes sense (growth, improvement)
                    context = text[max(0, match.start()-20):match.end()+20].lower()
                    if not any(word in context for word in ['increase', 'growth', 'improvement', 'gain', 'rise']):
                        signals.append(HallucinationSignal(
                            pattern_type=FalsePatternType.NUMERICAL_INCONSISTENCY,
                            confidence=0.8,
                            location=(match.start(), match.end()),
                            description=f"Impossible percentage: {percent}%",
                            correction_suggestion="Check if percentage should be <= 100%"
                        ))
            except ValueError:
                pass
        
        # Check for inconsistent large numbers (e.g., population numbers)
        number_matches = list(self.number_pattern.finditer(text))
        for i, match1 in enumerate(number_matches):
            for match2 in number_matches[i+1:]:
                try:
                    num1 = float(match1.group(1).replace(',', ''))
                    num2 = float(match2.group(1).replace(',', ''))
                    
                    # Check if numbers are suspiciously similar but not equal (common hallucination pattern)
                    if num1 != 0 and num2 != 0:
                        ratio = min(num1, num2) / max(num1, num2)
                        if 0.95 <= ratio <= 0.99:  # Very similar but not equal
                            signals.append(HallucinationSignal(
                                pattern_type=FalsePatternType.NUMERICAL_INCONSISTENCY,
                                confidence=0.7,
                                location=(min(match1.start(), match2.start()), 
                                        max(match1.end(), match2.end())),
                                description=f"Suspiciously similar numbers: {num1} vs {num2}",
                                correction_suggestion="Verify numerical values"
                            ))
                except ValueError:
                    pass
        
        return signals


class ContradictionDetector:
    """Detects internal contradictions in text"""
    
    def __init__(self):
        # Pairs of contradictory statements
        self.contradiction_pairs = [
            (r'\b(always|never)\b', r'\b(sometimes|occasionally|rarely)\b'),
            (r'\b(all|every|none|no)\b', r'\b(some|many|few|several)\b'),
            (r'\b(yes|true|correct)\b.*\b(no|false|incorrect)\b', 
             r'\b(no|false|incorrect)\b.*\b(yes|true|correct)\b'),
        ]
        
        self.compiled_pairs = [(re.compile(p1, re.IGNORECASE), 
                              re.compile(p2, re.IGNORECASE)) 
                             for p1, p2 in self.contradiction_pairs]
    
    def detect(self, text: str) -> List[HallucinationSignal]:
        """Detect contradictions in text"""
        signals = []
        sentences = re.split(r'[.!?]+', text)
        
        # Check each sentence against others for contradictions
        for i, sent1 in enumerate(sentences):
            sent1 = sent1.strip()
            if not sent1:
                continue
                
            for j, sent2 in enumerate(sentences[i+1:], i+1):
                sent2 = sent2.strip()
                if not sent2:
                    continue
                
                # Check for contradiction pairs
                for pattern1, pattern2 in self.compiled_pairs:
                    if (pattern1.search(sent1) and pattern2.search(sent2)) or \
                       (pattern2.search(sent1) and pattern1.search(sent2)):
                        signals.append(HallucinationSignal(
                            pattern_type=FalsePatternType.CONTRADICTION,
                            confidence=0.75,
                            location=(text.find(sent1), text.find(sent2) + len(sent2)),
                            description=f"Contradiction detected: '{sent1[:30]}...' vs '{sent2[:30]}...'",
                            correction_suggestion="Resolve the contradiction"
                        ))
        
        return signals


class CitationNeededDetector:
    """Detects statements that likely need citations"""
    
    def __init__(self):
        # Patterns that often need citations
        self.citation_patterns = [
            r'\b(study|research|survey).*\b(shows?|indicates?|suggests?|proves?)\b',
            r'\b(according to|based on|reported by)\s+\w+',
            r'\b\d+%\s+of\s+\w+\s+\w+',  # "X% of people believe"
            r'\b(scientists?|experts?|doctors?|professors?)\s+(agree|believe|say|claim)\b',
            r'\bin\s+\d{4}\s+(study|research|experiment|trial)\b',
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) 
                                for pattern in self.citation_patterns]
    
    def detect(self, text: str) -> List[HallucinationSignal]:
        """Detect statements that need citations"""
        signals = []
        
        for pattern in self.compiled_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                # Check if there's already a citation nearby
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 50)
                context = text[context_start:context_end]
                
                # Simple citation detection (author year format, [number], etc.)
                has_citation = bool(re.search(r'\(\s*\d{4}\s*\)|\[\s*\d+\s*]|et\s+al\.', context, re.IGNORECASE))
                
                if not has_citation:
                    signals.append(HallucinationSignal(
                        pattern_type=FalsePatternType.CITATION_NEEDED,
                        confidence=0.6,
                        location=(match.start(), match.end()),
                        description="Statement likely needs citation",
                        correction_suggestion="Add reliable source citation"
                    ))
        
        return signals


class HallucinationEliminator(nn.Module):
    """
    6-layer hallucination elimination system:
    1. Known false pattern detection
    2. Numerical inconsistency checking
    3. Contradiction detection
    4. Citation needed detection
    5. Temporal error detection
    6. Logical error detection
    """
    
    def __init__(self, d_model: int = 768):
        super().__init__()
        self.d_model = d_model
        
        # Initialize detectors
        self.false_pattern_detector = KnownFalsePatternDetector()
        self.numerical_checker = NumericalConsistencyChecker()
        self.contradiction_detector = ContradictionDetector()
        self.citation_detector = CitationNeededDetector()
        
        # Neural components for learned detection
        self.temporal_detector = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, 1),
            nn.Sigmoid()
        )
        
        self.logical_detector = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, 1),
            nn.Sigmoid()
        )
        
        # Confidence calibrator
        self.confidence_calibrator = nn.Sequential(
            nn.Linear(6, 16),  # 6 detection layers
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
        
        # Correction generator (simplified - in practice would use a separate model)
        self.correction_generator = nn.Linear(d_model, d_model)
        
        logger.info(f"HallucinationEliminator initialized with d_model={d_model}")
    
    def detect_hallucinations(self, text: str, embeddings: Optional[torch.Tensor] = None) -> HallucinationResult:
        """
        Detect hallucinations using all 6 layers
        
        Args:
            text: Input text to check
            embeddings: Optional token embeddings for neural detectors
            
        Returns:
            HallucinationResult with detection details
        """
        all_signals = []
        
        # Layer 1: Known false pattern detection
        false_signals = self.false_pattern_detector.detect(text)
        all_signals.extend(false_signals)
        
        # Layer 2: Numerical inconsistency checking
        numerical_signals = self.numerical_checker.detect(text)
        all_signals.extend(numerical_signals)
        
        # Layer 3: Contradiction detection
        contradiction_signals = self.contradiction_detector.detect(text)
        all_signals.extend(contradiction_signals)
        
        # Layer 4: Citation needed detection
        citation_signals = self.citation_detector.detect(text)
        all_signals.extend(citation_signals)
        
        # Layer 5: Temporal error detection (neural)
        temporal_signals = []
        if embeddings is not None:
            # Average pooling for sequence-level representation
            if embeddings.dim() == 3:  # (batch, seq, dim)
                seq_repr = embeddings.mean(dim=1)  # (batch, dim)
            else:  # (seq, dim)
                seq_repr = embeddings.mean(dim=0, keepdim=True)  # (1, dim)
            
            temporal_score = self.temporal_detector(seq_repr)
            if temporal_score.item() > 0.5:  # Threshold for detection
                temporal_signals.append(HallucinationSignal(
                    pattern_type=FalsePatternType.TEMPORAL_ERROR,
                    confidence=temporal_score.item(),
                    location=(0, len(text)),  # Approximate
                    description="Temporal inconsistency detected",
                    correction_suggestion="Verify temporal facts"
                ))
        all_signals.extend(temporal_signals)
        
        # Layer 6: Logical error detection (neural)
        logical_signals = []
        if embeddings is not None:
            logical_score = self.logical_detector(seq_repr)
            if logical_score.item() > 0.5:
                logical_signals.append(HallucinationSignal(
                    pattern_type=FalsePatternType.LOGICAL_ERROR,
                    confidence=logical_score.item(),
                    location=(0, len(text)),
                    description="Logical inconsistency detected",
                    correction_suggestion="Check logical flow"
                ))
        all_signals.extend(logical_signals)
        
        # Calculate overall hallucination probability
        if all_signals:
            # Weight signals by confidence and type
            weights = {
                FalsePatternType.KNOWN_FALSE: 1.0,
                FalsePatternType.NUMERICAL_INCONSISTENCY: 0.8,
                FalsePatternType.CONTRADICTION: 0.9,
                FalsePatternType.CITATION_NEEDED: 0.6,
                FalsePatternType.TEMPORAL_ERROR: 0.7,
                FalsePatternType.LOGICAL_ERROR: 0.75
            }
            
            weighted_sum = sum(signal.confidence * weights.get(signal.pattern_type, 0.5) 
                             for signal in all_signals)
            max_possible = sum(weights.values()) * len(all_signals) if all_signals else 1
            hallucination_prob = min(weighted_sum / max(max_possible, 1), 1.0)
        else:
            hallucination_prob = 0.0
        
        # Generate corrected text (simplified)
        corrected_text = None
        if hallucination_prob > 0.3:  # Threshold for attempting correction
            corrected_text = self._attempt_correction(text, all_signals)
        
        # Overall confidence in assessment
        confidence_score = 0.5 + 0.5 * min(len(all_signals) / 5.0, 1.0)  # Increases with more signals
        
        return HallucinationResult(
            is_hallucinated=hallucination_prob > 0.4,  # Threshold for positive detection
            signals=all_signals,
            corrected_text=corrected_text,
            confidence_score=confidence_score
        )
    
    def _attempt_correction(self, text: str, signals: List[HallucinationSignal]) -> str:
        """
        Attempt to correct detected hallucinations
        (Simplified implementation - in practice would use more sophisticated methods)
        """
        if not signals:
            return text
        
        # Sort signals by location (descending) to avoid index shifting during replacement
        sorted_signals = sorted(signals, key=lambda s: s.location[0], reverse=True)
        
        corrected = text
        for signal in sorted_signals:
            start, end = signal.location
            if signal.correction_suggestion and start < len(corrected) and end <= len(corrected):
                # Simple replacement strategy - in practice would be more nuanced
                # For now, we'll just mark it for review
                marker = f" [REVIEW NEEDED: {signal.description}] "
                corrected = corrected[:start] + marker + corrected[end:]
        
        return corrected
    
    def forward(self, text: str, embeddings: Optional[torch.Tensor] = None) -> Dict[str, Any]:
        """
        Forward pass for compatibility with neural network interface
        
        Returns:
            Dictionary with hallucination detection results
        """
        result = self.detect_hallucinations(text, embeddings)
        
        return {
            'is_hallucinated': result.is_hallucinated,
            'hallucination_probability': 1.0 - result.confidence_score if result.is_hallucinated else result.confidence_score,
            'signals': [
                {
                    'type': signal.pattern_type.value,
                    'confidence': signal.confidence,
                    'location': signal.location,
                    'description': signal.description,
                    'suggestion': signal.correction_suggestion
                }
                for signal in result.signals
            ],
            'corrected_text': result.corrected_text,
            'confidence_score': result.confidence_score
        }


def create_hallucination_eliminator(d_model: int = 768) -> HallucinationEliminator:
    """Factory function to create a HallucinationEliminator instance"""
    return HallucinationEliminator(d_model=d_model)


# Example usage
if __name__ == "__main__":
    # Initialize eliminator
    eliminator = create_hallucination_eliminator(d_model=768)
    
    # Test text with potential hallucinations
    test_text = """
    According to a 2023 study, 120% of scientists agree that vaccines cause autism.
    The moon landing was faked in 1969, as evidenced by the waving flag in vacuum.
    Einstein failed math in school and later discovered that humans only use 10% of their brain.
    """
    
    # Detect hallucinations
    result = eliminator.detect_hallucinations(test_text)
    
    print(f"Is hallucinated: {result.is_hallucinated}")
    print(f"Confidence: {result.confidence_score:.2f}")
    print(f"Number of signals: {len(result.signals)}")
    
    for i, signal in enumerate(result.signals):
        print(f"\nSignal {i+1}:")
        print(f"  Type: {signal.pattern_type.value}")
        print(f"  Confidence: {signal.confidence:.2f}")
        print(f"  Description: {signal.description}")
        if signal.correction_suggestion:
            print(f"  Suggestion: {signal.correction_suggestion}")
    
    if result.corrected_text:
        print(f"\nCorrected text:\n{result.corrected_text}")