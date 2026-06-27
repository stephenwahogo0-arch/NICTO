"""IntiraBioNet — Domain-specific neural network for bio/medicine/biology/chemistry/physics.

Specialist sub-networks:
  - BioMedicineNet: Drug discovery, disease modeling, clinical analysis
  - ChemistryNet: Molecular modeling, reaction prediction, properties
  - BiologyNet: Genetics, proteomics, cellular pathways, ecology
  - PhysicsNet: Physical simulation, quantum bio, biophysics
  - NeuroscienceNet: Brain modeling, neural circuits
  - PharmacologyNet: ADMET prediction, drug interactions
  - GenomicsNet: DNA/RNA analysis, gene expression
  - ImmunologyNet: Immune response, vaccine design
  - SystemsBioNet: Multi-scale biological systems
  - BiomedInformaticsNet: Medical data integration
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Tuple, Dict, List
from .super_config import SuperConfig
from .advanced_layers import MultiHeadLatentAttention, EnhancedMoE


class IntiraBioNetBase(nn.Module):
    """Base class for bio-medical neural networks with MLA + MoE."""
    def __init__(self, config: SuperConfig, name: str = ""):
        super().__init__()
        self.name = name
        self.d_model = config.d_model
        self.mla = MultiHeadLatentAttention(config)
        self.moe = EnhancedMoE(config)
        self.norm_in = nn.LayerNorm(config.d_model)
        self.norm_mid = nn.LayerNorm(config.d_model)
        self.norm_out = nn.LayerNorm(config.d_model)
        self.confidence = nn.Sequential(
            nn.Linear(config.d_model, 64), nn.ReLU(), nn.Linear(64, 1), nn.Sigmoid()
        )
        self.output_proj = nn.Linear(config.d_model, config.d_model)
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear) and m is not self.confidence and m is not self.output_proj:
                nn.init.xavier_uniform_(m.weight, gain=0.5)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class BioMedicineNet(IntiraBioNetBase):
    """Drug discovery, disease modeling, clinical trial analysis, precision medicine."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "bio_medicine")
        self.disease_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.treatment_gate = nn.Linear(config.d_model, config.d_model, bias=False)
        self.clinical_head = nn.Linear(config.d_model, 6)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h) + self.treatment_gate(x) * self.disease_encoder(x)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class ChemistryNet(IntiraBioNetBase):
    """Molecular modeling, reaction prediction, chemical properties, spectroscopy."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "chemistry")
        self.molecule_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 3), nn.GELU(),
            nn.Linear(config.d_model * 3, config.d_model),
        )
        self.bond_gate = nn.Linear(config.d_model, 1)
        self.reaction_head = nn.Linear(config.d_model, config.d_model)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        mol = self.molecule_encoder(h) * torch.sigmoid(self.bond_gate(h))
        h = h + mol
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class BiologyNet(IntiraBioNetBase):
    """Genetics, proteomics, cellular pathways, ecology, evolutionary biology."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "biology")
        self.pathway_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.cellular_gate = nn.Linear(config.d_model, config.d_model)
        self.eco_head = nn.Linear(config.d_model, config.d_model // 2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        pathway = torch.tanh(self.cellular_gate(h)) * self.pathway_encoder(h)
        h = h + pathway
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class PhysicsNet(IntiraBioNetBase):
    """Physical simulation, quantum biology, biophysics, statistical mechanics."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "physics_bio")
        self.quantum_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.psi_gate = nn.Linear(config.d_model, config.d_model, bias=False)
        self.sim_head = nn.Linear(config.d_model, config.d_model)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h) + self.psi_gate(x) * self.quantum_encoder(x)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class NeuroscienceNet(IntiraBioNetBase):
    """Brain modeling, neural circuits, cognitive neuroscience, BCI."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "neuroscience")
        self.brain_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.circuit_gate = nn.Linear(config.d_model, config.d_model)
        self.bci_head = nn.Linear(config.d_model, config.d_model // 2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        circuit = torch.sigmoid(self.circuit_gate(h)) * self.brain_encoder(h)
        h = h + circuit
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class PharmacologyNet(IntiraBioNetBase):
    """ADMET prediction, drug interactions, pharmacokinetics, toxicology."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "pharmacology")
        self.admet_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.drug_gate = nn.Linear(config.d_model, 1)
        self.tox_head = nn.Linear(config.d_model, 8)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        admet = self.admet_encoder(h) * torch.sigmoid(self.drug_gate(h))
        h = h + admet
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class GenomicsNet(IntiraBioNetBase):
    """DNA/RNA analysis, gene expression, CRISPR, epigenomics."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "genomics")
        self.genome_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.seq_gate = nn.Linear(config.d_model, config.d_model, bias=False)
        self.expr_head = nn.Linear(config.d_model, config.d_model // 2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h) + self.seq_gate(x) * self.genome_encoder(x)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class ImmunologyNet(IntiraBioNetBase):
    """Immune response, vaccine design, antibody engineering, immunotherapy."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "immunology")
        self.immune_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.ab_gate = nn.Linear(config.d_model, config.d_model)
        self.vaccine_head = nn.Linear(config.d_model, 4)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        immune = torch.tanh(self.ab_gate(h)) * self.immune_encoder(h)
        h = h + immune
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class SystemsBioNet(IntiraBioNetBase):
    """Multi-scale biological systems, metabolic pathways, network biology."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "systems_bio")
        self.system_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 3), nn.GELU(),
            nn.Linear(config.d_model * 3, config.d_model),
        )
        self.scale_gate = nn.Linear(config.d_model, config.d_model)
        self.network_head = nn.Linear(config.d_model, config.d_model // 2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        scale = torch.sigmoid(self.scale_gate(h)) * self.system_encoder(h)
        h = h + scale
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class BiomedInformaticsNet(IntiraBioNetBase):
    """Medical data integration, health informatics, clinical NLP, imaging."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "biomed_informatics")
        self.data_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.fusion_gate = nn.Linear(config.d_model, 1)
        self.clinical_head = nn.Linear(config.d_model, config.d_model)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        fused = self.data_encoder(h) * torch.sigmoid(self.fusion_gate(h))
        h = h + fused
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


BIO_NET_SPECIALISTS: Dict[str, str] = {
    "bio_medicine": "Drug discovery, disease modeling, clinical analysis",
    "chemistry": "Molecular modeling, reaction prediction, spectroscopy",
    "biology": "Genetics, proteomics, cellular pathways, ecology",
    "physics_bio": "Biophysics, quantum biology, physical simulation",
    "neuroscience": "Brain modeling, neural circuits, cognitive neuroscience",
    "pharmacology": "ADMET prediction, drug interactions, toxicology",
    "genomics": "DNA/RNA analysis, gene expression, CRISPR",
    "immunology": "Immune response, vaccine design, immunotherapy",
    "systems_bio": "Multi-scale biological systems, metabolic pathways",
    "biomed_informatics": "Medical data integration, health informatics",
}


BIO_NET_REGISTRY = {
    "bio_medicine": BioMedicineNet,
    "chemistry": ChemistryNet,
    "biology": BiologyNet,
    "physics_bio": PhysicsNet,
    "neuroscience": NeuroscienceNet,
    "pharmacology": PharmacologyNet,
    "genomics": GenomicsNet,
    "immunology": ImmunologyNet,
    "systems_bio": SystemsBioNet,
    "biomed_informatics": BiomedInformaticsNet,
}


class IntiraBioNetEnsemble(nn.Module):
    """Ensemble of all IntiraBioNet specialists with routing."""
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.config = config
        self.specialists = nn.ModuleDict()
        self.confidence = nn.Sequential(
            nn.Linear(config.d_model, 64), nn.ReLU(), nn.Linear(64, 1), nn.Sigmoid()
        )
        self.routing = nn.Linear(config.d_model, len(BIO_NET_REGISTRY))
        for name, cls in BIO_NET_REGISTRY.items():
            self.specialists[name] = cls(config)
        self.router_weights = nn.Parameter(torch.ones(len(BIO_NET_REGISTRY)) / len(BIO_NET_REGISTRY))

    def forward(self, x: torch.Tensor, domain: Optional[str] = None) -> Tuple[torch.Tensor, torch.Tensor, Dict]:
        if domain and domain in self.specialists:
            out, conf = self.specialists[domain](x)
            return out, conf, {"domain": domain, "routed": True}

        routing_logits = self.routing(x.mean(dim=1))
        routing_weights = F.softmax(routing_logits * self.router_weights, dim=-1)

        outputs = []
        confs = []
        for name, specialist in self.specialists.items():
            o, c = specialist(x)
            outputs.append(o)
            confs.append(c.unsqueeze(-1))

        stacked = torch.stack(outputs, dim=0)
        stacked_confs = torch.stack(confs, dim=0)
        weighted = (stacked * routing_weights.t().unsqueeze(-1).unsqueeze(-1)).sum(dim=0)
        avg_conf = (torch.cat(confs, dim=-1) * routing_weights).sum(dim=-1, keepdim=True)

        return weighted, avg_conf.squeeze(-1), {
            "routed": False,
            "weights": routing_weights.detach(),
        }

    def get_specialist(self, name: str) -> Optional[nn.Module]:
        return self.specialists.get(name)

    def list_specialists(self) -> List[str]:
        return list(self.specialists.keys())
