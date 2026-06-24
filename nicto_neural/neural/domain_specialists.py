"""100 domain-specialized neural networks — one per domain."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional


class DomainSpecialist(nn.Module):
    """Base class — 3-layer bottleneck with residual."""
    def __init__(self, d_model: int = 256, domain_id: int = 0, name: str = ""):
        super().__init__()
        D = d_model
        self.name = name
        self.domain_id = domain_id
        self.net = nn.Sequential(
            nn.Linear(D, D * 2), nn.GELU(), nn.Dropout(0.1),
            nn.Linear(D * 2, D * 2), nn.GELU(), nn.Dropout(0.1),
            nn.Linear(D * 2, D),
        )
        self.gate = nn.Parameter(torch.ones(1))
        self.norm = nn.LayerNorm(D)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.norm(x + self.net(x) * torch.sigmoid(self.gate))


# 100 domains — complete list
DOMAIN_SPECIALISTS: Dict[str, str] = {
    "aerospace": "Aerospace engineering + orbital mechanics",
    "agriculture": "Farming, crops, soil science, agronomy",
    "anthropology": "Human cultures, evolution, archaeology",
    "architecture": "Building design, urban planning, structures",
    "art": "Visual arts, painting, sculpture, galleries",
    "astronomy": "Stars, planets, cosmology, space",
    "astrophysics": "Stellar physics, black holes, relativity",
    "biochemistry": "Chemical processes in living organisms",
    "bioengineering": "Engineering solutions for biology",
    "bioinformatics": "Computational biology, genomics",
    "biology": "Life sciences, organisms, ecosystems",
    "blockchain": "Distributed ledgers, crypto, smart contracts",
    "botany": "Plants, algae, fungi, plant biology",
    "business": "Management, strategy, operations",
    "catalysis": "Chemical catalysts, reaction kinetics",
    "chemistry": "Chemical compounds, reactions, elements",
    "civil_engineering": "Infrastructure, bridges, roads, dams",
    "climatology": "Climate, weather patterns, atmosphere",
    "cognitive_science": "Mind, cognition, intelligence",
    "communication": "Media, telecom, signal processing",
    "computing": "General computing, algorithms, systems",
    "criminology": "Crime, justice, forensics",
    "cryptography": "Encryption, security protocols, hashing",
    "cybersecurity": "Threats, defense, penetration testing",
    "dance": "Choreography, movement, performance",
    "data_science": "Analytics, statistics, visualization",
    "demography": "Population, migration, census",
    "earth_science": "Geology, seismology, earth systems",
    "ecology": "Ecosystems, biodiversity, conservation",
    "economics": "Markets, finance, macro/micro economics",
    "education": "Teaching, pedagogy, learning theory",
    "electrical_engineering": "Circuits, electronics, power",
    "energy": "Power generation, renewables, grid",
    "engineering": "General engineering, mechanics, design",
    "environmental_science": "Environment, pollution, sustainability",
    "epidemiology": "Disease spread, public health",
    "ethics": "Moral philosophy, applied ethics",
    "fashion": "Clothing, design, textiles, style",
    "film": "Cinema, production, directing, editing",
    "finance": "Investing, banking, markets, analysis",
    "gastronomy": "Food, cooking, cuisine, nutrition",
    "genetics": "DNA, genes, heredity, genomics",
    "geography": "Maps, regions, human geography",
    "geology": "Rocks, minerals, earth processes",
    "geophysics": "Earth physics, gravity, magnetics",
    "graphic_design": "Visual design, typography, layout",
    "history": "Historical events, periods, analysis",
    "immunology": "Immune system, vaccines, antibodies",
    "information_theory": "Entropy, compression, channels",
    "international_relations": "Diplomacy, geopolitics, treaties",
    "journalism": "News, reporting, media ethics",
    "law": "Legal systems, cases, jurisprudence",
    "linguistics": "Language, grammar, phonetics, semantics",
    "literature": "Writing, poetry, novels, criticism",
    "logic": "Reasoning, proofs, formal systems",
    "machine_learning": "ML models, training, algorithms",
    "marine_biology": "Ocean life, marine ecosystems",
    "marketing": "Advertising, branding, consumer behavior",
    "materials_science": "Materials, properties, engineering",
    "mathematics": "Pure/applied math, theorems, proofs",
    "mechanical_engineering": "Machines, thermodynamics, design",
    "medicine": "Healthcare, diagnosis, treatment",
    "meteorology": "Weather, forecasting, atmospheric science",
    "microbiology": "Microorganisms, bacteria, viruses",
    "military_science": "Tactics, strategy, defense",
    "music": "Theory, composition, performance",
    "nanotechnology": "Nanoscale science, materials, devices",
    "neuroscience": "Brain, neurons, cognition, neurology",
    "nuclear_physics": "Atomic nuclei, radiation, reactors",
    "nursing": "Patient care, clinical practice",
    "nutrition": "Diet, food science, health",
    "oceanography": "Oceans, currents, marine science",
    "optics": "Light, lenses, photonics, vision",
    "paleontology": "Fossils, prehistoric life, evolution",
    "pathology": "Disease mechanisms, diagnosis",
    "pedagogy": "Teaching methods, curriculum design",
    "pharmacology": "Drugs, therapeutics, pharmacokinetics",
    "philosophy": "Knowledge, reality, existence, ethics",
    "photography": "Cameras, composition, editing",
    "physics": "Fundamental forces, matter, energy",
    "physiology": "Body function, organs, systems",
    "political_science": "Government, policy, politics",
    "psychiatry": "Mental health, diagnosis, therapy",
    "psychology": "Mind, behavior, cognition, emotion",
    "public_health": "Population health, prevention, policy",
    "quantum_computing": "Qubits, quantum gates, algorithms",
    "robotics": "Robot design, control, automation",
    "semiconductors": "Chips, transistors, fabrication",
    "sociology": "Society, social structures, groups",
    "software_engineering": "Code, design patterns, best practices",
    "sports_science": "Athletics, training, biomechanics",
    "statistics": "Probability, inference, modeling",
    "sustainability": "Sustainable development, ESG",
    "telecommunications": "Networks, wireless, signal processing",
    "theater": "Performance, drama, stage production",
    "theology": "Religion, belief systems, scripture",
    "transportation": "Logistics, vehicles, infrastructure",
    "urban_studies": "Cities, planning, development",
    "veterinary_science": "Animal health, medicine, surgery",
    "virology": "Viruses, infections, antivirals",
    "zoology": "Animals, behavior, taxonomy",
}


class DomainSpecialistEnsemble(nn.Module):
    """All 100 domain specialists in one container. Routes input to correct specialist."""
    def __init__(self, d_model: int = 256):
        super().__init__()
        self.d_model = d_model
        self.domains = sorted(DOMAIN_SPECIALISTS.keys())
        self.specialists = nn.ModuleDict({
            name: DomainSpecialist(d_model, i, name)
            for i, name in enumerate(self.domains)
        })
        self.domain_router = nn.Linear(d_model, len(self.domains))

    def forward(self, x: torch.Tensor, domain_hint: Optional[str] = None) -> torch.Tensor:
        if domain_hint and domain_hint in self.specialists:
            return self.specialists[domain_hint](x)
        routes = F.softmax(self.domain_router(x.mean(dim=1)), dim=-1)
        top_domains = routes.topk(3, dim=-1)
        out = 0
        for i in range(3):
            name = self.domains[top_domains.indices[0, i].item()]
            w = top_domains.values[0:1, i:i+1].unsqueeze(-1)
            out = out + self.specialists[name](x) * w
        return out

    def get_specialist(self, name: str) -> Optional[DomainSpecialist]:
        return self.specialists.get(name)

    def list_domains(self) -> List[str]:
        return self.domains
