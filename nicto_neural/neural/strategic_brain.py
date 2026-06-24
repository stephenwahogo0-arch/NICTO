"""Strategic Brain — 10 MoE+MLA networks for planning, goals & tactics."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
from .super_config import SuperConfig
from .advanced_layers import MultiHeadLatentAttention, EnhancedMoE


class StrategicBrainBase(nn.Module):
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


class GoalDecompositionNetwork(StrategicBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "goal_decomposition")
        self.goal_encoder = nn.Linear(config.d_model, config.d_model)
        self.subgoal_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        g = self.goal_encoder(h); h = h + self.subgoal_ffn(g)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class LongTermPlanningNetwork(StrategicBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "long_term_planning")
        self.horizon_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.sequence_encoder = nn.Linear(config.d_model, config.d_model)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        h = h + self.horizon_encoder(h) + self.sequence_encoder(h)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class ResourceOptimizationNetwork(StrategicBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "resource_optimization")
        self.cost_encoder = nn.Linear(config.d_model, 1)
        self.allocator = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        c = torch.sigmoid(self.cost_encoder(h)); h = h + c * self.allocator(h)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class RiskAssessmentNetwork(StrategicBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "risk_assessment")
        self.risk_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.probability_head = nn.Linear(config.d_model, 1)
        self.impact_head = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        r = self.risk_encoder(h)
        p = torch.sigmoid(self.probability_head(r)); i = torch.sigmoid(self.impact_head(r))
        h = h + r * p * i; h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class GameTheoryNetwork(StrategicBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "game_theory")
        self.payoff_encoder = nn.Linear(config.d_model, config.d_model)
        self.strategy_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        p = self.payoff_encoder(h); h = h + self.strategy_ffn(p)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class ContingencyPlanningNetwork(StrategicBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "contingency")
        self.branch_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.backup_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        b = torch.sigmoid(self.backup_gate(h)); h = h + b * self.branch_encoder(h)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class OpportunityDetectionNetwork(StrategicBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "opportunity")
        self.signal_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.opportunity_head = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        s = self.signal_encoder(h); o = torch.sigmoid(self.opportunity_head(s))
        h = h + o * s; h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class CompetitiveAnalysisNetwork(StrategicBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "competitive_analysis")
        self.adversary_encoder = nn.Linear(config.d_model, config.d_model)
        self.advantage_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        adv = self.adversary_encoder(h); h = h + self.advantage_ffn(adv)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class TimelineForecastingNetwork(StrategicBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "timeline")
        self.temporal_encoder = nn.Linear(config.d_model, config.d_model)
        self.schedule_head = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, 1))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h) + self.temporal_encoder(h)
        h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); t = torch.sigmoid(self.schedule_head(h.mean(dim=1, keepdim=True)))
        conf = self.confidence(h.mean(dim=1, keepdim=True)) * t
        return out, conf.squeeze(-1)


class ExecutionTrackingNetwork(StrategicBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "execution")
        self.tracker = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.progress_head = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        h = h + self.tracker(h); h = self.norm_mid(h); moe_out, _ = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); p = torch.sigmoid(self.progress_head(h.mean(dim=1, keepdim=True)))
        conf = self.confidence(h.mean(dim=1, keepdim=True)) * p
        return out, conf.squeeze(-1)


STRATEGIC_BRAIN_NETWORKS = {
    "goal_decomposition": GoalDecompositionNetwork,
    "long_term_planning": LongTermPlanningNetwork,
    "resource_optimization": ResourceOptimizationNetwork,
    "risk_assessment": RiskAssessmentNetwork,
    "game_theory": GameTheoryNetwork,
    "contingency_planning": ContingencyPlanningNetwork,
    "opportunity_detection": OpportunityDetectionNetwork,
    "competitive_analysis": CompetitiveAnalysisNetwork,
    "timeline_forecasting": TimelineForecastingNetwork,
    "execution_tracking": ExecutionTrackingNetwork,
}
