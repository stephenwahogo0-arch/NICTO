import torch
import torch.nn as nn
from typing import Optional
from neural.config import NeuralConfig
from neural.transformer import TransformerCore


class TextEncoder(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.config = config
        self.transformer = TransformerCore(config)
        self.projection = nn.Linear(config.d_model, config.d_model, bias=False)

    def forward(
        self, input_ids: torch.LongTensor, mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        hidden = self.transformer(input_ids, mask=mask)
        if mask is not None:
            mask_expanded = mask.unsqueeze(-1).float()
            pooled = (hidden * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1).clamp(min=1)
        else:
            pooled = hidden.mean(dim=1)
        return self.projection(pooled)

    def encode(self, text: str, tokenizer) -> torch.Tensor:
        tokens = tokenizer.encode(text)
        tokens = tokens.unsqueeze(0).to(next(self.parameters()).device)
        with torch.no_grad():
            return self.forward(tokens)
