"""Knowledge Brain — 10 MoE+MLA networks for facts, memory & learning."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
from .super_config import SuperConfig
from .advanced_layers import MultiHeadLatentAttention, EnhancedMoE


class KnowledgeBrainBase(nn.Module):
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


class FactualRetrievalNetwork(KnowledgeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "factual_retrieval")
        self.retrieval_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model * 2), nn.GELU(), nn.Linear(config.d_model * 2, config.d_model))
        self.relevance_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        r = torch.sigmoid(self.relevance_gate(h)); h = h + r * self.retrieval_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class ConceptMappingNetwork(KnowledgeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "concept_mapping")
        self.relation_encoder = nn.Linear(config.d_model, config.d_model)
        self.graph_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        rel = self.relation_encoder(h); h = h + self.graph_ffn(rel)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class ExplanationGenerationNetwork(KnowledgeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "explanation")
        self.causal_encoder = nn.Linear(config.d_model, config.d_model)
        self.step_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        c = self.causal_encoder(h); h = h + self.step_ffn(c)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class LearningSynthesisNetwork(KnowledgeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "learning_synthesis")
        self.integrate_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.synthesis_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        g = torch.sigmoid(self.synthesis_gate(h)); h = h + g * self.integrate_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class CrossDomainTransferNetwork(KnowledgeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "cross_domain")
        self.domain_a = nn.Linear(config.d_model, config.d_model)
        self.domain_b = nn.Linear(config.d_model, config.d_model)
        self.transfer_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        a = self.domain_a(h); b = self.domain_b(h)
        h = h + self.transfer_ffn(a + b)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class KnowledgeVerificationNetwork(KnowledgeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "verification")
        self.truth_encoder = nn.Linear(config.d_model, config.d_model)
        self.verification_head = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, 1))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        t = self.truth_encoder(h); v = torch.sigmoid(self.verification_head(t))
        h = h + v * t; h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True)) * v.mean(dim=1, keepdim=True)
        return out, conf.squeeze(-1)


class GapDetectionNetwork(KnowledgeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "gap_detection")
        self.unknown_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, 1))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        uk = torch.sigmoid(self.unknown_encoder(h)); h = h * (1 - uk)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class StructuredRecallNetwork(KnowledgeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "structured_recall")
        self.index_encoder = nn.Linear(config.d_model, config.d_model)
        self.recall_ffn = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        idx = self.index_encoder(h); h = h + self.recall_ffn(idx)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class MnemonicEncodingNetwork(KnowledgeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "mnemonic")
        self.assoc_encoder = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Linear(config.d_model, config.d_model))
        self.encoding_gate = nn.Linear(config.d_model, 1)
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        g = torch.sigmoid(self.encoding_gate(h)); h = h + g * self.assoc_encoder(h)
        h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class EpistemicCalibrationNetwork(KnowledgeBrainBase):
    def __init__(self, config: SuperConfig):
        super().__init__(config, "epistemic_calibration")
        self.certainty_encoder = nn.Linear(config.d_model, config.d_model)
        self.calibration_head = nn.Sequential(nn.Linear(config.d_model, 1), nn.Sigmoid())
    def forward(self, x):
        h = self.norm_in(x); h = self.mla(h)
        c = self.certainty_encoder(h); cal = self.calibration_head(c)
        h = h + cal * c; h = self.norm_mid(h); moe_out = self.moe(h); h = self.norm_out(h + moe_out)
        out = self.output_proj(h); conf = self.confidence(h.mean(dim=1, keepdim=True)) * cal.mean(dim=1, keepdim=True)
        return out, conf.squeeze(-1)


KNOWLEDGE_BRAIN_NETWORKS = {
    "factual_retrieval": FactualRetrievalNetwork,
    "concept_mapping": ConceptMappingNetwork,
    "explanation_generation": ExplanationGenerationNetwork,
    "learning_synthesis": LearningSynthesisNetwork,
    "cross_domain_transfer": CrossDomainTransferNetwork,
    "verification": KnowledgeVerificationNetwork,
    "gap_detection": GapDetectionNetwork,
    "structured_recall": StructuredRecallNetwork,
    "mnemonic_encoding": MnemonicEncodingNetwork,
    "epistemic_calibration": EpistemicCalibrationNetwork,
}
