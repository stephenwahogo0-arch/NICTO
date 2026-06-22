from typing import Optional


class CalibrationEngine:
    DOMAINS = [
        "cybersecurity", "programming", "mathematics",
        "language", "strategy", "knowledge",
        "general", "creative", "reasoning"
    ]

    def __init__(self):
        self._multipliers = {d: 1.0 for d in self.DOMAINS}
        self._history = {d: [] for d in self.DOMAINS}

    def calibrate(self, raw_confidence: float, domain: str = "general", result: Optional[dict] = None) -> float:
        multiplier = self._multipliers.get(domain, 1.0)
        calibrated = raw_confidence * multiplier
        return max(0.05, min(0.99, calibrated))

    def adjust(self, predicted_confidence, actual_quality, domain):
        if domain not in self._history:
            self._history[domain] = []
        self._history[domain].append((predicted_confidence, actual_quality))
        self._history[domain] = self._history[domain][-50:]
        history = self._history[domain]
        if len(history) < 5:
            return 0.0
        predictions = [h[0] for h in history]
        actuals = [h[1] for h in history]
        avg_pred = sum(predictions) / len(predictions)
        avg_actual = sum(actuals) / len(actuals)
        error = avg_actual - avg_pred
        delta = error * 0.1
        old_multiplier = self._multipliers.get(domain, 1.0)
        new_multiplier = max(0.3, min(1.5, old_multiplier + delta))
        self._multipliers[domain] = new_multiplier
        return delta

    def get_calibration_report(self):
        report = {}
        for domain, history in self._history.items():
            if len(history) < 3:
                continue
            predictions = [h[0] for h in history]
            actuals = [h[1] for h in history]
            error = sum(abs(p - a) for p, a in zip(predictions, actuals)) / len(history)
            report[domain] = {
                "calibration_error": round(error, 4),
                "multiplier": round(self._multipliers[domain], 4),
                "n_observations": len(history),
                "grade": "excellent" if error < 0.05 else "good" if error < 0.10 else "needs_work",
            }
        return report
