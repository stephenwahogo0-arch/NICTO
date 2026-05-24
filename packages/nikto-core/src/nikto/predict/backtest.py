import numpy as np
import pandas as pd
from collections import defaultdict


class BacktestEngine:
    def __init__(self):
        self.results = {}

    def run(self, model, features_list, actuals, model_name="default"):
        if len(features_list) != len(actuals):
            raise ValueError(f"features ({len(features_list)}) and actuals ({len(actuals)}) must match")
        if len(features_list) == 0:
            return {"model": model_name, "error": "no data"}

        predictions = []
        for i, (fv, actual) in enumerate(zip(features_list, actuals)):
            try:
                if hasattr(model, "predict_matchup"):
                    result = model.predict_matchup(fv)
                    prob = result["probability"]
                else:
                    X = np.array(fv).reshape(1, -1) if hasattr(fv, "shape") else np.array(fv).reshape(1, -1)
                    prob = model.predict(X)[0]
            except Exception:
                prob = 0.5
            predictions.append({"prob": prob, "actual": actual, "correct": (prob > 0.5) == (actual == 1)})

        return self._compute_metrics(predictions, model_name)

    def run_sequential(self, model_factory, feature_vectors, actuals, window=100):
        batched_results = []
        for i in range(window, len(feature_vectors)):
            train_X = np.array(feature_vectors[i - window:i])
            train_y = np.array(actuals[i - window:i])
            test_X = np.array(feature_vectors[i]).reshape(1, -1)
            test_y = actuals[i]
            model = model_factory()
            model.fit(train_X, train_y)
            prob = model.predict(test_X)[0]
            batched_results.append({"prob": prob, "actual": test_y, "correct": (prob > 0.5) == (test_y == 1)})
        return self._compute_metrics(batched_results, "sequential")

    def _compute_metrics(self, predictions, model_name):
        if not predictions:
            return {"model": model_name, "error": "no predictions"}

        correct = sum(1 for p in predictions if p["correct"])
        total = len(predictions)
        accuracy = correct / total if total > 0 else 0.0

        probs = np.array([p["prob"] for p in predictions])
        actuals = np.array([p["actual"] for p in predictions])

        from sklearn.metrics import brier_score_loss, roc_auc_score, log_loss
        try:
            brier = brier_score_loss(actuals, probs)
        except Exception:
            brier = 0.25
        try:
            auc = roc_auc_score(actuals, probs)
        except Exception:
            auc = 0.5
        try:
            ll = log_loss(actuals, probs)
        except Exception:
            ll = 0.693

        up_probs = probs[actuals == 1]
        down_probs = probs[actuals == 0]
        avg_prob_correct = float(np.mean(up_probs)) if len(up_probs) > 0 else 0.0
        avg_prob_wrong = float(np.mean(down_probs)) if len(down_probs) > 0 else 1.0

        bankroll = 1000.0
        final_bankroll = 1000.0
        max_bankroll = 1000.0
        for p in predictions:
            if abs(p["prob"] - 0.5) > 0.05:
                stake = 50.0
                if (p["prob"] > 0.5) == (p["actual"] == 1):
                    odds = 1.0 / max(p["prob"], 0.01)
                    final_bankroll += stake * (odds - 1)
                else:
                    final_bankroll -= stake
                max_bankroll = max(max_bankroll, final_bankroll)

        total_return = (final_bankroll - bankroll) / bankroll
        max_drawdown = (max_bankroll - final_bankroll) / max_bankroll if max_bankroll > 0 else 0.0

        result = {
            "model": model_name,
            "total_predictions": total,
            "correct": correct,
            "accuracy": round(accuracy, 4),
            "brier_score": round(brier, 4),
            "roc_auc": round(auc, 4),
            "log_loss": round(ll, 4),
            "avg_prob_correct": round(avg_prob_correct, 4),
            "avg_prob_wrong": round(avg_prob_wrong, 4),
            "total_return": round(total_return, 4),
            "max_drawdown": round(max_drawdown, 4),
            "profit_factor": round((final_bankroll - bankroll) / max((bankroll - min(1000, final_bankroll)), 0.001), 4),
        }
        self.results[model_name] = result
        return result

    def compare_models(self):
        if not self.results:
            return []
        sorted_results = sorted(self.results.values(), key=lambda r: r.get("accuracy", 0), reverse=True)
        return sorted_results

    def summary(self):
        lines = ["Backtest Summary"]
        lines.append("=" * 60)
        for name, result in sorted(self.results.items(), key=lambda x: x[1].get("accuracy", 0), reverse=True):
            lines.append(f"  {name:20s}  Acc:{result.get('accuracy',0):.2%}  AUC:{result.get('roc_auc',0):.3f}  Brier:{result.get('brier_score',0):.4f}  Ret:{result.get('total_return',0):.2%}")
        return "\n".join(lines)
