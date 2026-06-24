"""Train the creative brain subnetworks with cinematography + social media data.

Usage:
  python scripts/train_creative_brain.py [--epochs 10] [--lr 1e-4]
"""

import os
import sys
import argparse
import torch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ["NIKTO_ENABLE_EXPERIMENTAL"] = "1"
import warnings
warnings.filterwarnings("ignore")

from nicto_neural.neural.config import NeuralConfig
from nicto_neural.brain.creative import CreativeBrain
from nicto_neural.learning.creative_trainer import CreativeTrainer, CreativeDataLoader


def main():
    parser = argparse.ArgumentParser(description="Train creative brain with cinematography data")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--steps-per-epoch", type=int, default=100)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--data-dir", default=os.path.join(PROJECT_ROOT, "nicto_neural", "data"))
    parser.add_argument("--save", default=os.path.join(PROJECT_ROOT, "nicto_neural", "checkpoints", "creative_brain.pt"))
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"=== Creative Brain Training ===")
    print(f"Device: {device}")
    print(f"Epochs: {args.epochs}")
    print(f"Data: {args.data_dir}")
    print()

    config = NeuralConfig(d_model=128, n_heads=4, n_layers=2)
    creative_brain = CreativeBrain(config)
    print(f"Creative Brain: {creative_brain}")
    n_params = sum(p.numel() for p in creative_brain.parameters())
    print(f"Parameters: {n_params:,}")
    print()

    loader = CreativeDataLoader(args.data_dir)
    trainer = CreativeTrainer(creative_brain, loader, device=device)

    result = trainer.train(
        epochs=args.epochs,
        steps_per_epoch=args.steps_per_epoch,
        lr=args.lr,
        lr_decay=0.95,
    )

    os.makedirs(os.path.dirname(args.save) if os.path.dirname(args.save) else ".", exist_ok=True)
    trainer.save(args.save)

    print(f"\nTraining complete!")
    print(f"Final loss: {result['final_loss']:.4f}")
    print(f"Model saved to: {args.save}")
    print(f"To generate with: python -c \"from nicto_neural.brain.creative import CreativeBrain; from nicto_neural.neural.config import NeuralConfig; import torch; b = CreativeBrain(NeuralConfig(d_model=128)); b.load_state_dict(torch.load('{args.save}')['brain_state']); print('Creative brain loaded')\"")


if __name__ == "__main__":
    main()
