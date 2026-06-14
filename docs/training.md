# NICTO Training Guide

## Training Pipeline Overview

```
Data Preparation → Base Model Selection → LoRA Fine-Tuning → GGUF Export → Integration
```

## Step 1: Data Preparation

```bash
# Generate Kaggle/Colab training subsets
python scripts/kaggle_prepare_data.py
```

Outputs 5 JSONL files in `kaggle_data/`:
- `universal_chatml.jsonl` — 365K entries
- `kyros_chatml.jsonl` — 55K entries
- `omega_chatml.jsonl` — 150K entries
- `main_chatml.jsonl` — 119K entries
- `x_chatml.jsonl` — 125K entries

## Step 2: Choose Base Model

| Model | Params | Colab T4 | Quality |
|-------|--------|----------|---------|
| Phi-3-mini-4k | 3.8B | ✅ | Good |
| Llama-3.2-3B | 3B | ✅ | Good |
| **Qwen2.5-7B** (recommended) | 7B | ✅ (4-bit) | Best |
| Mistral-7B-v0.3 | 7B | ✅ (4-bit) | Excellent |

## Step 3: Train on Colab

1. Upload `colab_nicto_training.ipynb` to Google Colab
2. Select GPU runtime (T4/V100/A100)
3. The notebook will:
   - Install Unsloth + dependencies
   - Download training data
   - Train all 4 base models × 5 adapters = 20 trainings
   - Export GGUF files to Google Drive

**Estimated time**: ~20 hours for all 20 trainings on T4

## Step 4: Integrate Trained Weights

```bash
# Register a trained GGUF model
python scripts/integrate_gguf.py

# Or programmatically:
from scripts.integrate_gguf import integrate_gguf
core = integrate_gguf(
    model_name="nicto_universal",
    gguf_path="/path/to/model.gguf",
    pipeline="universal",
    model_type="qwen25",
    params="7B"
)
```

## Step 5: Benchmark

```bash
# Run multi-model verification
python scripts/train_and_verify_all_models.py
```

## Training Configurations

| Parameter | Universal | Kyros | Omega | Main | X |
|-----------|-----------|-------|-------|------|---|
| Dataset size | 365K | 55K | 150K | 119K | 125K |
| Epochs | 1 | 1 | 1 | 1 | 1 |
| Learning rate | 2e-4 | 2e-4 | 2e-4 | 2e-4 | 2e-4 |
| LoRA rank | 16 | 16 | 16 | 16 | 16 |
| Batch size | 2-4 | 4 | 4 | 4 | 4 |
| Est. time (T4) | 3h | 1h | 1.5h | 1.5h | 1.5h |
