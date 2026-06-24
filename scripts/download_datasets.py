"""Download training datasets from HuggingFace and Kaggle for NICTO neural training."""

import os
import json
import sys

DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")
os.makedirs(DATASETS_DIR, exist_ok=True)


def download_hf_datasets():
    """Download HuggingFace datasets for specialist network training."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("datasets package not installed. Run: pip install datasets")
        return

    datasets_to_download = {
        "tatsu-lab/alpaca": "instruction_following",
        "wikitext": "language_modeling",
        "c4": "web_text",
        "cnn_dailymail": "summarization",
        "squad": "qa",
    }

    for ds_name, category in datasets_to_download.items():
        out_dir = os.path.join(DATASETS_DIR, category, ds_name.replace("/", "_"))
        if os.path.exists(out_dir):
            print(f"  {ds_name} already downloaded, skipping")
            continue

        print(f"Downloading {ds_name} ({category})...")
        try:
            ds = load_dataset(ds_name, split="train", streaming=True)
            os.makedirs(out_dir, exist_ok=True)
            count = 0
            for i, example in enumerate(ds):
                file_path = os.path.join(out_dir, f"sample_{i}.json")
                with open(file_path, "w") as f:
                    json.dump(example, f)
                count += 1
                if count >= 100:
                    break
            print(f"  Saved {count} samples to {out_dir}")
        except Exception as e:
            print(f"  Error: {e}")


def main():
    print("=== NICTO Dataset Downloader ===")
    print(f"Datasets directory: {DATASETS_DIR}")
    print()

    print("[1/3] HuggingFace datasets...")
    download_hf_datasets()
    print()

    print("Done! Datasets saved to", DATASETS_DIR)


if __name__ == "__main__":
    main()
