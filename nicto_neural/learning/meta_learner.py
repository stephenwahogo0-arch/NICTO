class MetaLearner:
    def __init__(self):
        self._strategy_performance = {}
        self._hyperparameter_log = []
        self._best_config = None

    def observe_and_adapt(self, task=None, result=None):
        if result is None:
            result = task or {}
        mode = result.get("mode", result.get("type", "unknown"))
        history = result.get("history", [])
        if not history:
            return {"adapted": False}
        losses = [h.get("policy_loss", h.get("loss", 1.0)) for h in history]
        if len(losses) >= 2:
            improvement_rate = (losses[0] - losses[-1]) / max(losses[0], 1e-8)
        else:
            improvement_rate = 0.0
        if mode not in self._strategy_performance:
            self._strategy_performance[mode] = []
        self._strategy_performance[mode].append(improvement_rate)
        recommendation = self._recommend_strategy()
        self._hyperparameter_log.append({
            "mode": mode, "improvement_rate": improvement_rate,
            "recommendation": recommendation, "epochs": len(history),
        })
        return {
            "adapted": True, "mode_used": mode,
            "improvement_rate": improvement_rate,
            "recommendation": recommendation,
            "best_mode_so_far": self._best_mode(),
        }

    def _recommend_strategy(self):
        if not self._strategy_performance:
            return "hybrid"
        best_mode = self._best_mode()
        if best_mode:
            return f"continue_with_{best_mode}"
        return "hybrid"

    def _best_mode(self):
        if not self._strategy_performance:
            return "hybrid"
        mode_avgs = {}
        for mode, improvements in self._strategy_performance.items():
            if improvements:
                mode_avgs[mode] = sum(improvements) / len(improvements)
        if not mode_avgs:
            return "hybrid"
        return max(mode_avgs, key=mode_avgs.get)

    def get_meta_stats(self):
        return {
            "strategies_tried": list(self._strategy_performance.keys()),
            "best_strategy": self._best_mode(),
            "adaptation_cycles": len(self._hyperparameter_log),
            "strategy_performance": {
                mode: round(sum(v) / len(v), 4) if v else 0.0
                for mode, v in self._strategy_performance.items()
            },
        }
