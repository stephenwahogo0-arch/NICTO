"""Multimodal fusion — cross-modal attention fusion."""

import torch
import torch.nn as nn

from ..neural.attention import MultiHeadAttention


class MultimodalFusion(nn.Module):
    """Cross-modal attention fusion for combining text, image, and audio features."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.text_proj = nn.Linear(config.d_model, config.d_model)
        self.image_proj = nn.Linear(config.d_model, config.d_model)
        self.audio_proj = nn.Linear(config.d_model, config.d_model)
        self.cross_attention = MultiHeadAttention(config)
        self.norm = nn.LayerNorm(config.d_model)
        self.gate = nn.Linear(config.d_model * 3, config.d_model)

    def forward(
        self,
        text_features: torch.Tensor,
        image_features: torch.Tensor = None,
        audio_features: torch.Tensor = None,
    ) -> torch.Tensor:
        text_proj = self.text_proj(text_features)

        if image_features is not None and audio_features is not None:
            img_proj = self.image_proj(image_features).unsqueeze(1)
            aud_proj = self.audio_proj(audio_features).unsqueeze(1)
            combined = torch.cat([text_proj, img_proj, aud_proj], dim=1)
        elif image_features is not None:
            img_proj = self.image_proj(image_features).unsqueeze(1)
            combined = torch.cat([text_proj, img_proj], dim=1)
        elif audio_features is not None:
            aud_proj = self.audio_proj(audio_features).unsqueeze(1)
            combined = torch.cat([text_proj, aud_proj], dim=1)
        else:
            return text_proj

        fused = self.cross_attention(text_proj, combined, combined)
        return self.norm(fused + text_proj)
