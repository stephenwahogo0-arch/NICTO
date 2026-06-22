# Training Infrastructure

Training pipeline for NICTO AI models. Designed for Google Colab and Kaggle GPU runtimes.

## Training Pipeline

```
Data Preparation → Tokenization → LoRA Training → GGUF Export → Integration
```

## Components

| Component | Description | File |
|-----------|-------------|------|
| Colab Trainer | Full pipeline for Google Colab | `scripts/colab_train_all.py` |
| Unsloth Trainer | LoRA fine-tuning on GPU | `nicto_neural/train_nicto.py` |
| Data Builder | ChatML training data generation | `nicto_neural/build_training_data.py` |
| Super Data v3 | 361K multi-domain dataset builder | `nicto_neural/build_super_data_v3.py` |
| Hardware Setup | Auto-detects GPU, selects best model | `nicto_neural/setup_real_ai.py` |

## Supported Base Models

| Model | Params | VRAM | Colab Compatible | Quality |
|-------|--------|------|------------------|---------|
| Phi-3-mini-4k | 3.8B | 6GB | ✅ (T4) | Good |
| Llama-3.2-3B | 3B | 5GB | ✅ (T4) | Good |
| Qwen2.5-7B | 7B | 10GB | ✅ (T4 4-bit) | Best |
| Mistral-7B | 7B | 10GB | ✅ (T4 4-bit) | Excellent |

## Training Strategies

1. **Universal** — One model trained on all 361K entries for general purpose
2. **Specialized** — 4 separate LoRA adapters (Kyros/Omega/Main/X) for pipeline-specific behavior
3. **Combined** — Universal base + specialized LoRA adapters switched per pipeline

## Output Format

- LoRA adapters (small, ~50MB)
- Merged 16-bit model (full weights)
- GGUF quantized (q4_k_m, ~2-4GB)
