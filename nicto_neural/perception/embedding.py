import torch
import torch.nn as nn
from neural.config import NeuralConfig


class TokenEmbedding(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.d_model = config.d_model
        self._init_weights()

    def _init_weights(self):
        nn.init.normal_(self.embedding.weight, mean=0.0, std=0.02)

    def forward(self, input_ids: torch.LongTensor) -> torch.Tensor:
        return self.embedding(input_ids) * (self.d_model ** 0.5)
