"""BrainBoost — gradient-boosted ensemble over brains (dual mode)."""

import torch
import torch.nn.functional as F


class BrainBoost:
    """Gradient-boosted ensemble. Fixed mode + trained mode."""

    def __init__(self, config, brains: dict):
        self.config = config
        self.brains = brains
        self.n_stages = config.boost_stages
        self.lr = config.boost_learning_rate
        self.min_weight = config.boost_min_child_weight

        self._trained_weights = None
        self._fixed_weights = {
            name: 1.0 / len(brains) for name in brains
        }
        self._mode = "fixed"

    def predict(self, x: torch.Tensor, mode: str = "fixed") -> dict:
        self._mode = mode
        weights = (
            self._trained_weights
            if mode == "trained" and self._trained_weights
            else self._fixed_weights
        )

        primary_out = self.brains["primary"](x)
        ensemble_output = primary_out.get("output", x) * weights.get("primary", 0.2)

        stage_outputs = {"primary": primary_out}
        brain_list = list(self.brains.items())
        for brain_name, brain in brain_list[1 : self.n_stages + 1]:
            brain_result = brain(x)
            confidence = float(
                brain_result.get("confidence", torch.tensor(0.5)).mean()
            )
            if confidence >= self.min_weight:
                weight = weights.get(brain_name, 0.2) * self.lr
                brain_out = brain_result.get("output", x)
                if brain_out.shape == ensemble_output.shape:
                    ensemble_output = ensemble_output + weight * brain_out
                stage_outputs[brain_name] = brain_result

        all_confs = [
            float(v.get("confidence", torch.tensor(0.5)).mean())
            for v in stage_outputs.values()
        ]
        ensemble_confidence = sum(all_confs) / max(len(all_confs), 1)

        return {
            "output": ensemble_output,
            "confidence": ensemble_confidence,
            "stages": len(stage_outputs),
            "mode": mode,
        }

    def train_weights(self, validation_data: list, epochs: int = 50) -> dict:
        """Learn optimal stage weights via gradient descent."""
        weight_params = {
            name: torch.tensor([self._fixed_weights[name]], requires_grad=True)
            for name in self.brains
        }
        optimizer = torch.optim.Adam(list(weight_params.values()), lr=0.01)
        history = []

        for epoch in range(epochs):
            total_loss = 0.0
            for features, target in validation_data[:20]:
                optimizer.zero_grad()
                all_weights = torch.stack(list(weight_params.values()))
                softmax_weights = torch.softmax(all_weights, dim=0)
                for i, name in enumerate(weight_params.keys()):
                    self._fixed_weights[name] = float(softmax_weights[i])

                pred = self.predict(features, mode="fixed")
                if pred["output"] is not None and target is not None:
                    if pred["output"].shape == target.shape:
                        loss = F.mse_loss(pred["output"], target)
                        loss.backward()
                        optimizer.step()
                        total_loss += loss.item()

            avg_loss = total_loss / max(len(validation_data), 1)
            history.append({"epoch": epoch, "loss": avg_loss})

        all_weights = torch.stack(list(weight_params.values()))
        softmax_weights = torch.softmax(all_weights, dim=0)
        self._trained_weights = {
            name: float(softmax_weights[i])
            for i, name in enumerate(weight_params.keys())
        }
        return {"history": history, "trained_weights": self._trained_weights}
