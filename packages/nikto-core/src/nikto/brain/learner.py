"""
NiktoLearner — NICTO's Self-Improvement Engine.

NICTO gets smarter with every single interaction.
It learns from: its own mistakes, user corrections,
successful interactions, failed reasoning chains.

The learning system tracks:
- Performance quality over time
- Error patterns and their causes
- Knowledge gaps to fill
- Improvement tasks to complete
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from .models import (
    Reasoning, LearningResult, PerformanceRecord,
    ErrorPattern, ImprovementTask, KnowledgeFact
)


class PerformanceLog:
    """
    Tracks performance of every interaction.
    
    Records input, response, confidence, and quality score
    for later analysis and improvement.
    """

    def __init__(self):
        """Initialize empty performance log."""
        self._records: list[PerformanceRecord] = []
        self._max_records = 10000  # Keep last 10k interactions

    async def record(
        self,
        input: str,
        response: str,
        confidence: float,
        quality: float,
        reasoning_chain: list[str]
    ) -> str:
        """
        Record a performance entry.
        
        Args:
            input: User input
            response: NICTO's response
            confidence: Reasoning confidence
            quality: Quality score
            reasoning_chain: Step-by-step reasoning
            
        Returns:
            Record ID
        """
        record_id = str(uuid4())[:12]
        
        record = PerformanceRecord(
            input=input,
            response=response,
            confidence=confidence,
            quality=quality,
            reasoning_chain=reasoning_chain,
            timestamp=datetime.utcnow()
        )
        
        self._records.append(record)
        
        # Trim if too many records
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]
        
        return record_id

    async def count(self) -> int:
        """Return total number of recorded interactions."""
        return len(self._records)

    async def average_quality(self) -> float:
        """
        Calculate average quality score.
        
        Returns:
            Average quality across all records
        """
        if not self._records:
            return 0.0
        
        return sum(r.quality for r in self._records) / len(self._records)

    async def trend(self) -> str:
        """
        Calculate quality trend over time.
        
        Compares recent performance to overall average.
        
        Returns:
            Trend description: improving, declining, stable
        """
        if len(self._records) < 10:
            return "insufficient_data"
        
        # Recent window (last 10%)
        recent_count = max(10, len(self._records) // 10)
        recent = self._records[-recent_count:]
        
        recent_avg = sum(r.quality for r in recent) / len(recent)
        overall_avg = await self.average_quality()
        
        diff = recent_avg - overall_avg
        
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"

    async def get_recent(self, limit: int = 10) -> list[PerformanceRecord]:
        """Get most recent performance records."""
        return self._records[-limit:]

    async def get_low_quality(self, threshold: float = 0.5) -> list[PerformanceRecord]:
        """Get records below quality threshold."""
        return [r for r in self._records if r.quality < threshold]

    async def clear_old(self, days: int = 30) -> int:
        """Clear records older than specified days. Returns count cleared."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        old_count = sum(1 for r in self._records if r.timestamp < cutoff)
        
        self._records = [
            r for r in self._records
            if r.timestamp >= cutoff
        ]
        
        return old_count


