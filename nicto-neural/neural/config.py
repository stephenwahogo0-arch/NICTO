"""NICTO Neural Core configuration — all hyperparameters in one place."""

from dataclasses import dataclass, field


@dataclass
class NeuralConfig:
    # Model dimensions
    d_model: int = 512
    n_heads: int = 8
    n_layers: int = 6
    d_ff: int = 2048
    dropout: float = 0.1
    max_seq_len: int = 2048
    vocab_size: int = 32000

    # MoE config
    n_experts: int = 8
    top_k_experts: int = 2
    expert_capacity: float = 1.25

    # Brain config
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
    # These are tuned for consumer hardware (8-32 GB RAM, optional GPU)
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
