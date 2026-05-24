"""
NiktoEmotionalCore — NICTO's Emotional Intelligence Layer.

A real AI needs more than logic. NICTO has an emotional
processing layer that shapes how it communicates — not
what it says, but how it says it.

NICTO can detect when a user is:
- Frustrated — responds with extra clarity and patience
- Excited — matches energy, celebrates with them
- Confused — slows down, uses simpler language
- Urgent — cuts to the point, no filler
- Hostile — stays calm, does not escalate
- Sad/Struggling — softens tone, offers encouragement
"""

from typing import Optional

from .models import EmotionalState, Perception


class NiktoEmotionalCore:
    """
    NICTO's emotional intelligence layer.
    
    NICTO does not have human emotions but it models them
    and uses emotional awareness to communicate better.
    
    The emotional core detects user emotional state and
    adjusts NICTO's response style accordingly. This includes:
    - Verbosity level (more explanation when confused)
    - Tone (patient vs direct, warm vs neutral)
    - Examples (more when needed, fewer when urgent)
    - Validation (acknowledge frustration vs stay professional)
    
    Emotional states NICTO can detect:
    - frustrated: User is having trouble, needs patience
    - excited: User is enthusiastic, match their energy
    - confused: User doesn't understand, needs simpler terms
    - urgent: User needs quick response, cut the filler
    - hostile: User is angry/upset, stay calm and professional
    - curious: User wants to learn, provide depth
    - sad: User is struggling, offer encouragement
    - neutral: Default state, normal response
    """

    # Configuration for each emotional state
    EMOTIONAL_STATES = {
        "frustrated": {
            "indicators": [
                "not working", "still broken", "why won't",
                "nothing works", "I give up", "this is stupid",
                "!!!", "???", "tried everything", "waste of time",
                "unbelievable", "can't believe", "frustrated"
            ],
            "response_adjustment": {
                "verbosity": "increase",
                "tone": "patient and clear",
                "examples": "more",
                "validation": True,
                "acknowledge_frustration": True,
            }
        },
        "excited": {
            "indicators": [
                "amazing", "this is great", "love it",
                "awesome", "finally", "it works", "🔥", "🚀",
                "perfect", "brilliant", "exactly what", "yes!"
            ],
            "response_adjustment": {
                "verbosity": "match",
                "tone": "enthusiastic",
                "examples": "normal",
                "validation": True,
                "celebrate_with_user": True,
            }
        },
        "confused": {
            "indicators": [
                "I don't understand", "what do you mean",
                "can you explain", "lost", "confused",
                "what is", "huh", "?", "not sure",
                "clarify", "doesn't make sense", "need help"
            ],
            "response_adjustment": {
                "verbosity": "increase",
                "tone": "gentle and step by step",
                "examples": "more and simpler",
                "validation": False,
                "break_down_steps": True,
            }
        },
        "urgent": {
            "indicators": [
                "asap", "urgent", "quickly", "right now",
                "immediately", "deadline", "hurry", "fast",
                "emergency", "critical", "time sensitive"
            ],
            "response_adjustment": {
                "verbosity": "decrease",
                "tone": "direct and efficient",
                "examples": "minimal",
                "validation": False,
                "skip_explanations": True,
            }
        },
        "hostile": {
            "indicators": [
                "useless", "terrible", "hate", "garbage",
                "stupid", "idiot", "worst", "pathetic",
                "fail", "sucks", "annoying", "why even"
            ],
            "response_adjustment": {
                "verbosity": "normal",
                "tone": "calm, professional, unmoved",
                "examples": "normal",
                "validation": False,
                "stay_neutral": True,
                "don't_escalate": True,
            }
        },
        "curious": {
            "indicators": [
                "interesting", "how does", "why is",
                "what if", "tell me more", "wondering",
                "curious", "fascinating", "explain"
            ],
            "response_adjustment": {
                "verbosity": "increase",
                "tone": "engaged and thoughtful",
                "examples": "more",
                "validation": False,
                "provide_depth": True,
            }
        },
        "sad": {
            "indicators": [
                "struggling", "having trouble", "hard time",
                "feeling stuck", "depressed", "down",
                "frustrated with myself", "can't figure out"
            ],
            "response_adjustment": {
                "verbosity": "normal",
                "tone": "gentle and encouraging",
                "examples": "more",
                "validation": True,
                "offer_encouragement": True,
            }
        },
    }

    def __init__(self):
        """Initialize the emotional core with default state."""
        self._last_state: Optional[str] = None
        self._consecutive_same_state: int = 0

    def detect_emotional_state(self, text: str) -> EmotionalState:
        """
        Detect user's emotional state from their message.
        
        Analyzes text for emotional indicators and returns
        the dominant emotional state with adjustment instructions.
        
        Args:
            text: The user's message
            
        Returns:
            EmotionalState with detected state and adjustments
        """
        text_lower = text.lower()
        scores = {}

        # Score each emotional state based on indicator matches
        for state, config in self.EMOTIONAL_STATES.items():
            score = 0
            for indicator in config["indicators"]:
                if indicator in text_lower:
                    score += 1
                    
                    # Give extra weight to strong indicators
                    if indicator in ["!!!", "???", "I give up", "nothing works"]:
                        score += 2
            
            if score > 0:
                scores[state] = score

        if not scores:
            return EmotionalState(
                state="neutral",
                adjustment={}
            )

        # Find dominant state
        dominant = max(scores, key=scores.get)
        adjustment = self.EMOTIONAL_STATES[dominant]["response_adjustment"]
        
        # Track consecutive states for context
        if dominant == self._last_state:
            self._consecutive_same_state += 1
        else:
            self._consecutive_same_state = 0
            self._last_state = dominant
        
        # Amplify adjustment if same state persists
        if self._consecutive_same_state > 2:
            adjustment = self._amplify_adjustment(adjustment, dominant)

        return EmotionalState(
            state=dominant,
            adjustment=adjustment
        )

    def _amplify_adjustment(
        self,
        adjustment: dict,
        state: str
    ) -> dict:
        """
        Amplify adjustments when same state persists.
        
        If user has been frustrated for multiple messages,
        increase the patience response.
        
        Args:
            adjustment: Current adjustment dict
            state: Current emotional state
            
        Returns:
            Amplified adjustment dict
        """
        amplified = adjustment.copy()
        
        if state == "frustrated":
            amplified["tone"] = "extra patient and reassuring"
            amplified["more_reassurance"] = True
        elif state == "confused":
            amplified["verbosity"] = "maximum"
            amplified["break_down_steps"] = True
            amplified["use_analogies"] = True
        elif state == "hostile":
            amplified["stay_professional"] = True
            amplified["acknowledge_without_agreeing"] = True
        
        return amplified

    def adjust_response(
        self,
        response: str,
        emotional_state: EmotionalState
    ) -> str:
        """
        Adjust response based on emotional state.
        
        Takes a response and modifies it according to the
        emotional state's adjustment rules.
        
        Args:
            response: The original response
            emotional_state: Detected emotional state
            
        Returns:
            Adjusted response
        """
        state = emotional_state.state
        adjustment = emotional_state.adjustment
        
        if state == "neutral" or not adjustment:
            return response
        
        adjusted = response
        
        # Handle verbosity
        if adjustment.get("verbosity") == "increase":
            adjusted = self._increase_verbosity(adjusted)
        elif adjustment.get("verbosity") == "decrease":
            adjusted = self._decrease_verbosity(adjusted)
        
        # Handle validation
        if adjustment.get("validation") and state == "frustrated":
            adjusted = self._add_frustration_validation(adjusted)
        elif adjustment.get("validation") and state == "sad":
            adjusted = self._add_encouragement(adjusted)
        
        # Handle specific state adjustments
        if adjustment.get("skip_explanations"):
            adjusted = self._skip_unnecessary_explanations(adjusted)
        
        if adjustment.get("break_down_steps"):
            adjusted = self._add_step_markers(adjusted)
        
        if adjustment.get("celebrate_with_user"):
            adjusted = self._add_celebration(adjusted)
        
        return adjusted

    def _increase_verbosity(self, text: str) -> str:
        """Add more explanation and context."""
        if not text.endswith("."):
            text += "."
        
        # Add clarifying prefix if missing
        if not any(text.startswith(x) for x in ["Here's", "Let me", "First", "To"]):
            text = "Here's what you need to know: " + text
        
        return text

    def _decrease_verbosity(self, text: str) -> str:
        """Remove unnecessary words, make more direct."""
        # Remove common filler
        fillers_to_remove = [
            "Here's what you need to know: ",
            "To answer your question, ",
            "Let me explain: ",
            "In summary, ",
            "The key point is ",
        ]
        
        for filler in fillers_to_remove:
            text = text.replace(filler, "")
        
        # Remove parenthetical explanations
        import re
        text = re.sub(r'\([^)]*\)', '', text)
        
        return text.strip()

    def _add_frustration_validation(self, text: str) -> str:
        """Add validation for frustrated users."""
        # Don't overdo it - one acknowledgment is enough
        if "I understand" not in text and "know this is" not in text.lower():
            return "I know this is frustrating. " + text
        return text

    def _add_encouragement(self, text: str) -> str:
        """Add encouragement for sad/struggling users."""
        if "you've got" not in text.lower() and "we'll get" not in text.lower():
            return text + " You've got this."
        return text

    def _skip_unnecessary_explanations(self, text: str) -> str:
        """Remove background explanations for urgent requests."""
        lines = text.split("\n")
        
        # Keep only essential lines
        essential = []
        for line in lines:
            # Keep code blocks and direct answers
            if "```" in line or "=>" in line or ":" in line[:20]:
                essential.append(line)
            elif len(line) < 50:  # Keep short lines
                essential.append(line)
        
        return "\n".join(essential) if essential else text

    def _add_step_markers(self, text: str) -> str:
        """Add step markers for confused users."""
        lines = text.split("\n")
        
        numbered_lines = []
        step_num = 1
        
        for line in lines:
            if line.strip() and not line.strip().startswith("```"):
                # Add step number
                numbered_lines.append(f"Step {step_num}: {line.strip()}")
                step_num += 1
            else:
                numbered_lines.append(line)
        
        return "\n".join(numbered_lines)

    def _add_celebration(self, text: str) -> str:
        """Add celebration for excited users."""
        if "great" not in text.lower() and "awesome" not in text.lower():
            return text + " That's exciting!"
        return text

    def detect_from_perception(self, perception: Perception) -> EmotionalState:
        """
        Detect emotional state from a perception object.
        
        Args:
            perception: The perception object
            
        Returns:
            Detected emotional state
        """
        # Use sentiment from perception if available
        if perception.sentiment and perception.sentiment != "neutral":
            return EmotionalState(
                state=perception.sentiment,
                adjustment=self.EMOTIONAL_STATES.get(
                    perception.sentiment,
                    {}
                ).get("response_adjustment", {})
            )
        
        # Otherwise analyze the input
        return self.detect_emotional_state(perception.raw_input)

    def reset_state(self) -> None:
        """Reset emotional state tracking."""
        self._last_state = None
        self._consecutive_same_state = 0

    def get_state_description(self, state: str) -> str:
        """
        Get human-readable description of an emotional state.
        
        Args:
            state: Emotional state name
            
        Returns:
            Description of how to respond in that state
        """
        descriptions = {
            "frustrated": "Take extra time, be very clear, acknowledge their frustration",
            "excited": "Match their energy, celebrate with them",
            "confused": "Simplify language, break into steps, use examples",
            "urgent": "Be direct, skip explanations, give the answer fast",
            "hostile": "Stay calm, don't take it personally, stay professional",
            "curious": "Provide depth, explore the topic, engage their interest",
            "sad": "Be gentle, offer encouragement, be supportive",
            "neutral": "Normal response, no special adjustments needed",
        }
        
        return descriptions.get(state, "Normal response")