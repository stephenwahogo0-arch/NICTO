# Notebooks

Jupyter notebooks for NICTO development, training, and experimentation.

## Available Notebooks

| Notebook | Purpose | Platform |
|----------|---------|----------|
| `colab_nicto_training.ipynb` | Full training pipeline (4 base models × 5 adapters) | Google Colab |

## Usage

### Google Colab

1. Go to https://colab.research.google.com
2. File → Open notebook → GitHub → `stephenwahogo0-arch/NICTO`
3. Select `colab_nicto_training.ipynb`
4. Runtime → Change runtime type → GPU (T4/V100/A100)
5. Run all cells

### Local

```bash
jupyter notebook notebooks/
```
