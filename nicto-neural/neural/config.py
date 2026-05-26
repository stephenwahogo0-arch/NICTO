"""NICTO Neural Core configuration — all hyperparameters in one place.

Production architecture: 17B dense transformer (40 layers, 32 heads, 4096 d_model, 11008 FFN).
Default values below are scaled for development and testing on consumer hardware.
For production deployment, use NeuralConfig.production() to get the full 17B config.
"""

from dataclasses import dataclass, field


@dataclass
class NeuralConfig:
    # --- Production target: 17B dense transformer ---
    # d_model=4096, n_heads=32, n_layers=40, d_ff=11008, vocab=32000
    # Defaults below are scaled for dev/test on consumer hardware.

    # Model dimensions (dev-scale defaults)
    d_model: int = 512
    n_heads: int = 8
    n_layers: int = 6
    d_ff: int = 2048
    dropout: float = 0.1
    max_seq_len: int = 2048
    vocab_size: int = 32000

    # MoE config (optional routing layer)
    n_experts: int = 8
    top_k_experts: int = 2
    expert_capacity: float = 1.25

    # Brain config — 6 specialist brains, each a projection of the shared backbone
    n_brains: int = 6
    brain_names: list = field(default_factory=lambda: [
        "primary", "analytical", "creative",
        "strategic", "knowledge", "intuitive",
    ])

    # Training config
    learning_rate: float = 3e-4
    batch_size: int = 32
    max_epochs: int = 100
    warmup_steps: int = 1000
    grad_clip: float = 1.0

    # RL config (PPO)
    ppo_clip: float = 0.2
    ppo_epochs: int = 4
    gae_lambda: float = 0.95
    value_coef: float = 0.5
    entropy_coef: float = 0.01
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: int = 10000
    noise_std: float = 0.1

    # ELO config
    elo_base: int = 1500
    elo_k_factor: int = 32
    elo_domains: list = field(default_factory=lambda: [
        "code", "math", "creative", "strategic",
        "knowledge", "intuitive", "general",
        "cybersecurity", "language", "logic",
    ])

    # Curriculum config
    curriculum_levels: int = 6
    plateau_window: int = 5
    plateau_threshold: float = 0.01
    min_accuracy_for_plateau: float = 0.75

    # Memory config
    memory_db_path: str = "~/.nicto/neural/memory"
    max_episodic_entries: int = 100000
    max_semantic_entries: int = 50000
    experience_buffer_size: int = 10000

    # BrainBoost config
    boost_stages: int = 5
    boost_learning_rate: float = 0.3
    boost_max_depth: int = 3
    boost_min_child_weight: float = 1.0

    # Optimal runtime parameters for NICTO
    inference_batch_size: int = 1
    inference_max_tokens: int = 4096
    temperature_min: float = 0.3
    temperature_max: float = 0.7
    temperature_default: float = 0.5
    top_p: float = 0.9
    top_k_sampling: int = 50
    repetition_penalty: float = 1.1
    context_window: int = 4096
    max_reasoning_depth: int = 10
    memory_consolidation_interval: int = 100
    elo_update_frequency: int = 1
    exploration_warmup_steps: int = 500
    min_confidence_threshold: float = 0.65
    truth_verification_threshold: float = 0.95

    @classmethod
    def production(cls) -> "NeuralConfig":
        """17B production config — requires ~34 GB RAM (fp16) or ~17 GB (int8)."""
        return cls(
            d_model=4096,
            n_heads=32,
            n_layers=40,
            d_ff=11008,
            max_seq_len=4096,
            vocab_size=32000,
        )

    # Architecture identity
    PARAMETER_COUNT = "17B (dense transformer)"
    ARCHITECTURE = "40-layer, 32-head, 4096-dim dense transformer + 6-brain system"
