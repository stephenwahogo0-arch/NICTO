"""Run SUPERIOR recursive creative learning — NICTO teaches itself to surpass any AI at creativity.

NICTO uses the YouTube API key to autonomously fetch cinematography data at scale,
self-generates training pairs via 90+ creative prompts, evaluates on 12 quality axes,
retrains with curriculum-weighted sampling, and repeats — quality compounds each cycle.

Usage:
  python scripts/run_recursive_creative_learning.py --api-key "YOUR_KEY" --cycles 10 --steps 500
  python scripts/run_recursive_creative_learning.py  # reads YOUTUBE_API_KEY env var
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

from nicto_neural.brain.superior_creative import SuperiorCreativeBrain, count_parameters
from nicto_neural.learning.superior_creative_learner import SuperiorRecursiveCreativeLearner


def main():
    parser = argparse.ArgumentParser(description="Superior Recursive Creative Learning — surpass any AI at creativity")
    parser.add_argument("--api-key", help="YouTube Data API key (or set YOUTUBE_API_KEY env var)")
    parser.add_argument("--cycles", type=int, default=5, help="Number of recursive cycles")
    parser.add_argument("--steps", type=int, default=300, help="Training steps per cycle")
    parser.add_argument("--queries", type=int, default=5, help="YouTube queries per cycle")
    parser.add_argument("--d-model", type=int, default=512, help="Model dimension")
    parser.add_argument("--n-heads", type=int, default=8, help="Number of attention heads")
    parser.add_argument("--n-layers", type=int, default=4, help="Number of transformer layers")
    parser.add_argument("--data-dir", default=os.path.join(PROJECT_ROOT, "nicto_neural", "data"))
    parser.add_argument("--save", default=os.path.join(PROJECT_ROOT, "nicto_neural", "checkpoints", "superior_creative_brain.pt"))
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("YOUTUBE_API_KEY", "")
    if not api_key:
        print("WARNING: No YouTube API key. NICTO won't be able to autonomously fetch data.")
        print("  Pass --api-key or set YOUTUBE_API_KEY environment variable.")
        print()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"{'='*60}")
    print(f" NICTO Superior Recursive Creative Learning Engine")
    print(f"{'='*60}")
    print(f"Device: {device}")
    print(f"Cycles: {args.cycles}  |  Steps/cycle: {args.steps}")
    print(f"YouTube: {'AUTONOMOUS' if api_key else 'DISABLED'}")
    print(f"Data dir: {args.data_dir}")
    print(f"Output: {args.save}")
    print()

    brain = SuperiorCreativeBrain(
        d_model=args.d_model,
        n_heads=args.n_heads,
        n_layers=args.n_layers,
    )
    n_params = count_parameters(brain)
    print(f"SuperiorCreativeBrain: {n_params:,} parameters ({n_params/1e6:.1f}M)")
    print()

    if os.path.exists(args.save):
        try:
            state = torch.load(args.save, map_location=device)
            brain.load_state_dict(state["brain_state"], strict=False)
            print(f"Restored brain from {args.save}")
        except Exception as e:
            print(f"Could not restore: {e}")
    else:
        os.makedirs(os.path.dirname(args.save) if os.path.dirname(args.save) else ".", exist_ok=True)

    learner = SuperiorRecursiveCreativeLearner(
        creative_brain=brain,
        data_dir=args.data_dir,
        youtube_api_key=api_key,
        device=device,
        d_model=args.d_model,
    )

    results = learner.run(
        num_cycles=args.cycles,
        steps_per_cycle=args.steps,
        queries_per_cycle=args.queries,
    )

    learner.save_brain(args.save)

    print(f"\n{'='*60}")
    print(f" SUPERIOR RECURSIVE LEARNING COMPLETE")
    print(f"{'='*60}")
    print(f"Brain saved to: {args.save}")
    print(f"Cycles completed: {len(results)}")
    print(f"Final loss: {results[-1]['loss']:.4f}" if results else "N/A")
    print(f"Final confidence: {results[-1]['confidence']:.3f}" if results else "N/A")
    print(f"Final quality: {results[-1]['quality']:.3f}" if results else "N/A")
    print(f"Final samples: {learner.history['total_samples']}")
    print(f"YouTube fetched: {learner.history['youtube_fetched']}")
    print(f"Self-play generated: {learner.history['selfplay_generated']}")


if __name__ == "__main__":
    main()
