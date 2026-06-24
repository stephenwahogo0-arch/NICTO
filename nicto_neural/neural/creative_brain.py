"""Creative Brain — 10 MoE+MLA networks for novelty, divergent thinking & imagination."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
from .super_config import SuperConfig
from .advanced_layers import MultiHeadLatentAttention, EnhancedMoE


class CreativeBrainBase(nn.Module):
    def __init__(self, config: SuperConfig, name: str = ""):
        super().__init__()
        self.name = name; self.d_model = config.d_model
        self.mla = MultiHeadLatentAttention(config)
        self.moe = EnhancedMoE(config)
        self.norm_in = nn.LayerNorm(config.d_model); self.norm_mid = nn.LayerNorm(config.d_model); self.norm_out = nn.LayerNorm(config.d_model)
        self.confidence = nn.Sequential(nn.Linear(config.d_model, 64), nn.ReLU(), nn.Linear(64, 1), nn.Sigmoid())
        self.output_proj = nn.Linear(config.d_model, config.d_model)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h); h = self.norm_mid(h)
        moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class IdeaGenerationNetwork(CreativeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "idea_generation")
        self.divergent_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model * 2), nn.GELU(), nn.Linear(config.d_model * 2, config.d_model))
        self.novelty_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        n = torch.sigmoid(self.novelty_gate(h)); h = h + n * self.divergent_encoder(h)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class MetaphoricThinkingNetwork(CreativeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "metaphor")
        self.source_proj = nn.Linear(config.d_model, config.d_model)
        self.target_proj = nn.Linear(config.d_model, config.d_model)
        self.blend_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        src = self.source_proj(h); tgt = self.target_proj(h)
        h = h + self.blend_ffn(src + tgt)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class CounterfactualReasoningNetwork(CreativeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "counterfactual")
        self.whatif_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h) + self.whatif_encoder(h)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class VisualizationEngineNetwork(CreativeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "visualization")
        self.spatial_encoder = nn.Linear(config.d_model, config.d_model)
        self.viz_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h) + self.viz_ffn(self.spatial_encoder(h))
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class NarrativeConstructionNetwork(CreativeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "narrative")
        self.story_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model * 2), nn.GELU(), nn.Linear(config.d_model * 2, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h) + self.story_encoder(h)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class DesignSynthesisNetwork(CreativeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "design_synthesis")
        self.form_encoder = nn.Linear(config.d_model, config.d_model)
        self.function_encoder = nn.Linear(config.d_model, config.d_model)
        self.design_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        form = self.form_encoder(h); func = self.function_encoder(h)
        h = h + self.design_ffn(form + func)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class ImprovisationEngineNetwork(CreativeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "improvisation")
        self.recombiner = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.spontaneity_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        s = torch.sigmoid(self.spontaneity_gate(h)); h = h + s * self.recombiner(h)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class AestheticAppraisalNetwork(CreativeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "aesthetic")
        self.style_encoder = nn.Linear(config.d_model, config.d_model)
        self.appraisal_head = nn.Sequential(nn.Linear(config.d_model, 1), nn.Sigmoid())
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h) + self.style_encoder(h)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); a = self.appraisal_head(h.mean(dim=1, keepdim=True))
        conf = self.confidence(h.mean(dim=1, keepdim=True)) * a
        return out, conf.squeeze(-1)


class HumorDetectionNetwork(CreativeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "humor")
        self.incongruity_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, 1))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        inc = torch.sigmoid(self.incongruity_encoder(h)); h = h * inc
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class InnovationScoutingNetwork(CreativeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "innovation_scouting")
        self.gap_encoder = nn.Linear(config.d_model, config.d_model)
        self.innovation_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        g = self.gap_encoder(h); h = h + self.innovation_ffn(g)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


CREATIVE_BRAIN_NETWORKS = {
    "idea_generation": IdeaGenerationNetwork,
    "metaphoric_thinking": MetaphoricThinkingNetwork,
    "counterfactual_reasoning": CounterfactualReasoningNetwork,
    "visualization_engine": VisualizationEngineNetwork,
    "narrative_construction": NarrativeConstructionNetwork,
    "design_synthesis": DesignSynthesisNetwork,
    "improvisation_engine": ImprovisationEngineNetwork,
    "aesthetic_appraisal": AestheticAppraisalNetwork,
    "humor_detection": HumorDetectionNetwork,
    "innovation_scouting": InnovationScoutingNetwork,
}
