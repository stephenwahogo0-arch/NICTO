# Evaluation & Benchmarking

Automated evaluation framework for measuring NICTO model performance.

## Benchmarks

| Benchmark | Domain | Metrics |
|-----------|--------|---------|
| Reasoning | Logic, math, analysis | Accuracy, latency, coherence |
| Coding | Python, Rust, TypeScript | Compilation rate, correctness |
| Memory | Recall, consolidation | Precision, recall, latency |
| Knowledge | 57 domains | Factual accuracy, coverage |
| Security | Vulnerability detection | Precision, recall, risk score |
| Tool Usage | Search, calculator, code exec | Success rate, latency |

## Verification Suites

| Suite | Tests | Run Command |
|-------|-------|-------------|
| NICTO X Full Suite | 66 | `python packages/nicto-x/tests/test_all.py` |
| Game Engine Suite | 18 | `python scripts/verify_game_engine.py` |
| Multi-Model | 28 (7 prompts × 4 models) | `python scripts/train_and_verify_all_models.py` |

## Current Results

| Model | Latency | Response Quality | Success Rate |
|-------|---------|-----------------|:-------:|
| Kyros | 0.62ms | Minimal, direct | 100% |
| Omega | 2.93ms | Balanced reasoning | 100% |
| Main | 3.02ms | Full cognitive + security | 100% |
| X | 2.36s | Multi-agent frontier | 100% |
