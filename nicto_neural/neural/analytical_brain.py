"""Analytical Brain — 10 MoE+MLA networks for logic, analysis & precision."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
from .super_config import SuperConfig
from .advanced_layers import MultiHeadLatentAttention, EnhancedMoE


class AnalyticalBrainBase(nn.Module):
    def __init__(self, config: SuperConfig, name: str = ""):
        super().__init__()
        self.name = name; self.d_model = config.d_model
        self.mla = MultiHeadLatentAttention(config)
        self.moe = EnhancedMoE(config)
        self.norm_in = nn.LayerNorm(config.d_model); self.norm_mid = nn.LayerNorm(config.d_model); self.norm_out = nn.LayerNorm(config.d_model)
        self.confidence = nn.Sequential(nn.Linear(config.d_model, 64), nn.ReLU(), nn.Linear(64, 1), nn.Sigmoid())
        self.output_proj = nn.Linear(config.d_model, config.d_model)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x); h = self.mla(h); h = self.norm_mid(h)
        moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class LogicalDeductionNetwork(AnalyticalBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "logical_deduction")
        self.premise_encoder = nn.Linear(config.d_model, config.d_model)
        self.rule_engine = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.validity_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h); p = self.premise_encoder(h)
        v = torch.sigmoid(self.validity_gate(p)); h = h + v * self.rule_engine(p)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True)) * v.mean(dim=1, keepdim=True)
        return out, conf.squeeze(-1)


class CriticalAnalysisNetwork(AnalyticalBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "critical_analysis")
        self.claim_encoder = nn.Linear(config.d_model, config.d_model)
        self.evidence_scorer = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, 1))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        c = self.claim_encoder(h); ev = torch.sigmoid(self.evidence_scorer(c))
        h = h + ev * c; h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True)) * ev.mean(dim=1, keepdim=True)
        return out, conf.squeeze(-1)


class SystematicDecompositionNetwork(AnalyticalBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "decomposition")
        self.components = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h) + self.components(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class MathematicalReasoningNetwork(AnalyticalBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "math_reasoning")
        self.quant_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, 1))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        q = torch.sigmoid(self.quant_encoder(h)); h = h * q
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class DataDrivenInferenceNetwork(AnalyticalBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "data_inference")
        self.evidence_encoder = nn.Linear(config.d_model, config.d_model)
        self.inference_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        e = self.evidence_encoder(h); h = h + self.inference_ffn(e)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class HypothesisTestingNetwork(AnalyticalBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "hypothesis_testing")
        self.hypothesis_encoder = nn.Linear(config.d_model, config.d_model)
        self.falsifier = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, 1))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        hyp = self.hypothesis_encoder(h); f = torch.sigmoid(self.falsifier(hyp))
        h = h + f * hyp; h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class CausalReasoningNetwork(AnalyticalBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "causal_reasoning")
        self.cause_encoder = nn.Linear(config.d_model, config.d_model)
        self.effect_encoder = nn.Linear(config.d_model, config.d_model)
        self.causal_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        cause = self.cause_encoder(h); effect = self.effect_encoder(h)
        h = h + self.causal_ffn(cause * effect)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class ComparativeAnalysisNetwork(AnalyticalBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "comparative_analysis")
        self.compare_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model * 2), nn.GELU(), nn.Linear(config.d_model * 2, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h) + self.compare_ffn(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class RootCauseAnalysisNetwork(AnalyticalBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "root_cause")
        self.trace_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.iterations = 3
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        for _ in range(self.iterations): h = h + self.trace_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class FormalVerificationNetwork(AnalyticalBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "formal_verification")
        self.constraint_encoder = nn.Linear(config.d_model, config.d_model)
        self.verifier = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, 1))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        c = self.constraint_encoder(h); v = torch.sigmoid(self.verifier(c))
        h = h + v * c; h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True)) * v.mean(dim=1, keepdim=True)
        return out, conf.squeeze(-1)


ANALYTICAL_BRAIN_NETWORKS = {
    "logical_deduction": LogicalDeductionNetwork,
    "critical_analysis": CriticalAnalysisNetwork,
    "systematic_decomposition": SystematicDecompositionNetwork,
    "mathematical_reasoning": MathematicalReasoningNetwork,
    "data_driven_inference": DataDrivenInferenceNetwork,
    "hypothesis_testing": HypothesisTestingNetwork,
    "causal_reasoning": CausalReasoningNetwork,
    "comparative_analysis": ComparativeAnalysisNetwork,
    "root_cause_analysis": RootCauseAnalysisNetwork,
    "formal_verification": FormalVerificationNetwork,
}
