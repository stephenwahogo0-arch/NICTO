"""IntiraEngNet — Domain-specific neural network for engineering/quantum/home science/invention.

Specialist sub-networks:
  - EngineeringNet: Systems, mechanical, electrical, civil, software
  - QuantumNet: Quantum computing, algorithms, error correction
  - HomeScienceNet: Home automation, domestic energy, smart living
  - InventionNet: Innovation, patent analysis, design thinking
  - MechatronicsNet: Robotics, control systems, automation
  - MaterialScienceNet: Materials, nano tech, composites
  - AerospaceNet: Aeronautics, space systems, propulsion
  - EnergySysNet: Power systems, renewables, smart grid
  - QuantumEngNet: Quantum engineering, hardware, sensing
  - InnovationNet: Creative problem-solving, design methodology
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Tuple, Dict, List
from .super_config import SuperConfig
from .advanced_layers import MultiHeadLatentAttention, EnhancedMoE


class IntiraEngNetBase(nn.Module):
    """Base class for engineering neural networks with MLA + MoE."""
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


class EngineeringNet(IntiraEngNetBase):
    """Systems, mechanical, electrical, civil, software engineering."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "engineering")
        self.systems_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.design_gate = nn.Linear(config.d_model, config.d_model, bias=False)
        self.systems_head = nn.Linear(config.d_model, config.d_model // 2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h) + self.design_gate(x) * self.systems_encoder(x)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class QuantumNet(IntiraEngNetBase):
    """Quantum computing, algorithms, error correction, quantum information."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "quantum")
        self.quantum_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 3), nn.GELU(),
            nn.Linear(config.d_model * 3, config.d_model),
        )
        self.qubit_gate = nn.Linear(config.d_model, 1)
        self.quantum_head = nn.Linear(config.d_model, config.d_model)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        q = self.quantum_encoder(h) * torch.sigmoid(self.qubit_gate(h))
        h = h + q
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class HomeScienceNet(IntiraEngNetBase):
    """Home automation, domestic energy, smart living, sustainable housing."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "home_science")
        self.home_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.smart_gate = nn.Linear(config.d_model, config.d_model, bias=False)
        self.energy_head = nn.Linear(config.d_model, config.d_model // 2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h) + self.smart_gate(x) * self.home_encoder(x)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class InventionNet(IntiraEngNetBase):
    """Innovation, patent analysis, design thinking, creativity methods."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "invention")
        self.invent_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 3), nn.GELU(),
            nn.Linear(config.d_model * 3, config.d_model),
        )
        self.novelty_gate = nn.Linear(config.d_model, config.d_model)
        self.patent_head = nn.Linear(config.d_model, config.d_model // 2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        inv = torch.tanh(self.novelty_gate(h)) * self.invent_encoder(h)
        h = h + inv
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class MechatronicsNet(IntiraEngNetBase):
    """Robotics, control systems, automation, embedded systems."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "mechatronics")
        self.robot_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.control_gate = nn.Linear(config.d_model, config.d_model)
        self.robot_head = nn.Linear(config.d_model, config.d_model // 2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        robot = torch.sigmoid(self.control_gate(h)) * self.robot_encoder(h)
        h = h + robot
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class MaterialScienceNet(IntiraEngNetBase):
    """Materials science, nanotechnology, composites, smart materials."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "material_science")
        self.material_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.structure_gate = nn.Linear(config.d_model, 1)
        self.material_head = nn.Linear(config.d_model, config.d_model)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        mat = self.material_encoder(h) * torch.sigmoid(self.structure_gate(h))
        h = h + mat
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class AerospaceNet(IntiraEngNetBase):
    """Aeronautics, space systems, propulsion, orbital mechanics."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "aerospace")
        self.aero_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.flight_gate = nn.Linear(config.d_model, config.d_model, bias=False)
        self.space_head = nn.Linear(config.d_model, config.d_model // 2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h) + self.flight_gate(x) * self.aero_encoder(x)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class EnergySysNet(IntiraEngNetBase):
    """Power systems, renewable energy, smart grid, energy storage."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "energy_systems")
        self.energy_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.grid_gate = nn.Linear(config.d_model, config.d_model)
        self.power_head = nn.Linear(config.d_model, config.d_model // 2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        energy = torch.tanh(self.grid_gate(h)) * self.energy_encoder(h)
        h = h + energy
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class QuantumEngNet(IntiraEngNetBase):
    """Quantum engineering, quantum hardware, sensors, metrology."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "quantum_engineering")
        self.q_eng_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 3), nn.GELU(),
            nn.Linear(config.d_model * 3, config.d_model),
        )
        self.hardware_gate = nn.Linear(config.d_model, config.d_model, bias=False)
        self.sensor_head = nn.Linear(config.d_model, config.d_model)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h) + self.hardware_gate(x) * self.q_eng_encoder(x)
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


class InnovationNet(IntiraEngNetBase):
    """Creative problem-solving, design methodology, TRIZ, ideation."""
    def __init__(self, config: SuperConfig):
        super().__init__(config, "innovation")
        self.creative_encoder = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2), nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.ideation_gate = nn.Linear(config.d_model, config.d_model)
        self.design_head = nn.Linear(config.d_model, config.d_model // 2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm_in(x)
        h = self.mla(h)
        creative = torch.tanh(self.ideation_gate(h)) * self.creative_encoder(h)
        h = h + creative
        h = self.norm_mid(h)
        moe_out = self.moe(h)
        h = self.norm_out(h + moe_out)
        out = self.output_proj(h)
        conf = self.confidence(h.mean(dim=1))
        return out, conf.squeeze(-1)


ENG_NET_SPECIALISTS: Dict[str, str] = {
    "engineering": "Systems, mechanical, electrical, civil, software engineering",
    "quantum": "Quantum computing, algorithms, error correction",
    "home_science": "Home automation, domestic energy, smart living",
    "invention": "Innovation, patent analysis, design thinking",
    "mechatronics": "Robotics, control systems, automation",
    "material_science": "Materials, nanotechnology, composites",
    "aerospace": "Aeronautics, space systems, propulsion",
    "energy_systems": "Power systems, renewables, smart grid",
    "quantum_engineering": "Quantum engineering, hardware, sensing",
    "innovation": "Creative problem-solving, design methodology",
}


ENG_NET_REGISTRY = {
    "engineering": EngineeringNet,
    "quantum": QuantumNet,
    "home_science": HomeScienceNet,
    "invention": InventionNet,
    "mechatronics": MechatronicsNet,
    "material_science": MaterialScienceNet,
    "aerospace": AerospaceNet,
    "energy_systems": EnergySysNet,
    "quantum_engineering": QuantumEngNet,
    "innovation": InnovationNet,
}


class IntiraEngNetEnsemble(nn.Module):
    """Ensemble of all IntiraEngNet specialists with routing."""
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.config = config
        self.specialists = nn.ModuleDict()
        self.confidence = nn.Sequential(
            nn.Linear(config.d_model, 64), nn.ReLU(), nn.Linear(64, 1), nn.Sigmoid()
        )
        self.routing = nn.Linear(config.d_model, len(ENG_NET_REGISTRY))
        for name, cls in ENG_NET_REGISTRY.items():
            self.specialists[name] = cls(config)
        self.router_weights = nn.Parameter(torch.ones(len(ENG_NET_REGISTRY)) / len(ENG_NET_REGISTRY))

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
