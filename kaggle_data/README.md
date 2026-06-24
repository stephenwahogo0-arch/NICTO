# NICTO Kaggle / Colab Training Data

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
