"""Write Kaggle dataset metadata files."""
import json
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "kaggle_data"

meta = {
    "title": "NICTO Super Training Data",
    "subtitle": "361K ChatML entries across 57 domains for fine-tuning NICTO AI models",
    "description": "Multi-domain training data with model-specific subsets (Kyros, Omega, Main, X)",
    "total_entries": 361800,
    "domains": 57,
    "subsets": ["kyros", "omega", "main", "x", "universal"],
    "format": "ChatML JSONL",
    "version": "2.0",
}
with open(OUT_DIR / "dataset_metadata.json", "w") as f:
    json.dump(meta, f, indent=2)

readme = """# NICTO Kaggle / Colab Training Data

## Structure
- `universal_chatml.jsonl` — Full 365K entries (all domains, enhanced)
- `kyros_chatml.jsonl` — 55K entries (simple Q&A, minimal reasoning)
- `omega_chatml.jsonl` — 150K entries (reasoning, ethics, general knowledge)
- `main_chatml.jsonl` — 119K entries (reasoning + security + coding)
- `x_chatml.jsonl` — 125K entries (agent, coding, research, planning)

## Enhanced Data
- 2,000 chain-of-thought reasoning examples
- 500 multi-turn conversations
- 1,000 code generation examples with tests

## Format
Each line: `{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`

## Usage
```python
from datasets import Dataset
import json
with open("universal_chatml.jsonl") as f:
    data = [json.loads(line) for line in f if line.strip()]
dataset = Dataset.from_list(data)
```
"""
with open(OUT_DIR / "README.md", "w") as f:
    f.write(readme)

print("Metadata written")
