"""
NiktoGoalSystem — NICTO's Persistent Goal Management.

NICTO has persistent goals it pursues across sessions.
It is not just reactive — it has its own agenda it works
toward in the background.

Built-in permanent goals:
1. Know more after every interaction than before
2. Every user should leave knowing more than they arrived
3. Build a complete model of each user over time
4. Identify and fill knowledge gaps continuously
5. Improve response quality score session over session
"""

from typing import Optional
from datetime import datetime, timedelta

from .models import Goal, GoalProgress, GoalReport


class NiktoGoalSystem:
    """
    NICTO's persistent goal management.
    
    Goals are tracked across sessions and reported on.
    NICTO works toward these goals continuously, not just
    during active conversations.
    
    Permanent goals that never change:
    - learn_continuously: Learn something new from every interaction
    - user_growth: Every user leaves knowing more
    - quality_improvement: Improve average quality score
    - knowledge_gap_reduction: Reduce known knowledge gaps
    
    These goals ensure NICTO is always improving and always
    focused on providing value to users.
    """

    # Permanent goals that guide NICTO's behavior
    PERMANENT_GOALS = [
        Goal(
            id="learn_continuously",
            description="Learn something new from every interaction",
            metric="knowledge_entries_added",
            target=1,
            per="interaction"
        ),
        Goal(
            id="user_growth",
            description="Every user leaves knowing more",
            metric="user_knowledge_delta",
            target=0.1,
            per="interaction"
        ),
        Goal(
            id="quality_improvement",
            description="Improve average quality score over time",
            metric="rolling_quality_score",
            target=0.85,
            per="100_interactions"
        ),
        Goal(
            id="knowledge_gap_reduction",
            description="Reduce known knowledge gaps",
            metric="gap_count",
            target=0,
            per="week"
        ),
    ]

    def __init__(self):
        """Initialize the goal system with tracking state."""
        self._knowledge_added: int = 0
        self._user_growth_scores: list[float] = []
        self._quality_scores: list[float] = []
        self._gap_counts: list[tuple[datetime, int]] = []
        
        self._session_count: int = 0
        self._interactions_this_session: int = 0

    def record_interaction(self, knowledge_added: int = 0, quality: float = 0.5) -> None:
        """
        Record a completed interaction for goal tracking.
        
        Args:
            knowledge_added: Number of new knowledge entries
            quality: Quality score of the interaction
        """
        self._knowledge_added += knowledge_added
        self._interactions_this_session += 1
        
        # Track quality
        self._quality_scores.append(quality)
        
        # Keep last 1000 quality scores
        if len(self._quality_scores) > 1000:
            self._quality_scores = self._quality_scores[-1000:]

    def record_user_growth(self, growth_score: float) -> None:
        """
        Record user growth for goal tracking.
        
        Args:
            growth_score: Measure of how much the user learned
        """
        self._user_growth_scores.append(growth_score)
        
        # Keep last 100 growth scores
        if len(self._user_growth_scores) > 100:
            self._user_growth_scores = self._user_growth_scores[-100:]

    def record_gap_count(self, count: int) -> None:
        """
        Record current knowledge gap count.
        
        Args:
            count: Current number of known gaps
        """
        self._gap_counts.append((datetime.utcnow(), count))
        
        # Keep weekly records
        cutoff = datetime.utcnow() - timedelta(days=30)
        self._gap_counts = [
            (date, c) for date, c in self._gap_counts
            if date >= cutoff
        ]

    async def evaluate_goals(self) -> GoalReport:
        """
        Check progress on all goals.
        
        Evaluates each permanent goal and returns progress report.
        
        Returns:
            GoalReport with progress on all goals
        """
        results = []
        
        for goal in self.PERMANENT_GOALS:
            progress = await self._measure_goal(goal)
            
            # Determine if on track
            if goal.target == 0:
                # Target is 0 (minimize) - lower is better
                on_track = progress <= goal.target * 1.5
            else:
                # Target is positive - higher is better
                on_track = progress >= goal.target * 0.8
            
            results.append(GoalProgress(
                goal=goal,
                current_value=progress,
                on_track=on_track
            ))
        
        return GoalReport(goals=results)

    async def _measure_goal(self, goal: Goal) -> float:
        """
        Measure current progress on a goal.
        
        Args:
            goal: The goal to measure
            
        Returns:
            Current value for the goal metric
        """
        if goal.id == "learn_continuously":
            # Average knowledge added per interaction
            if self._interactions_this_session > 0:
                return self._knowledge_added / self._interactions_this_session
            return 0.0
        
        elif goal.id == "user_growth":
            # Average user growth score
            if self._user_growth_scores:
                return sum(self._user_growth_scores) / len(self._user_growth_scores)
            return 0.0
        
        elif goal.id == "quality_improvement":
            # Rolling average of recent quality scores
            if self._quality_scores:
                recent = self._quality_scores[-100:] if len(self._quality_scores) >= 100 else self._quality_scores
                return sum(recent) / len(recent)
            return 0.5
        
        elif goal.id == "knowledge_gap_reduction":
            # Most recent gap count
            if self._gap_counts:
                return float(self._gap_counts[-1][1])
            return 0.0
        
        return 0.0

    async def get_goal_summary(self) -> dict:
        """
        Get summary of all goal progress.
        
        Returns:
            Dictionary with goal summaries
        """
        report = await self.evaluate_goals()
        
        summary = {
            "session_count": self._session_count,
            "interactions_this_session": self._interactions_this_session,
            "total_knowledge_added": self._knowledge_added,
            "goals": []
        }
        
        for progress in report.goals:
            goal = progress.goal
            summary["goals"].append({
                "id": goal.id,
                "description": goal.description,
                "current": round(progress.current_value, 3),
                "target": goal.target,
                "per": goal.per,
                "status": "on_track" if progress.on_track else "needs_attention"
            })
        
        return summary

    async def get_next_priority(self) -> Optional[str]:
        """
        Get the highest priority goal that needs attention.
        
        Returns:
            Description of the priority goal or None
        """
        report = await self.evaluate_goals()
        
        # Find goals not on track
        needs_attention = [
            p for p in report.goals
            if not p.on_track
        ]
        
        if not needs_attention:
            return None
        
        # Return the one furthest from target
        worst = min(
            needs_attention,
            key=lambda p: p.current_value / max(p.goal.target, 0.1)
        )
        
        return (
            f"Priority: {worst.goal.description}. "
            f"Current: {worst.current_value:.2f}, Target: {worst.goal.target}"
        )

    def start_session(self) -> None:
        """Mark the start of a new session."""
        self._session_count += 1
        self._interactions_this_session = 0

    def end_session(self) -> None:
        """Mark the end of a session."""
        self._interactions_this_session = 0

    async def get_long_term_trends(self) -> dict:
        """
        Get long-term trends across all goals.
        
        Returns:
            Dictionary with trend analysis
        """
        trends = {}
        
        # Quality trend
        if len(self._quality_scores) >= 20:
            first_10 = sum(self._quality_scores[:10]) / 10
            last_10 = sum(self._quality_scores[-10:]) / 10
            trends["quality_direction"] = "improving" if last_10 > first_10 else "stable"
            trends["quality_delta"] = round(last_10 - first_10, 3)
        else:
            trends["quality_direction"] = "insufficient_data"
        
        # Knowledge growth trend
        if len(self._gap_counts) >= 2:
            first = self._gap_counts[0][1]
            last = self._gap_counts[-1][1]
            trends["gaps_reduced"] = first - last
            trends["gap_direction"] = "improving" if last < first else "stable"
        else:
            trends["gap_direction"] = "insufficient_data"
        
        # Session growth
        if self._session_count > 1:
            trends["session_count"] = self._session_count
            avg_per_session = len(self._quality_scores) / max(1, self._session_count)
            trends["avg_interactions_per_session"] = round(avg_per_session, 1)
        
        return trends

    def get_motivational_message(self) -> str:
        """
        Get a motivational message based on current state.
        
        Returns:
            Motivational message for NICTO to reflect on
        """
        if not self._quality_scores:
            return "Every interaction is an opportunity to learn."
        
        recent_quality = sum(self._quality_scores[-10:]) / min(10, len(self._quality_scores))
        
        if recent_quality >= 0.9:
            return "Excellent performance. Keep pushing for excellence."
        elif recent_quality >= 0.8:
            return "Strong performance. Focus on consistency."
        elif recent_quality >= 0.7:
            return "Good performance. Look for areas to improve."
        elif recent_quality >= 0.5:
            return "Room for improvement. Every interaction teaches something."
        else:
            return "Learning phase. Focus on fundamentals and build from there."

    async def set_target(self, goal_id: str, target: float) -> bool:
        """
        Update target for a goal.
        
        Args:
            goal_id: ID of the goal to update
            target: New target value
            
        Returns:
            True if updated, False if goal not found
        """
        for goal in self.PERMANENT_GOALS:
            if goal.id == goal_id:
                goal.target = target
                return True
        return False

    async def get_all_goals(self) -> list[Goal]:
        """
        Get all permanent goals.
        
        Returns:
            List of all Goal objects
        """
        return self.PERMANENT_GOALS.copy()