"""Primary brain — task routing, conversation management, state control."""

import torch
import torch.nn as nn


class PrimaryBrain(nn.Module):
    """The conductor of the brain orchestra."""

    def __init__(self, config, elo_system):
        super().__init__()
        self.name = "primary"
        self.config = config
        self.elo = elo_system
        self.router_head = nn.Linear(config.d_model, len(config.brain_names))
        self.state_tracker = nn.GRU(config.d_model, config.d_model, batch_first=True)
        self._hidden = None
        self.specializations = ["routing", "conversation", "state"]

    def route(self, features: torch.Tensor) -> dict:
        """Decide which specialist brains to activate."""
        routing_logits = self.router_head(features)
        routing_probs = torch.softmax(routing_logits, dim=-1)
        return {
            brain: float(routing_probs[..., i].mean())
            for i, brain in enumerate(self.config.brain_names)
        }

    def forward(self, x: torch.Tensor, context=None) -> dict:
        inp = x.unsqueeze(1) if x.dim() == 2 else x
        out, self._hidden = self.state_tracker(inp, self._hidden)
        return {"output": out, "routing": self.route(out.mean(1)), "brain": self.name}

    def reset_state(self) -> None:
        self._hidden = None
