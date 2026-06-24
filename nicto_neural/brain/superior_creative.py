"""SuperiorCreativeBrain — 500K+ parameter multi-domain creative brain.

Architecture:
- Multi-head self-attention over knowledge domain embeddings
- Cross-attention between visual concepts and text prompts
- Knowledge graph connection layer (camera angles ↔ lighting ↔ genres ↔ composition ↔ grading)
- 8 specialized output heads: visual_describe, critique, compose, light, grade, direct, storyboard, innovate
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class KnowledgeEmbedding(nn.Module):
    """Embeds structured knowledge (camera angles, lighting, etc.) into vectors."""

    def __init__(self, d_model: int, n_domains: int = 5, entries_per_domain: int = 50):
        super().__init__()
        self.domain_embed = nn.Embedding(n_domains, d_model)
        self.entry_embed = nn.Embedding(entries_per_domain, d_model)
        self.output_proj = nn.Linear(d_model * 2, d_model)

    def forward(self, domain_ids: torch.Tensor, entry_ids: torch.Tensor) -> torch.Tensor:
        d = self.domain_embed(domain_ids)
        e = self.entry_embed(entry_ids)
        return self.output_proj(torch.cat([d, e], dim=-1))


class KnowledgeGraphAttention(nn.Module):
    """Cross-attention between knowledge domains — e.g. how camera angle choice affects lighting."""

    def __init__(self, d_model: int, n_heads: int = 8, n_domains: int = 5):
        super().__init__()
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        self.n_domains = n_domains
        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model, d_model)
        self.domain_gate = nn.Parameter(torch.ones(n_domains, n_domains) * 0.5)

    def forward(self, x: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
        B, N, D = x.shape
        H = self.n_heads
        Dh = self.d_head

        q = self.q_proj(x).view(B, N, H, Dh).transpose(1, 2)
        k = self.k_proj(x).view(B, N, H, Dh).transpose(1, 2)
        v = self.v_proj(x).view(B, N, H, Dh).transpose(1, 2)

        gate = torch.sigmoid(self.domain_gate).unsqueeze(0).unsqueeze(0)
        attn = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(Dh)
        attn = attn * gate
        if mask is not None:
            attn = attn.masked_fill(mask == 0, float("-inf"))
        attn = F.softmax(attn, dim=-1)

        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().view(B, N, D)
        return self.out_proj(out)


class CrossModalAttention(nn.Module):
    """Cross-attention between visual knowledge and text prompts."""

    def __init__(self, d_visual: int, d_text: int, d_model: int, n_heads: int = 8):
        super().__init__()
        self.q_proj = nn.Linear(d_visual, d_model)
        self.k_proj = nn.Linear(d_text, d_model)
        self.v_proj = nn.Linear(d_text, d_model)
        self.out_proj = nn.Linear(d_model, d_visual)
        self.n_heads = n_heads
        self.d_head = d_model // n_heads

    def forward(self, visual: torch.Tensor, text: torch.Tensor) -> torch.Tensor:
        B, Nv, Dv = visual.shape
        B, Nt, Dt = text.shape
        H = self.n_heads
        Dh = self.d_head

        q = self.q_proj(visual).view(B, Nv, H, Dh).transpose(1, 2)
        k = self.k_proj(text).view(B, Nt, H, Dh).transpose(1, 2)
        v = self.v_proj(text).view(B, Nt, H, Dh).transpose(1, 2)

        attn = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(Dh)
        attn = F.softmax(attn, dim=-1)
        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().view(B, Nv, Dv)
        return self.out_proj(out)


class SuperiorCreativeBrain(nn.Module):
    """500K+ parameter creative brain with knowledge graph, cross-modal attention, and specialized output heads."""

    def __init__(self, d_model: int = 512, n_heads: int = 8, n_layers: int = 4, n_domains: int = 5, vocab_size: int = 512):
        super().__init__()
        self.d_model = d_model
        self.n_domains = n_domains

        self.knowledge_embed = KnowledgeEmbedding(d_model, n_domains, 50)
        self.text_proj = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, d_model),
        )

        self.graph_attn = KnowledgeGraphAttention(d_model, n_heads, n_domains)
        self.cross_attn = CrossModalAttention(d_model, d_model, d_model, n_heads)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_model * 4,
            dropout=0.1, activation="gelu", batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)

        self.divergent_noise = nn.Sequential(
            nn.Linear(d_model, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
            nn.Sigmoid(),
        )
        self.noise_scale = nn.Parameter(torch.tensor(0.5))

        self.concept_projector = nn.Linear(d_model, 64)

        self.output_heads = nn.ModuleDict({
            "visual_describe": nn.Linear(d_model, d_model),
            "critique": nn.Linear(d_model, 6),
            "compose": nn.Linear(d_model, 8),
            "light": nn.Linear(d_model, 11),
            "grade": nn.Linear(d_model, 6),
            "direct": nn.Linear(d_model, d_model),
            "storyboard": nn.Linear(d_model, d_model),
            "innovate": nn.Linear(d_model, d_model),
        })

        self.confidence_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Linear(d_model // 2, 1),
            nn.Sigmoid(),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight, gain=1.0)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Embedding):
                nn.init.normal_(m.weight, mean=0, std=0.02)
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor, domain_ids: torch.Tensor = None,
                entry_ids: torch.Tensor = None, temperature: float = 0.8) -> dict:
        B, T, D = x.shape

        text_feats = self.text_proj(x)

        if domain_ids is not None and entry_ids is not None:
            kb_feats = self.knowledge_embed(domain_ids, entry_ids)
            kb_feats = kb_feats.unsqueeze(0).expand(B, -1, -1)
        else:
            kb_feats = torch.randn(B, self.n_domains, self.d_model, device=x.device)

        kb_feats = self.graph_attn(kb_feats)
        fused = self.cross_attn(kb_feats, text_feats)

        combined = torch.cat([text_feats, fused], dim=1)
        encoded = self.transformer(combined)

        noise_gate = self.divergent_noise(encoded)
        noise = torch.randn_like(encoded) * self.noise_scale * temperature
        encoded = encoded + noise * noise_gate

        concept_embeds = self.concept_projector(encoded)

        confidence = self.confidence_head(encoded)

        outputs = {}
        for name, head in self.output_heads.items():
            outputs[name] = head(encoded)

        return {
            "encoded": encoded,
            "concept_embeds": concept_embeds,
            "confidence": confidence.squeeze(-1),
            "outputs": outputs,
        }

    def brainstorm_creative_brief(self, prompt: str, n_concepts: int = 10) -> list[dict]:
        device = next(self.parameters()).device
        dummy = torch.randn(1, n_concepts, self.d_model, device=device)
        out = self.forward(dummy, temperature=1.2)
        concept_embeds = out["concept_embeds"]
        confidence = out["confidence"]

        concepts = []
        for i in range(n_concepts):
            seed = concept_embeds[0, i].detach().cpu().numpy()
            seed_flat = seed.ravel()
            tags = []
            tag_names = ["novel", "practical", "elegant", "scalable", "bold", "subtle", "dynamic", "atmospheric", "minimalist", "cinematic"]
            for j, tag_name in enumerate(tag_names):
                if j < len(seed_flat) and seed_flat[j] > 0:
                    tags.append(tag_name)
            if not tags:
                tags.append("alternative")

            visual_desc = out["outputs"]["visual_describe"][0, i]
            conf = confidence[0, i].item()

            concepts.append({
                "id": i,
                "tags": tags[:4],
                "diversity_score": float(abs(seed_flat).mean()),
                "confidence": conf,
                "prompt": prompt,
                "visual_intensity": float(torch.sigmoid(visual_desc).mean()),
            })

        concepts.sort(key=lambda c: c["confidence"] * c["diversity_score"], reverse=True)
        return concepts


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
