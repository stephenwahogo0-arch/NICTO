"""Primary Brain — 10 MoE+MLA networks for general intelligence & broad reasoning."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
from .super_config import SuperConfig
from .advanced_layers import MultiHeadLatentAttention, EnhancedMoE


class PrimaryBrainBase(nn.Module):
    def __init__(self, config: SuperConfig, name: str = ""):
        super().__init__()
        self.name = name
        self.d_model = config.d_model
        self.mla = MultiHeadLatentAttention(config)
        self.moe = EnhancedMoE(config)
        self.norm_in = nn.LayerNorm(config.d_model)
        self.norm_mid = nn.LayerNorm(config.d_model)
        self.norm_out = nn.LayerNorm(config.d_model)
        self.confidence = nn.Sequential(nn.Linear(config.d_model, 64), nn.ReLU(), nn.Linear(64, 1), nn.Sigmoid())
        self.output_proj = nn.Linear(config.d_model, config.d_model)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class GeneralReasoningNetwork(PrimaryBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "general_reasoning")
        self.reasoning_depth = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.depth_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        d = torch.sigmoid(self.depth_gate(h)); h = h + d * self.reasoning_depth(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class LanguageComprehensionNetwork(PrimaryBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "language")
        self.context_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model * 2), nn.GELU(), nn.Linear(config.d_model * 2, config.d_model))
        self.context_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        c = torch.sigmoid(self.context_gate(h)); h = h + c * self.context_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class ProblemSolvingNetwork(PrimaryBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "problem_solving")
        self.decomposer = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.solver = nn.Linear(config.d_model, config.d_model)
        self.iterations = 3
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        h = self.decomposer(h)
        for _ in range(self.iterations): h = h + self.solver(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class DecisionMakingNetwork(PrimaryBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "decision_making")
        self.option_encoder = nn.Linear(config.d_model, config.d_model)
        self.evaluator = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, 1))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        h = h + self.option_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        dec = torch.sigmoid(self.evaluator(h.mean(dim=1, keepdim=True)))
        conf = self.confidence(h.mean(dim=1, keepdim=True)) * dec
        return out, conf.squeeze(-1)


class PatternRecognitionNetwork(PrimaryBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "pattern_recognition")
        self.pattern_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model * 2), nn.GELU(), nn.Linear(config.d_model * 2, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        h = h + self.pattern_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class AbstractionBuilderNetwork(PrimaryBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "abstraction")
        self.level_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.abstract_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        g = torch.sigmoid(self.abstract_gate(h)); h = h + g * self.level_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class AnalogyEngineNetwork(PrimaryBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "analogy")
        self.source_encoder = nn.Linear(config.d_model, config.d_model)
        self.target_encoder = nn.Linear(config.d_model, config.d_model)
        self.mapping_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        src = self.source_encoder(h); tgt = self.target_encoder(h)
        h = h + self.mapping_ffn(src * tgt)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class CommonSenseNetwork(PrimaryBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "common_sense")
        self.physical_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.social_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.sense_gate = nn.Linear(config.d_model, 2)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        g = torch.sigmoid(self.sense_gate(h))
        h = h + g[:, :, :1] * self.physical_encoder(h) + g[:, :, 1:] * self.social_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class AttentionFilterNetwork(PrimaryBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "attention_filter")
        self.relevance_scorer = nn.Linear(config.d_model, 1)
        self.filter_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        rel = torch.sigmoid(self.relevance_scorer(h)); h = h + rel * self.filter_ffn(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class IntegrationHubNetwork(PrimaryBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "integration_hub")
        self.fusion_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model * 2), nn.GELU(), nn.Linear(config.d_model * 2, config.d_model))
        self.integration_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        g = torch.sigmoid(self.integration_gate(h)); h = h + g * self.fusion_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


PRIMARY_BRAIN_NETWORKS = {
    "general_reasoning": GeneralReasoningNetwork,
    "language_comprehension": LanguageComprehensionNetwork,
    "problem_solving": ProblemSolvingNetwork,
    "decision_making": DecisionMakingNetwork,
    "pattern_recognition": PatternRecognitionNetwork,
    "abstraction_builder": AbstractionBuilderNetwork,
    "analogy_engine": AnalogyEngineNetwork,
    "common_sense": CommonSenseNetwork,
    "attention_filter": AttentionFilterNetwork,
    "integration_hub": IntegrationHubNetwork,
}
