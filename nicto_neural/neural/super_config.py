import torch
import math
from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class SuperConfig:
    d_model: int = 2048
    n_heads: int = 16
    n_kv_heads: Optional[int] = None
    n_layers: int = 20
    d_ff: int = 8192
    n_experts: int = 8
    n_active_experts: int = 2
    expert_capacity_factor: float = 1.25
    vocab_size: int = 32768
    max_seq_len: int = 4096
    dropout: float = 0.1
    activation: str = "swiglu"
    eps: float = 1e-6
    device: str = ""
    dtype: str = "float32"
    use_mixed_precision: bool = False
    gradient_checkpointing: bool = False
    max_batch_size: int = 32
    n_brain_heads: int = 9
    brain_head_dim: int = 0
    reasoning_paths: int = 6
    reasoning_dim: int = 0
    use_rope: bool = True
    rope_theta: float = 10000.0
    use_flash_attn: bool = False
    n_shared_experts: int = 1
    moe_z_loss_coef: float = 0.001
    moe_aux_loss_coef: float = 0.01
    rope_scaling: Optional[dict] = None
    use_speculative: bool = False
    use_nas: bool = False
    use_hierarchical_moe: bool = False
    use_expert_choice: bool = False
    use_mixture_of_depths: bool = False
    use_ssm: bool = False
    spec_lookahead: int = 5
    n_expert_groups: int = 2
    n_moe_layers: int = 8
    mod_theta: float = 0.5
    ssm_d_state: int = 16
    nas_population: int = 10
    nas_generations: int = 20

    # MLA (Multi-head Latent Attention)
    use_mla: bool = False
    mla_compression_ratio: float = 0.25
    mla_separate_q: bool = True

    # Enhanced MoE
    use_enhanced_moe: bool = True

    # Advanced layers
    use_retention: bool = False
    use_gated_fusion: bool = False
    use_adaptive_inference: bool = False
    use_hierarchical_merge: bool = False
    use_ntm: bool = False
    use_xnet: bool = False
    use_hyper_connection: bool = False
    use_progressive_agg: bool = False
    use_sparse_moa: bool = False
    adaptive_max_steps: int = 5
    ntm_memory_size: int = 128
    ntm_memory_dim: int = 64

    # Domain specialists
    use_domain_specialists: bool = False
    n_domain_specialists: int = 100
    domain_specialist_dim: int = 256

    # Coding specialists
    use_coding_specialists: bool = False
    n_coding_specialists: int = 20
    coding_specialist_dim: int = 256

    # Speed reader
    use_speed_reader: bool = False
    speed_reader_chunk_size: int = 512
    speed_reader_streams: int = 4

    # Learning paradigms
    learning_paradigm: str = "auto"  # auto, supervised, unsupervised, semi_supervised, reinforcement, self_supervised

    def __post_init__(self):
        if not self.device:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.n_kv_heads is None:
            self.n_kv_heads = self.n_heads
        if self.brain_head_dim == 0:
            self.brain_head_dim = self.d_model // max(1, self.n_brain_heads)
        if self.reasoning_dim == 0:
            self.reasoning_dim = self.d_model

    @property
    def head_dim(self) -> int:
        return self.d_model // self.n_heads

    @property
    def kv_head_dim(self) -> int:
        return self.d_model // self.n_kv_heads if self.n_kv_heads > 0 else self.head_dim

    @property
    def expert_capacity(self) -> int:
        return int(self.max_batch_size * self.max_seq_len // self.n_experts * self.expert_capacity_factor)

    def estimate_params(self) -> dict:
        emb = self.vocab_size * self.d_model
        attn_per_layer = 4 * self.d_model * self.d_model
        expert_per_layer = self.n_experts * 3 * self.d_model * self.d_ff
        shared_per_layer = self.n_shared_experts * 3 * self.d_model * self.d_ff if self.n_shared_experts > 0 else 0
        moe_per_layer = expert_per_layer + shared_per_layer
        total_transformer = self.n_layers * (attn_per_layer + moe_per_layer)
        total_params = emb + total_transformer
        return {
            "embedding": emb,
            "attention": attn_per_layer * self.n_layers,
            "moe": moe_per_layer * self.n_layers,
            "total": total_params,
            "total_billions": total_params / 1e9,
        }


SMALL_CONFIG = SuperConfig(
    d_model=768,
    n_heads=12,
    n_kv_heads=4,
    n_layers=12,
    d_ff=2048,
    n_experts=4,
    n_active_experts=1,
    max_seq_len=2048,
    n_brain_heads=9,
)

MEDIUM_CONFIG = SuperConfig(
    d_model=1024,
    n_heads=16,
    n_kv_heads=8,
    n_layers=16,
    d_ff=4096,
    n_experts=8,
    n_active_experts=2,
    max_seq_len=4096,
    n_brain_heads=9,
)

LARGE_CONFIG = SuperConfig(
    d_model=2048,
    n_heads=16,
    n_kv_heads=8,
    n_layers=20,
    d_ff=8192,
    n_experts=8,
    n_active_experts=2,
    max_seq_len=8192,
    n_brain_heads=9,
)

HUGE_CONFIG = SuperConfig(
    d_model=4096,
    n_heads=32,
    n_kv_heads=8,
    n_layers=28,
    d_ff=16384,
    n_experts=16,
    n_active_experts=4,
    max_seq_len=16384,
    n_brain_heads=9,
)

ULTRA_CONFIG = SuperConfig(
    d_model=8192,
    n_heads=64,
    n_kv_heads=8,
    n_layers=40,
    d_ff=32768,
    n_experts=32,
    n_active_experts=6,
    max_seq_len=32768,
    n_brain_heads=9,
)

CONFIG_MAP = {
    "small": SMALL_CONFIG,
    "medium": MEDIUM_CONFIG,
    "large": LARGE_CONFIG,
    "huge": HUGE_CONFIG,
    "ultra": ULTRA_CONFIG,
}