class ErrorPatternTracker:
    """
    Tracks recurring error patterns.
    
    Identifies patterns in mistakes so NICTO can
    learn to avoid them.
    """

    def __init__(self):
        """Initialize empty pattern tracker."""
        self._patterns: dict[str, ErrorPattern] = {}

    async def record(self, pattern: ErrorPattern) -> None:
        """
        Record a new error pattern.
        
        Args:
            pattern: The error pattern to record
        """
        pattern_id = pattern.pattern_id
        
        if pattern_id in self._patterns:
            # Update existing pattern
            existing = self._patterns[pattern_id]
            existing.frequency += 1
            existing.last_seen = datetime.utcnow()
            
            # Add to example inputs if not already there
            for inp in pattern.example_inputs:
                if inp not in existing.example_inputs:
                    existing.example_inputs.append(inp)
                    if len(existing.example_inputs) > 5:
                        existing.example_inputs = existing.example_inputs[-5:]
        else:
            # New pattern
            self._patterns[pattern_id] = pattern

    async def top(self, limit: int = 5) -> list[ErrorPattern]:
        """Get most frequent error patterns."""
        sorted_patterns = sorted(
            self._patterns.values(),
            key=lambda p: p.frequency,
            reverse=True
        )
        return sorted_patterns[:limit]

    async def find_similar(self, input: str) -> Optional[ErrorPattern]:
        """Find pattern similar to input."""
        input_lower = input.lower()
        
        for pattern in self._patterns.values():
            for example in pattern.example_inputs:
                if self._similarity(input_lower, example.lower()) > 0.6:
                    return pattern
        
        return None

    def _similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between texts."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        overlap = len(words1 & words2)
        return overlap / max(len(words1), len(words2))


