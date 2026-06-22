import torch
import torch.nn as nn
from typing import Optional, Tuple, List, Dict
from .config import NeuralConfig
from .attention import MultiHeadAttention, CausalSelfAttention
from .positional import create_positional_encoding


class FeedForward(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.gate = nn.Linear(config.d_model, config.d_ff, bias=False)
        self.up = nn.Linear(config.d_model, config.d_ff, bias=False)
        self.down = nn.Linear(config.d_ff, config.d_model, bias=False)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dropout(self.down(torch.sigmoid(self.gate(x)) * self.up(x)))


class TransformerBlock(nn.Module):
    def __init__(self, config: NeuralConfig, layer_idx: int = 0):
        super().__init__()
        self.ln1 = nn.LayerNorm(config.d_model, eps=config.eps)
        self.attn = CausalSelfAttention(config)
        self.ln2 = nn.LayerNorm(config.d_model, eps=config.eps)
        self.ffn = FeedForward(config)
        self.dropout = nn.Dropout(config.dropout)
        self.layer_idx = layer_idx

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
    ) -> torch.Tensor:
        x = x + self.dropout(self.attn(self.ln1(x), mask=mask, kv_cache=kv_cache))
        x = x + self.dropout(self.ffn(self.ln2(x)))
        return x


class TransformerCore(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.position_encoding = create_positional_encoding(config, "sinusoidal")
        self.dropout = nn.Dropout(config.dropout)

        self.layers = nn.ModuleList(
            [TransformerBlock(config, i) for i in range(config.n_layers)]
        )
        self.ln_final = nn.LayerNorm(config.d_model, eps=config.eps)

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if module.bias is not None:
                    torch.nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            elif isinstance(module, nn.LayerNorm):
                torch.nn.init.ones_(module.weight)
                if module.bias is not None:
                    torch.nn.init.zeros_(module.bias)

    def forward(
        self,
        input_ids: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        kv_caches: Optional[List[Optional[Tuple[torch.Tensor, torch.Tensor]]]] = None,
    ) -> torch.Tensor:
        x = self.token_embedding(input_ids)
        x = self.position_encoding(x)
        x = self.dropout(x)

        for i, layer in enumerate(self.layers):
            kv_cache = kv_caches[i] if kv_caches is not None else None
            x = layer(x, mask=mask, kv_cache=kv_cache)

        x = self.ln_final(x)
        return x

    def get_num_params(self) -> int:
        return sum(p.numel() for p in self.parameters())


class TransformerWithLMHead(TransformerCore):
    def __init__(self, config: NeuralConfig):
        super().__init__(config)
        self.lm_head = nn.Linear(config.d_model, config.vocab_size, bias=False)
        self.lm_head.weight = self.token_embedding.weight

    def forward(
        self,
        input_ids: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        kv_caches: Optional[List[Optional[Tuple[torch.Tensor, torch.Tensor]]]] = None,
    ) -> torch.Tensor:
        hidden = super().forward(input_ids, mask=mask, kv_caches=kv_caches)
        logits = self.lm_head(hidden)
        return logits
