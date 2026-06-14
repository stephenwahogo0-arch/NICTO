# Datasets

Training and evaluation datasets for NICTO AI models.

## Available Datasets

| Dataset | Format | Entries | Domains | Location |
|---------|--------|---------|---------|----------|
| NICTO Super v3 | ChatML JSONL | 361,800 | 57 | `kaggle_data/universal_chatml.jsonl` |
| NICTO Kyros | ChatML JSONL | 55,000 | 20 | `kaggle_data/kyros_chatml.jsonl` |
| NICTO Omega | ChatML JSONL | 150,000 | 40 | `kaggle_data/omega_chatml.jsonl` |
| NICTO Main | ChatML JSONL | 119,303 | 50 | `kaggle_data/main_chatml.jsonl` |
| NICTO X | ChatML JSONL | 125,118 | 55 | `kaggle_data/x_chatml.jsonl` |

## Dataset Pipeline

1. **Ingestion** — Raw data loaded from JSONL files
2. **Validation** — Schema checks, required fields verification
3. **Cleaning** — Deduplication, normalization, filtering
4. **Versioning** — Metadata tracking for reproducibility
5. **Statistics** — Domain distribution, length analysis, difficulty scoring

## Categories

- Reasoning (mathematics, logic, physics)
- Mathematics (algebra, calculus, statistics)
- Science (biology, chemistry, earth science)
- Coding (Python, Rust, TypeScript, algorithms)
- General Knowledge (history, geography, culture)
- Research (literature review, hypothesis generation)
- Documentation (code docs, technical writing)

## Tools

- `scripts/kaggle_prepare_data.py` — Dataset splitting and enhancement
- `nicto_neural/build_super_data_v3.py` — Synthetic data generation
- `nicto_neural/build_training_data.py` — ChatML conversation builder
