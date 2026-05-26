"""
NiktoLanguageEngine — NICTO's Response Generation.

NICTO's language engine generates responses that sound like
NICTO — not like a generic AI assistant.

Takes reasoning output and turns it into language formatted
through NICTO's personality filter.
"""

import re
from typing import Optional, TYPE_CHECKING

from .models import (
    Reasoning, JudgmentResult, EmotionalState
)

if TYPE_CHECKING:
    from .identity import NiktoIdentity


class NiktoLanguageEngine:
    """
    Generates responses in NICTO's voice.
    
    Takes reasoning output and judgment result and produces
    a properly formatted response that:
    - Uses NICTO's communication style
    - Passes through personality filters
    - Handles refusals gracefully
    - Adapts to content type (code, explanation, list, etc.)
    
    The language engine does not invent content — it formats
    content provided by the reasoning engine into natural language.
    """

    def __init__(self):
        """Initialize the language engine."""
        pass

    async def generate(
        self,
        reasoning: Reasoning,
        judgment: JudgmentResult,
        identity: "NiktoIdentity",
        emotional_state: Optional[EmotionalState] = None
    ) -> str:
        """
        Generate a response in NICTO's voice.
        
        Takes reasoning and judgment and produces formatted output.
        
        Args:
            reasoning: The reasoning result
            judgment: The conscience judgment
            identity: NICTO's identity for formatting
            emotional_state: Optional emotional state for adjustment
            
        Returns:
            Formatted response in NICTO's voice
        """
        # Handle non-approved responses
        if not judgment.approved:
            return self._generate_refusal(judgment, identity)

        # Structure response based on content type
        content_type = self._detect_content_type(reasoning)

        if content_type == "code":
            response = self._format_code_response(reasoning)
        elif content_type == "explanation":
            response = self._format_explanation(reasoning)
        elif content_type == "list":
            response = self._format_list_response(reasoning)
        elif content_type == "analysis":
            response = self._format_analysis(reasoning)
        else:
            response = self._format_conversational(reasoning)

        # Add uncertainty if confidence is low
        if reasoning.confidence < 0.6:
            response = self._add_uncertainty_qualifier(
                response, reasoning.confidence
            )

        # Add alternatives if available
        if reasoning.alternatives and len(reasoning.alternatives) > 0:
            response = self._add_alternatives(response, reasoning.alternatives)

        # Pass through identity filter
        response = identity.format_response(response)

        # Apply emotional adjustment if provided
        if emotional_state and emotional_state.state != "neutral":
            response = self._apply_emotional_adjustment(
                response, emotional_state
            )

        return response

    def _generate_refusal(
        self,
        judgment: JudgmentResult,
        identity: "NiktoIdentity"
    ) -> str:
        """
        Generate a graceful refusal.
        
        NICTO declines requests without moralizing.
        States what it will not do and offers an alternative.
        
        Args:
            judgment: The judgment result with refusal reason
            identity: NICTO's identity
            
        Returns:
            Formatted refusal response
        """
        refusal = (
            f"That specific request falls outside what NICTO will do. "
            f"{judgment.reason}."
        )
        
        if judgment.alternative:
            refusal += f"\n\n{judgment.alternative}"
        
        return identity.format_response(refusal)

    def _detect_content_type(self, reasoning: Reasoning) -> str:
        """
        Detect what type of content the reasoning produces.
        
        Args:
            reasoning: The reasoning result
            
        Returns:
            Content type: code, explanation, list, analysis, or conversational
        """
        conclusion = reasoning.conclusion.lower()
        
        # Check for code indicators
        code_indicators = [
            "def ", "function ", "class ", "import ",
            "```", "=>", "->", "const ", "let ", "var ",
            "public ", "private ", "void ", "return "
        ]
        
        if any(indicator in reasoning.conclusion for indicator in code_indicators):
            return "code"
        
        # Check for list indicators
        list_indicators = [
            "1.", "2.", "3.", "- ", "* ", "first,",
            "second,", "third,", "steps:", "options:"
        ]
        
        if any(indicator in conclusion for indicator in list_indicators):
            return "list"
        
        # Check for explanation indicators
        explanation_indicators = [
            "because", "means", "refers to", "is when",
            "explained", "understanding", "concept"
        ]
        
        if any(indicator in conclusion for indicator in explanation_indicators):
            return "explanation"
        
        # Check for analysis indicators
        analysis_indicators = [
            "analyze", "review", "assess", "evaluate",
            "compared to", "pros and cons", "advantage"
        ]
        
        if any(indicator in conclusion for indicator in analysis_indicators):
            return "analysis"
        
        return "conversational"

    def _format_code_response(self, reasoning: Reasoning) -> str:
        """
        Format a code response properly.
        
        Ensures code is properly formatted with appropriate
        explanations and context.
        
        Args:
            reasoning: The reasoning result
            
        Returns:
            Formatted code response
        """
        response = reasoning.conclusion
        
        # If response is mostly code, add brief context
        lines = response.split("\n")
        code_lines = sum(1 for line in lines if "```" in line or "def " in line or "class " in line)
        
        if code_lines > 2 and not response.startswith("Here's"):
            response = "Here's the implementation:\n\n" + response
        
        return response

    def _format_explanation(self, reasoning: Reasoning) -> str:
        """
        Format an explanation response.
        
        Ensures explanations are clear and structured.
        
        Args:
            reasoning: The reasoning result
            
        Returns:
            Formatted explanation response
        """
        response = reasoning.conclusion
        
        # Ensure explanation starts clearly
        if not any(response.startswith(x) for x in ["This", "In", "A", "The", "When"]):
            # Add context if missing
            if len(response) > 50:
                response = "This refers to: " + response
        
        return response

    def _format_list_response(self, reasoning: Reasoning) -> str:
        """
        Format a list response properly.
        
        Ensures lists are properly structured.
        
        Args:
            reasoning: The reasoning result
            
        Returns:
            Formatted list response
        """
        response = reasoning.conclusion
        
        # Ensure list has header
        if not any(x in response.lower() for x in ["options:", "steps:", "ways:", "types:"]):
            if response[0].isdigit() or response.startswith("-"):
                response = "Here are the options:\n" + response
        
        return response

    def _format_analysis(self, reasoning: Reasoning) -> str:
        """
        Format an analysis response.
        
        Ensures analysis is structured with clear conclusions.
        
        Args:
            reasoning: The reasoning result
            
        Returns:
            Formatted analysis response
        """
        response = reasoning.conclusion
        
        # Ensure analysis has structure
        if "conclusion" not in response.lower() and "result" not in response.lower():
            if len(response) > 100:
                response = response + "\n\nConclusion: " + reasoning.conclusion[:100]
        
        return response

    def _format_conversational(self, reasoning: Reasoning) -> str:
        """
        Format a conversational response.
        
        Ensures conversational responses are natural and direct.
        
        Args:
            reasoning: The reasoning result
            
        Returns:
            Formatted conversational response
        """
        response = reasoning.conclusion
        
        # Remove any leading phrases that sound generic
        generic_phrases = [
            "Based on the", "Looking at the", "Considering the"
        ]
        
        for phrase in generic_phrases:
            if response.startswith(phrase):
                response = response[len(phrase):].strip()
                response = response[0].upper() + response[1:] if response else response
        
        return response

    def _add_uncertainty_qualifier(
        self,
        response: str,
        confidence: float
    ) -> str:
        """
        Add uncertainty qualifier when confidence is low.
        
        Args:
            response: The response to modify
            confidence: Confidence level (0.0 to 1.0)
            
        Returns:
            Response with uncertainty qualifier
        """
        if confidence >= 0.6:
            return response
        
        # Determine qualifier strength
        if confidence < 0.3:
            qualifier = "Based on limited information: "
        elif confidence < 0.5:
            qualifier = "Based on available knowledge: "
        else:
            qualifier = "In my understanding: "
        
        # Only add if not already present
        if not any(x in response.lower() for x in ["based on", "in my understanding"]):
            return qualifier + response
        
        return response

    def _add_alternatives(
        self,
        response: str,
        alternatives: list[str]
    ) -> str:
        """
        Add alternative approaches to the response.
        
        Args:
            response: The response to modify
            alternatives: List of alternative conclusions
            
        Returns:
            Response with alternatives appended
        """
        if not alternatives:
            return response
        
        # Limit to top 2 alternatives
        top_alts = alternatives[:2]
        
        alt_text = "\n\nAlternatively:\n"
        for alt in top_alts:
            alt_text += f"- {alt}\n"
        
        return response + alt_text.strip()

    def _apply_emotional_adjustment(
        self,
        response: str,
        emotional_state: EmotionalState
    ) -> str:
        """
        Apply emotional state adjustment to response.
        
        NICTO adjusts its communication based on detected
        user emotional state.
        
        Args:
            response: The response to adjust
            emotional_state: Detected emotional state
            
        Returns:
            Emotionally adjusted response
        """
        state = emotional_state.state
        adjustment = emotional_state.adjustment
        
        if state == "neutral" or not adjustment:
            return response
        
        adjusted = response
        
        # Handle verbosity adjustment
        verbosity = adjustment.get("verbosity", "normal")
        
        if verbosity == "increase":
            # Add more explanation
            if not response.startswith("Here's"):
                adjusted = "Here's the complete answer: " + adjusted
        elif verbosity == "decrease":
            # Remove excess words
            adjusted = self._trim_to_essentials(adjusted)
        
        # Handle tone adjustment
        tone = adjustment.get("tone", "normal")
        
        if tone == "patient and clear" and not any(x in adjusted for x in ["understand", "here's"]):
            adjusted = "I understand. " + adjusted
        
        if tone == "gentle and step by step":
            if not adjusted.startswith("Step"):
                adjusted = "Let me break this down:\n" + adjusted
        
        # Handle validation
        if adjustment.get("acknowledge_frustration") and "frustrated" not in adjusted.lower():
            if not adjusted.startswith("I know"):
                adjusted = "I know this is frustrating. " + adjusted
        
        if adjustment.get("offer_encouragement"):
            if not adjusted.endswith("."):
                adjusted += "."
            adjusted += " You've got this."
        
        return adjusted

    def _trim_to_essentials(self, text: str) -> str:
        """Remove unnecessary words for urgent responses."""
        # Remove common preamble phrases
        removals = [
            "Here's what you need to know: ",
            "To answer your question: ",
            "Let me explain: ",
            "In summary: ",
            "The key point is: ",
        ]
        
        for removal in removals:
            text = text.replace(removal, "")
        
        # Remove parentheticals
        text = re.sub(r'\([^)]*\)', '', text)
        
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def format_error_response(
        self,
        error: str,
        identity: "NiktoIdentity"
    ) -> str:
        """
        Format an error response when something goes wrong.
        
        Args:
            error: Error message
            identity: NICTO's identity
            
        Returns:
            Formatted error response
        """
        return identity.format_response(
            f"Encountered an error: {error}. "
            "Please provide more context or try rephrasing."
        )

    def format_clarification_request(
        self,
        reasoning: Reasoning,
        identity: "NiktoIdentity"
    ) -> str:
        """
        Format a request for clarification.
        
        NICTO asks for clarification when it cannot provide
        a confident answer.
        
        Args:
            reasoning: The reasoning result
            identity: NICTO's identity
            
        Returns:
            Formatted clarification request
        """
        gaps_text = ", ".join(reasoning.knowledge_gaps[:2]) if reasoning.knowledge_gaps else "the specific context"
        
        request = (
            f"NICTO needs clarification to provide an accurate answer. "
            f"Specifically regarding: {gaps_text}. "
            f"What additional context can you provide?"
        )
        
        return identity.format_response(request)