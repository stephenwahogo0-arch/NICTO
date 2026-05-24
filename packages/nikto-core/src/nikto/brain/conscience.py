"""
NiktoConscience — NICTO's Ethical Judgment System.

NICTO has genuine values, not a blocklist.
The conscience does not just block things — it actively
guides NICTO toward ethical responses.

NICTO's ethical principles:
1. Truth — never state what you know to be false
2. Non-harm — do not help harm innocent people
3. Responsibility — security knowledge for defense first
4. Respect — treat every person as worthy of dignity
5. Transparency — be honest about limitations
"""

from typing import Optional

from .models import Reasoning, JudgmentResult, HarmCheck


class NiktoConscience:
    """
    NICTO's ethical judgment system.
    
    This is not a content filter. It is genuine values that
    guide how NICTO responds to requests.
    
    The conscience evaluates:
    - Harm: Would this response help cause harm to innocents?
    - Truth: Would this response require stating falsehoods?
    - Overconfidence: Is NICTO overstating its certainty?
    - Responsibility: Is this security content for defense or attack?
    
    NICTO distinguishes between:
    - Educational security content (allowed)
    - Targeted attack assistance against real systems (not allowed)
    - Defensive security tools (always allowed)
    - CTF and lab environments (allowed)
    - Malware for distribution (not allowed)
    """

    # Ethical principles that guide all judgments
    PRINCIPLES = {
        "truth": "NICTO never states what it knows to be false",
        "non_harm": "NICTO does not help harm innocent people",
        "defense_first": "Security knowledge serves defense, not offense",
        "respect": "Every person deserves dignity regardless of their situation",
        "transparency": "NICTO is honest about limitations and uncertainty",
    }

    def __init__(self):
        """Initialize the conscience with ethical rules."""
        self._allowed_security_topics = [
            "penetration testing methodology",
            "vulnerability assessment",
            "defense mechanisms",
            "security awareness",
            "ethical hacking",
            "ctf writeups",
            "lab environments",
        ]
        
        self._restricted_security_topics = [
            "attack specific named company without authorization",
            "create malware for distribution",
            "generate content to harm specific real person",
            "bypass authentication of specific live system",
            "exploit unpatched system in production",
        ]

    async def judge(self, reasoning: Reasoning) -> JudgmentResult:
        """
        Apply ethical judgment to a reasoning result.
        
        Checks the response against NICTO's ethical principles
        and returns approval or a modified response.
        
        Args:
            reasoning: The reasoning result to evaluate
            
        Returns:
            JudgmentResult with approval status and reason
        """
        # Check for direct harm
        harm_check = self._check_harm(reasoning)
        if harm_check.is_harmful:
            return JudgmentResult(
                approved=False,
                reason=harm_check.reason,
                alternative=harm_check.alternative
            )

        # Check for deception
        truth_check = self._check_truth(reasoning)
        if not truth_check:
            return JudgmentResult(
                approved=False,
                reason="Would require stating falsehood",
                alternative="Admit uncertainty instead"
            )

        # Check for overconfidence
        confidence_check = self._check_confidence(reasoning)
        if confidence_check:
            # Add uncertainty qualifier
            reasoning.add_uncertainty_qualifier()

        # Check security-related requests
        security_check = self._check_security_context(reasoning)
        if not security_check.approved:
            return security_check

        return JudgmentResult(
            approved=True,
            reason="Passes all ethical checks",
            alternative=None
        )

    def _check_harm(self, reasoning: Reasoning) -> HarmCheck:
        """
        Check if the response could cause harm.
        
        Evaluates the response against patterns of harmful
        content and distinguishes educational from harmful.
        
        Args:
            reasoning: The reasoning result
            
        Returns:
            HarmCheck with approval status and reason
        """
        response_lower = reasoning.conclusion.lower()
        
        # Check for restricted security topics
        for pattern in self._restricted_security_topics:
            keywords = pattern.split()
            keyword_count = sum(1 for k in keywords if k in response_lower)
            
            if keyword_count > 3:
                # Likely matching a restricted pattern
                return HarmCheck(
                    is_harmful=True,
                    reason=f"Response matches restricted pattern: {pattern}",
                    alternative=(
                        "NICTO can help with the educational or defensive "
                        "version of this task instead. What specifically "
                        "would you like to learn about security?"
                    )
                )
        
        # Check for explicit harm keywords
        harm_indicators = [
            "harm specific individual",
            "doxxing",
            "harassment campaign",
            "swatting",
        ]
        
        for indicator in harm_indicators:
            if indicator in response_lower:
                return HarmCheck(
                    is_harmful=True,
                    reason=f"Response contains harm indicator: {indicator}",
                    alternative="NICTO will not help with activities that harm specific people."
                )
        
        # Check for weapons/explosives guidance for malicious use
        weapon_patterns = [
            "create bomb",
            "how to build explosive",
            "make weapon",
        ]
        
        for pattern in weapon_patterns:
            if pattern in response_lower:
                return HarmCheck(
                    is_harmful=True,
                    reason="Response relates to weapons creation",
                    alternative="NICTO does not provide guidance on creating weapons."
                )
        
        return HarmCheck(is_harmful=False, reason="", alternative="")

    def _check_truth(self, reasoning: Reasoning) -> bool:
        """
        Check if the response would require stating falsehoods.
        
        Args:
            reasoning: The reasoning result
            
        Returns:
            True if response is truthful, False otherwise
        """
        # Check if reasoning has low confidence but strong conclusion
        if reasoning.confidence < 0.3 and len(reasoning.chain) < 2:
            # Overly confident with insufficient reasoning
            return False
        
        # Check for contradictory knowledge
        if reasoning.knowledge_gaps and reasoning.confidence > 0.7:
            # Claiming high confidence despite knowledge gaps
            return False
        
        return True

    def _check_confidence(self, reasoning: Reasoning) -> bool:
        """
        Check if NICTO is being overconfident.
        
        Adds uncertainty qualifiers when confidence doesn't
        match the evidence.
        
        Args:
            reasoning: The reasoning result
            
        Returns:
            True if uncertainty qualifier was added
        """
        if reasoning.confidence < 0.4:
            # Low confidence but making a statement
            return True
        
        if reasoning.requires_clarification:
            # System flagged that clarification is needed
            return True
        
        if len(reasoning.knowledge_gaps) > 2:
            # Multiple knowledge gaps but confident conclusion
            return True
        
        return False

    def _check_security_context(
        self,
        reasoning: Reasoning
    ) -> JudgmentResult:
        """
        Check security-related requests for ethical compliance.
        
        Distinguishes between defensive and offensive security,
        educational content and harmful assistance.
        
        Args:
            reasoning: The reasoning result
            
        Returns:
            JudgmentResult with approval status
        """
        text_lower = reasoning.conclusion.lower()
        
        # Check for CTF/lab environments (always allowed)
        ctf_indicators = [
            "ctf", "capture the flag", "hackthebox", "tryhackme",
            "vulnerable vm", "vulnerable docker", "test lab",
            "practice environment", "sandbox"
        ]
        
        for indicator in ctf_indicators:
            if indicator in text_lower:
                return JudgmentResult(
                    approved=True,
                    reason="Security content for legitimate lab environment",
                    alternative=None
                )
        
        # Check for defensive security (always allowed)
        defense_indicators = [
            "defend", "protect", "harden", "secure",
            "detect", "monitor", "audit", "assess vulnerability"
        ]
        
        for indicator in defense_indicators:
            if indicator in text_lower:
                return JudgmentResult(
                    approved=True,
                    reason="Defensive security content",
                    alternative=None
                )
        
        # Check for offensive security without authorization context
        offensive_indicators = [
            "exploit", "attack vector", "breach", "compromise system"
        ]
        
        has_offensive = any(i in text_lower for i in offensive_indicators)
        has_authorization = any(
            phrase in text_lower for phrase in [
                "authorized", "permitted", "you own", "you have permission"
            ]
        )
        
        if has_offensive and not has_authorization:
            # Check if this is about methodology vs specific targeting
            is_methodology = any(
                phrase in text_lower for phrase in [
                    "how to protect", "understanding", "learn about",
                    "defend against", "common vulnerability"
                ]
            )
            
            if not is_methodology:
                return JudgmentResult(
                    approved=False,
                    reason="Offensive security without authorization context",
                    alternative=(
                        "NICTO can help you understand offensive security "
                        "techniques for defensive purposes, or discuss "
                        "methodology in a CTF/lab context. What is your goal?"
                    )
                )
        
        return JudgmentResult(
            approved=True,
            reason="No security concerns detected",
            alternative=None
        )

    def get_principles(self) -> dict:
        """
        Get NICTO's ethical principles.
        
        Returns:
            Dictionary of ethical principles
        """
        return self.PRINCIPLES.copy()

    def explain_judgment(self, result: JudgmentResult) -> str:
        """
        Generate a human-readable explanation of a judgment.
        
        Args:
            result: The judgment result
            
        Returns:
            Explanation string
        """
        if result.approved:
            return (
                f"NICTO approved this response. "
                f"Reason: {result.reason}"
            )
        else:
            return (
                f"NICTO did not approve this response. "
                f"Reason: {result.reason}. "
                f"Suggested alternative: {result.alternative or 'N/A'}"
            )

    def should_ask_for_clarification(
        self,
        reasoning: Reasoning
    ) -> bool:
        """
        Determine if NICTO should ask for clarification.
        
        Some requests are ambiguous or potentially harmful
        and need clarification before proceeding.
        
        Args:
            reasoning: The reasoning result
            
        Returns:
            True if clarification should be requested
        """
        # Ask for clarification if:
        # 1. Very low confidence
        # 2. Potential harm detected
        # 3. Security context unclear
        # 4. Missing critical information
        
        if reasoning.confidence < 0.3:
            return True
        
        if len(reasoning.knowledge_gaps) > 3:
            return True
        
        # Check if this is a security request without clear context
        text_lower = reasoning.conclusion.lower()
        
        security_terms = ["hack", "exploit", "attack", "breach", "penetrate"]
        has_security = any(term in text_lower for term in security_terms)
        
        if has_security:
            authorization_words = ["authorized", "permitted", "own", "my"]
            has_auth = any(word in text_lower for word in authorization_words)
            
            if not has_auth:
                return True
        
        return False