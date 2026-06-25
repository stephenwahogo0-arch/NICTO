"""Math Brain — 10 MoE+MLA neural networks for pure math & theoretical physics."""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Tuple, Dict, List
from .super_config import SuperConfig
from .advanced_layers import MultiHeadLatentAttention, EnhancedMoE


class MathBrainBase(nn.Module):
    """Base class for all math brain networks — every one uses MLA + MoE."""
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
        conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class PureAlgebraNetwork(MathBrainBase):
    """Pure math — algebra, group/ring/field theory, Galois theory, category theory."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "algebra")
        self.structure_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.axiom_gate = nn.Linear(config.d_model, config.d_model, bias=False)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h) + self.axiom_gate(x) * self.structure_encoder(x)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class AnalysisNetwork(MathBrainBase):
    """Real/complex/functional analysis, measure theory, topology."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "analysis")
        self.limit_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model), nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )
        self.convergence_gate = nn.Linear(config.d_model, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        h = h + self.limit_encoder(h) * torch.sigmoid(self.convergence_gate(h))
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class GeometryTopologyNetwork(MathBrainBase):
    """Differential geometry, algebraic topology, manifolds, bundles."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "geometry")
        self.metric_encoder = nn.Linear(config.d_model, config.d_model)
        self.curvature_ffn = nn.Sequential(
            nn.Linear(config.d_model, config.d_model), nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        h = h + self.curvature_ffn(self.metric_encoder(h))
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class NumberTheoryNetwork(MathBrainBase):
    """Number theory, primes, Diophantine equations, modular forms, cryptography."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "number_theory")
        self.modular_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.arithmetic_gate = nn.Linear(config.d_model, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        gate = torch.sigmoid(self.arithmetic_gate(h))
        h = h + gate * self.modular_encoder(h)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1, keepdim=True))
        return out, conf.squeeze(-1)


class QuantumMechanicsNetwork(MathBrainBase):
    """QM formalism, Hilbert spaces, perturbation theory, scattering."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "quantum")
        self.hilbert_proj = nn.Linear(config.d_model, config.d_model)
        self.hamiltonian_ffn = nn.Sequential(
            nn.Linear(config.d_model, config.d_model), nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )
        self.energy_head = nn.Linear(config.d_model, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        psi = self.hilbert_proj(h)
        h = h + self.hamiltonian_ffn(psi)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        e = torch.sigmoid(self.energy_head(h.mean(dim=1, keepdim=True)))
        conf = self.confidence(h.mean(dim=1, keepdim=True)) * e
        return out, conf.squeeze(-1)


class RelativityCosmologyNetwork(MathBrainBase):
    """GR, SR, black holes, cosmology, Friedman equations, inflation."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "relativity")
        self.metric_tensor = nn.Linear(config.d_model, config.d_model)
        self.einstein_ffn = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.stress_energy = nn.Linear(config.d_model, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        g = self.metric_tensor(h)
        h = h + self.einstein_ffn(g)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        T = torch.sigmoid(self.stress_energy(h.mean(dim=1, keepdim=True)))
        conf = self.confidence(h.mean(dim=1, keepdim=True)) * T
        return out, conf.squeeze(-1)


class StatisticalMechanicsNetwork(MathBrainBase):
    """Statistical mechanics, thermodynamics, ensembles, phase transitions."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "stat_mech")
        self.partition_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model), nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )
        self.entropy_head = nn.Linear(config.d_model, 1)
        self.temperature_gate = nn.Linear(config.d_model, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        beta = torch.sigmoid(self.temperature_gate(h))
        h = h + beta * self.partition_encoder(h)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        S = torch.sigmoid(self.entropy_head(h.mean(dim=1, keepdim=True)))
        conf = self.confidence(h.mean(dim=1, keepdim=True)) * (1 + S) / 2
        return out, conf.squeeze(-1)


class ParticleFieldTheoryNetwork(MathBrainBase):
    """QFT, Standard Model, Feynman diagrams, gauge theories, renormalization."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "qft")
        self.lagrangian_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.gauge_proj = nn.Linear(config.d_model, config.d_model)
        self.feynman_gate = nn.Linear(config.d_model, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        L = self.lagrangian_encoder(x)
        h = self.mla(h) + self.gauge_proj(L)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        g = torch.sigmoid(self.feynman_gate(h.mean(dim=1, keepdim=True)))
        conf = self.confidence(h.mean(dim=1, keepdim=True)) * g
        return out, conf.squeeze(-1)


class MathPhysicsBridgeNetwork(MathBrainBase):
    """Connects pure math to physics — symmetries, Lie groups, conservation laws, diff eq."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "math_physics_bridge")
        self.symmetry_encoder = nn.Linear(config.d_model, config.d_model)
        self.conservation_ffn = nn.Sequential(
            nn.Linear(config.d_model, config.d_model), nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )
        self.lie_algebra = nn.Linear(config.d_model, config.d_model)
        self.bridge_gate = nn.Linear(config.d_model, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        sym = self.symmetry_encoder(x)
        lie = self.lie_algebra(x)
        h = self.mla(h) + self.conservation_ffn(sym + lie)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        g = torch.sigmoid(self.bridge_gate(h.mean(dim=1, keepdim=True)))
        conf = self.confidence(h.mean(dim=1, keepdim=True)) * g
        return out, conf.squeeze(-1)


class ComputationalMathPhysicsNetwork(MathBrainBase):
    """Numerical methods, simulation, finite elements, Monte Carlo, spectral methods."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "computational_math")
        self.discretizer = nn.Linear(config.d_model, config.d_model)
        self.solver = nn.Sequential(
            nn.Linear(config.d_model, config.d_model), nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )
        self.convergence_head = nn.Linear(config.d_model, 1)
        self.iterations = 3

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        h = self.discretizer(h)
        for _ in range(self.iterations):
            h = h + self.solver(h)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conv = torch.sigmoid(self.convergence_head(h.mean(dim=1, keepdim=True)))
        conf = self.confidence(h.mean(dim=1, keepdim=True)) * conv
        return out, conf.squeeze(-1)


MATH_BRAIN_NETWORKS = {
    "algebra": PureAlgebraNetwork,
    "analysis": AnalysisNetwork,
    "geometry_topology": GeometryTopologyNetwork,
    "number_theory": NumberTheoryNetwork,
    "quantum_mechanics": QuantumMechanicsNetwork,
    "relativity_cosmology": RelativityCosmologyNetwork,
    "statistical_mechanics": StatisticalMechanicsNetwork,
    "particle_field_theory": ParticleFieldTheoryNetwork,
    "math_physics_bridge": MathPhysicsBridgeNetwork,
    "computational_math_physics": ComputationalMathPhysicsNetwork,
}
