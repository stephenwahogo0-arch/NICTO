import torch
import torch.nn as nn
from typing import Dict, Optional
from neural.config import NeuralConfig
from neural.attention import CrossAttention


class MultimodalFusion(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.config = config
        self.text_to_image = CrossAttention(config)
        self.image_to_text = CrossAttention(config)
        self.text_to_audio = CrossAttention(config)
        self.audio_to_text = CrossAttention(config)

        self.fusion_gate = nn.Sequential(
            nn.Linear(config.d_model * 4, config.d_model * 2),
            nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
            nn.Sigmoid(),
        )
        self.output_proj = nn.Linear(config.d_model, config.d_model, bias=False)

    def forward(self, modalities: Dict[str, torch.Tensor]) -> torch.Tensor:
        text = modalities.get("text", None)
        image = modalities.get("image", None)
        audio = modalities.get("audio", None)

        fused = text
        if text is not None and image is not None:
            t2i = self.text_to_image(text, image)
            i2t = self.image_to_text(image, text)
            img_context = torch.cat([t2i, i2t], dim=-1)
        else:
            img_context = None

        if text is not None and audio is not None:
            t2a = self.text_to_audio(text, audio)
            a2t = self.audio_to_text(audio, text)
            aud_context = torch.cat([t2a, a2t], dim=-1)
        else:
            aud_context = None

        modalities_present = 1
        if text is None and image is not None:
            fused = image
        elif text is None and audio is not None:
            fused = audio
        elif text is None and image is not None and audio is not None:
            fused = (image + audio) / 2

        if text is not None:
            gate_inputs = [text]
            if img_context is not None:
                gate_inputs.append(img_context.mean(dim=1, keepdim=True).expand(-1, text.size(1), -1))
            if aud_context is not None:
                gate_inputs.append(aud_context.mean(dim=1, keepdim=True).expand(-1, text.size(1), -1))
            while len(gate_inputs) < 4:
                gate_inputs.append(torch.zeros_like(gate_inputs[0]))
            gate = self.fusion_gate(torch.cat(gate_inputs, dim=-1))
            if img_context is not None:
                fused = fused + gate * t2i
            if aud_context is not None:
                fused = fused + gate * t2a

        return self.output_proj(fused)
