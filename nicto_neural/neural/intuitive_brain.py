"""Intuitive Brain — 10 MoE+MLA networks for rapid cognition & gut feeling."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
from .super_config import SuperConfig
from .advanced_layers import MultiHeadLatentAttention, EnhancedMoE


class IntuitiveBrainBase(nn.Module):
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
        moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class RapidPatternMatchNetwork(IntuitiveBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "rapid_pattern_match")
        self.prototype_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.match_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        m = torch.sigmoid(self.match_gate(h)); h = h + m * self.prototype_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class EmotionalAttunementNetwork(IntuitiveBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "emotional_attunement")
        self.affect_encoder = nn.Linear(config.d_model, config.d_model)
        self.empathy_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.affect_head = nn.Linear(config.d_model, 6)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        a = self.affect_encoder(h); h = h + self.empathy_ffn(a)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); aff = torch.sigmoid(self.affect_head(h.mean(dim=1, keepdim=True)))
        conf = self.confidence(h.mean(dim=1, keepdim=True)) * aff.mean(dim=-1, keepdim=True)
        return out, conf.squeeze(-1)


class HeuristicEngineNetwork(IntuitiveBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "heuristic_engine")
        self.heuristic_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.fast_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        f = torch.sigmoid(self.fast_gate(h)); h = h + f * self.heuristic_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class ImplicitLearningNetwork(IntuitiveBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "implicit_learning")
        self.subconscious_encoder = nn.Linear(config.d_model, config.d_model)
        self.accumulator = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        s = self.subconscious_encoder(h); h = h + self.accumulator(s)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class GestaltPerceptionNetwork(IntuitiveBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "gestalt")
        self.whole_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model * 2), nn.GELU(), nn.Linear(config.d_model * 2, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        h = h + self.whole_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class ValueJudgmentNetwork(IntuitiveBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "value_judgment")
        self.value_encoder = nn.Linear(config.d_model, config.d_model)
        self.judgment_head = nn.Sequential(nn.Linear(config.d_model, 1), nn.Sigmoid())
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        v = self.value_encoder(h); j = self.judgment_head(v)
        h = h + j * v; h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True)) * j.mean(dim=1, keepdim=True)
        return out, conf.squeeze(-1)


class SituationalAwarenessNetwork(IntuitiveBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "situational_awareness")
        self.context_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.awareness_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        a = torch.sigmoid(self.awareness_gate(h)); h = h + a * self.context_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class TrustCalibrationNetwork(IntuitiveBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "trust_calibration")
        self.reliability_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.trust_head = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        r = self.reliability_encoder(h); t = torch.sigmoid(self.trust_head(r))
        h = h + t * r; h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True)) * t.mean(dim=1, keepdim=True)
        return out, conf.squeeze(-1)


class SocialIntuitionNetwork(IntuitiveBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "social_intuition")
        self.social_encoder = nn.Linear(config.d_model, config.d_model)
        self.dynamics_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        s = self.social_encoder(h); h = h + self.dynamics_ffn(s)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class BlinkDecisionEngineNetwork(IntuitiveBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "blink_decision")
        self.thin_slice_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.blink_head = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        s = self.thin_slice_encoder(h); b = torch.sigmoid(self.blink_head(s))
        h = h + b * s; h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True)) * b.mean(dim=1, keepdim=True)
        return out, conf.squeeze(-1)


INTUITIVE_BRAIN_NETWORKS = {
    "rapid_pattern_match": RapidPatternMatchNetwork,
    "emotional_attunement": EmotionalAttunementNetwork,
    "heuristic_engine": HeuristicEngineNetwork,
    "implicit_learning": ImplicitLearningNetwork,
    "gestalt_perception": GestaltPerceptionNetwork,
    "value_judgment": ValueJudgmentNetwork,
    "situational_awareness": SituationalAwarenessNetwork,
    "trust_calibration": TrustCalibrationNetwork,
    "social_intuition": SocialIntuitionNetwork,
    "blink_decision": BlinkDecisionEngineNetwork,
}