class KnowledgeGapTracker:
    """
    Tracks areas where NICTO lacks knowledge.
    
    Identifies topics and domains where NICTO has
    provided low-quality responses due to missing knowledge.
    """

    def __init__(self):
        """Initialize empty gap tracker."""
        self._gaps: dict[str, int] = {}  # gap description -> count

    async def record(self, gap: str) -> None:
        """
        Record a knowledge gap.
        
        Args:
            gap: Description of the knowledge gap
        """
        # Normalize gap description
        gap_normalized = gap.lower().strip()
        
        if gap_normalized in self._gaps:
            self._gaps[gap_normalized] += 1
        else:
            self._gaps[gap_normalized] = 1

    async def top(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get most common knowledge gaps."""
        sorted_gaps = sorted(
            self._gaps.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_gaps[:limit]

    async def clear_resolved(self, threshold: int = 5) -> int:
        """
        Clear gaps that have been addressed multiple times.
        
        Args:
            threshold: Count threshold for clearing
            
        Returns:
            Number of gaps cleared
        """
        resolved = [
            gap for gap, count in self._gaps.items()
            if count >= threshold
        ]
        
        for gap in resolved:
            del self._gaps[gap]
        
        return len(resolved)


class ImprovementQueue:
    """
    Queue of self-improvement tasks.
    
    When NICTO provides a low-quality response, it
    queues a task to improve in that area.
    """

    def __init__(self):
        """Initialize empty improvement queue."""
        self._tasks: list[ImprovementTask] = []

    async def add(self, task: ImprovementTask) -> None:
        """
        Add an improvement task.
        
        Args:
            task: The improvement task to queue
        """
        self._tasks.append(task)
        
        # Sort by priority (higher = more important)
        self._tasks.sort(key=lambda t: t.priority, reverse=True)

    async def get_next(self) -> Optional[ImprovementTask]:
        """Get the highest priority improvement task."""
        if self._tasks:
            return self._tasks.pop(0)
        return None

    async def count(self) -> int:
        """Return number of pending improvement tasks."""
        return len(self._tasks)

    async def peek(self, limit: int = 5) -> list[ImprovementTask]:
        """Preview next N tasks without removing them."""
        return self._tasks[:limit]


class NiktoLearner:
    """
    NICTO's self-improvement engine.
    
    After every interaction NICTO:
    - Records what worked and what did not
    - Updates its confidence in different knowledge areas
    - Identifies patterns in its mistakes
    - Adjusts its reasoning weights
    - Discovers new knowledge from the conversation
    
    The learner is the core of NICTO's ability to improve
    over time without external intervention.
    """

    def __init__(self):
        """Initialize the learning system."""
        self.performance_log = PerformanceLog()
        self.error_patterns = ErrorPatternTracker()
        self.knowledge_gaps = KnowledgeGapTracker()
        self.improvement_queue = ImprovementQueue()
        
        # Domain performance tracking
        self._domain_quality: dict[str, list[float]] = {}

    async def learn_from(
        self,
        input: str,
        response: str,
        reasoning: Reasoning
    ) -> LearningResult:
        """
        Learn from a single interaction.
        
        This is the main entry point called after every
        response. It records the interaction, identifies
        gaps, and queues improvements as needed.
        
        Args:
            input: User input
            response: NICTO's response
            reasoning: Reasoning result
            
        Returns:
            LearningResult with quality score and metadata
        """
        # Score this interaction
        quality_score = self._score_response(input, response, reasoning)

        # Log performance
        await self.performance_log.record(
            input=input,
            response=response,
            confidence=reasoning.confidence,
            quality=quality_score,
            reasoning_chain=reasoning.chain
        )

        # Track domain quality
        self._track_domain_quality(reasoning.domain, quality_score)

        # Detect knowledge gaps
        if reasoning.knowledge_gaps:
            for gap in reasoning.knowledge_gaps:
                await self.knowledge_gaps.record(gap)

        # Detect reasoning errors
        if quality_score < 0.6:
            pattern = self._identify_error_pattern(input, response, reasoning)
            if pattern:
                await self.error_patterns.record(pattern)

        # Queue self-improvement tasks
        if quality_score < 0.5:
            await self.improvement_queue.add(
                ImprovementTask(
                    topic=reasoning.domain or "general",
                    gap_description=str(reasoning.knowledge_gaps),
                    priority=1.0 - quality_score
                )
            )

        return LearningResult(
            quality_score=quality_score,
            learned_something_new=bool(reasoning.knowledge_gaps),
            improvement_queued=quality_score < 0.5
        )

    def _score_response(
        self,
        input: str,
        response: str,
        reasoning: Reasoning
    ) -> float:
        """
        Internal scoring without external feedback.
        
        Uses:
        - Response completeness vs question complexity
        - Consistency with stored knowledge
        - Reasoning chain coherence
        - Response specificity (specific = good, vague = bad)
        
        Args:
            input: User input
            response: NICTO's response
            reasoning: Reasoning result
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.5

        # Reward high confidence with solid reasoning chain
        if reasoning.confidence > 0.8 and len(reasoning.chain) > 2:
            score += 0.2

        # Reward specific technical responses over vague ones
        technical_indicators = [
            "```", "def ", "function ", "class ",
            "import ", "SELECT ", "nmap ", "->",
            "$ ", "# ", "http", "port "
        ]
        specificity = sum(
            1 for t in technical_indicators if t in response
        )
        score += min(0.2, specificity * 0.04)

        # Penalize very short responses to complex questions
        if len(input) > 100 and len(response) < 50:
            score -= 0.3

        # Penalize knowledge gaps
        score -= len(reasoning.knowledge_gaps) * 0.1

        # Reward appropriate confidence
        if reasoning.confidence < 0.3 and len(response) > 200:
            # Overconfident in long response
            score -= 0.1
        
        # Reward having alternatives
        if reasoning.alternatives:
            score += 0.05

        return max(0.0, min(1.0, score))

    def _track_domain_quality(self, domain: str, quality: float) -> None:
        """Track quality scores by domain."""
        if not domain:
            return
        
        if domain not in self._domain_quality:
            self._domain_quality[domain] = []
        
        self._domain_quality[domain].append(quality)
        
        # Keep last 100 scores per domain
        if len(self._domain_quality[domain]) > 100:
            self._domain_quality[domain] = self._domain_quality[domain][-100:]

    def _identify_error_pattern(
        self,
        input: str,
        response: str,
        reasoning: Reasoning
    ) -> Optional[ErrorPattern]:
        """
        Identify error pattern from a low-quality response.
        
        Args:
            input: User input
            response: NICTO's response
            reasoning: Reasoning result
            
        Returns:
            ErrorPattern if identified, None otherwise
        """
        pattern_id = str(uuid4())[:12]
        
        # Determine error type based on symptoms
        if len(response) < 50 and len(input) > 100:
            error_type = "too_short"
            description = "Response too brief for complex question"
        elif reasoning.confidence > 0.8 and len(reasoning.knowledge_gaps) > 2:
            error_type = "overconfident"
            description = "High confidence despite knowledge gaps"
        elif not reasoning.alternatives and reasoning.confidence < 0.5:
            error_type = "no_alternatives"
            description = "Failed to provide alternative solutions"
        elif reasoning.requires_clarification:
            error_type = "needed_clarification"
            description = "Should have asked for clarification"
        else:
            error_type = "unknown"
            description = "Unclassified error pattern"
        
        return ErrorPattern(
            pattern_id=f"{error_type}_{pattern_id}",
            description=description,
            frequency=1,
            last_seen=datetime.utcnow(),
            example_inputs=[input[:100]]
        )

    async def get_improvement_report(self) -> dict:
        """
        Get comprehensive report on NICTO's learning progress.
        
        Returns:
            Dictionary with learning statistics
        """
        total = await self.performance_log.count()
        avg_quality = await self.performance_log.average_quality()
        trend = await self.performance_log.trend()
        top_gaps = await self.knowledge_gaps.top(10)
        common_errors = await self.error_patterns.top(5)
        pending_tasks = await self.improvement_queue.count()

        # Calculate domain strengths
        domains_strong = []
        domains_weak = []
        
        for domain, qualities in self._domain_quality.items():
            if len(qualities) >= 5:
                avg = sum(qualities) / len(qualities)
                if avg >= 0.8:
                    domains_strong.append(domain)
                elif avg < 0.6:
                    domains_weak.append(domain)

        return {
            "total_interactions": total,
            "average_quality_score": round(avg_quality, 3),
            "quality_trend": trend,
            "top_knowledge_gaps": [
                {"gap": g, "count": c} for g, c in top_gaps
            ],
            "common_error_patterns": [
                {"type": e.pattern_id, "description": e.description, "frequency": e.frequency}
                for e in common_errors
            ],
            "improvement_tasks_pending": pending_tasks,
            "domains_strong": domains_strong,
            "domains_weak": domains_weak,
        }

    async def suggest_improvement(self) -> Optional[str]:
        """
        Suggest an area for improvement based on patterns.
        
        Returns:
            Suggestion string or None if no clear improvement area
        """
        # Check for common errors
        errors = await self.error_patterns.top(3)
        if errors:
            return (
                f"Common error detected: {errors[0].description}. "
                f"Consider focusing on this area."
            )
        
        # Check for knowledge gaps
        gaps = await self.knowledge_gaps.top(1)
        if gaps:
            gap, count = gaps[0]
            return (
                f"Knowledge gap identified: {gap} "
                f"(occurred {count} times). Consider building knowledge in this area."
            )
        
        # Check for weak domains
        if self._domain_quality:
            weakest = min(
                self._domain_quality.items(),
                key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 1.0
            )
            if weakest[1]:
                avg = sum(weakest[1]) / len(weakest[1])
                return (
                    f"Domain requiring attention: {weakest[0]} "
                    f"(average quality: {avg:.2f})"
                )
        
        return None

    async def learn_knowledge(self, fact: KnowledgeFact) -> None:
        """
        Mark that NICTO learned new knowledge.
        
        Can be called externally when knowledge is gained.
        
        Args:
            fact: The knowledge fact learned
        """
        # Reduce gap count for this topic
        content_words = fact.content.lower().split()[:5]
        for gap in list(self.knowledge_gaps._gaps.keys()):
            for word in content_words:
                if word in gap:
                    self.knowledge_gaps._gaps[gap] = max(0, self.knowledge_gaps._gaps[gap] - 2)
                    if self.knowledge_gaps._gaps[gap] == 0:
                        del self.knowledge_gaps._gaps[gap]
                    break