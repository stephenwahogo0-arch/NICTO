"""Fine-tuning engine — LoRA-style fine-tuning for Q, K, V, O projections."""

import torch
import torch.nn as nn


class LoRALayer(nn.Module):
    """Low-Rank Adaptation layer for efficient fine-tuning."""

    def __init__(self, in_features: int, out_features: int, rank: int = 8):
        super().__init__()
        self.rank = rank
        self.lora_a = nn.Linear(in_features, rank, bias=False)
        self.lora_b = nn.Linear(rank, out_features, bias=False)
        self.scaling = 1.0 / rank
        nn.init.normal_(self.lora_a.weight, std=0.02)
        nn.init.zeros_(self.lora_b.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.lora_b(self.lora_a(x)) * self.scaling


class FineTuner:
    """Applies LoRA fine-tuning to Q, K, V, O projections."""

    def __init__(self, config, rank: int = 8):
        self.config = config
        self.rank = rank
        self._lora_layers: dict[str, LoRALayer] = {}
        self._frozen_params: list[nn.Parameter] = []

    def prepare_model(self, model: nn.Module) -> nn.Module:
        """Freeze base model and add LoRA adapters to attention projections."""
        for param in model.parameters():
            param.requires_grad = False
            self._frozen_params.append(param)

        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                if any(proj in name for proj in ["W_q", "W_k", "W_v", "W_o"]):
                    lora = LoRALayer(
                        module.in_features, module.out_features, self.rank
                    )
                    self._lora_layers[name] = lora

        return model

    def get_trainable_params(self) -> list[nn.Parameter]:
        """Return only LoRA parameters for optimizer."""
        params = []
        for lora in self._lora_layers.values():
            params.extend(lora.parameters())
        return params

    def trainable_param_count(self) -> int:
        return sum(p.numel() for p in self.get_trainable_params())

    def total_param_count(self) -> int:
        return sum(p.numel() for p in self._frozen_params) + self.trainable_param_count()

    def get_stats(self) -> dict:
        trainable = self.trainable_param_count()
        total = self.total_param_count()
        return {
            "lora_layers": len(self._lora_layers),
            "rank": self.rank,
            "trainable_params": trainable,
            "total_params": total,
            "trainable_ratio": trainable / max(total, 1),
        }
