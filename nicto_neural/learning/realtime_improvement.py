from dataclasses import dataclass


@dataclass
class ImprovementResult:
    interaction_count: int
    quality_score: float
    calibration_delta: float
    improvements: list
    micro_updates_done: int


class RealtimeImprovementEngine:
    MIN_BUFFER_FOR_MICRO_UPDATE = 32
    MICRO_UPDATE_INTERVAL = 16

    def __init__(self, rl_agent=None, experience_buffer=None, knowledge_gap_tracker=None,
                 confidence_calibrator=None, dream_steerer=None, truth_engine=None):
        self.rl = rl_agent
        self.buffer = experience_buffer
        self.gaps = knowledge_gap_tracker
        self.calibrator = confidence_calibrator
        self.dream = dream_steerer
        self.truth = truth_engine
        self.interaction_count = 0
        self.improvement_log = []
        self.micro_updates_done = 0

    async def improve(self, question=None, response=None, confidence=None, domain=None,
                      truth_verified=None, claims_blocked=None):
        self.interaction_count += 1
        improvements = []

        if question is not None and response is not None:
            quality = self._self_evaluate(question, response, confidence, truth_verified)
            if quality < 0.7 and self.gaps:
                await self.gaps.record({
                    "domain": domain or "general",
                    "question_type": self._classify_question(question),
                    "quality_score": quality,
                    "confidence_at_time": confidence or 0.5,
                })
                improvements.append(f"Gap recorded: {domain or 'general'}")
            if self.calibrator and confidence is not None:
                calibration_delta = self.calibrator.adjust(
                    predicted_confidence=confidence, actual_quality=quality, domain=domain or "general"
                )
                if abs(calibration_delta) > 0.05:
                    improvements.append(f"Calibration adjusted by {calibration_delta:+.3f}")
            if (self.interaction_count % self.MICRO_UPDATE_INTERVAL == 0
                    and self.buffer and getattr(self.buffer, 'is_ready', lambda x: False)(self.MIN_BUFFER_FOR_MICRO_UPDATE)):
                batch = self.buffer.sample(self.MIN_BUFFER_FOR_MICRO_UPDATE)
                if self.rl:
                    metrics = self.rl.update(batch)
                    self.micro_updates_done += 1
                    improvements.append(
                        f"Micro PPO update #{self.micro_updates_done}: loss={metrics.get('policy_loss', 0):.4f}"
                    )
            if claims_blocked and claims_blocked > 3 or (quality is not None and quality < 0.4):
                improvements.append(f"Flagged for dream cycle (quality={quality:.2f})")
        else:
            quality = 0.5
            calibration_delta = 0.0

        result = ImprovementResult(
            interaction_count=self.interaction_count,
            quality_score=quality if 'quality' in dir() else 0.5,
            calibration_delta=calibration_delta if 'calibration_delta' in dir() else 0.0,
            improvements=improvements,
            micro_updates_done=self.micro_updates_done,
        )
        self.improvement_log.append({
            "count": self.interaction_count,
            "quality": quality if 'quality' in dir() else 0.5,
            "domain": domain or "general",
            "improvements": len(improvements),
        })
        return result

    def _self_evaluate(self, question, response, confidence, truth_verified):
        score = 0.5
        if confidence is not None:
            score += confidence * 0.2
        if truth_verified:
            score += 0.15
        q_len = len(question.split()) if question else 0
        r_len = len(response.split()) if response else 0
        if q_len > 20 and r_len > 50:
            score += 0.1
        elif q_len < 10 and r_len < 20:
            score += 0.05
        specificity = sum(1 for m in ["```", "def ", "import ", "http", "SELECT", "nmap "] if m in (response or ""))
        score += min(0.1, specificity * 0.02)
        return max(0.0, min(1.0, score))

    def _classify_question(self, question):
        q = question.lower() if question else ""
        if any(k in q for k in ["how do i", "how to", "what is the way"]):
            return "procedural"
        if any(k in q for k in ["what is", "explain", "define"]):
            return "conceptual"
        if any(k in q for k in ["why", "because", "reason"]):
            return "causal"
        if any(k in q for k in ["code", "script", "function", "class"]):
            return "generative"
        return "general"

    def get_improvement_trajectory(self):
        if len(self.improvement_log) < 2:
            return {"trend": "insufficient_data"}
        recent = self.improvement_log[-20:]
        avg_quality = sum(r["quality"] for r in recent) / len(recent)
        first_quality = self.improvement_log[0]["quality"] if self.improvement_log else 0
        return {
            "total_interactions": self.interaction_count,
            "micro_updates": self.micro_updates_done,
            "recent_avg_quality": avg_quality,
            "improvement_since_start": avg_quality - first_quality,
            "trend": "improving" if avg_quality > first_quality else "stable",
        }
