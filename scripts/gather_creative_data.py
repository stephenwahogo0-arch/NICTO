"""Gather creative content data from YouTube, HuggingFace datasets, and web sources.

Feeds NICTO's creative brain with camera angles, lighting, genre conventions,
and cinematography techniques from real-world video content.

Sources:
  - HuggingFace: video captioning datasets, cinematography datasets
  - YouTube API (optional): video titles, descriptions, tags about techniques
  - Built-in: structured cinematography knowledge base
"""

import json
import os
import sys
import random

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "nicto_neural", "data")
os.makedirs(DATA_DIR, exist_ok=True)


def gather_huggingface_datasets():
    """Download video/caption datasets from HuggingFace for creative training."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("  datasets not installed. Run: pip install datasets")
        return []

    datasets_config = [
        ("HuggingFaceM4/COCO", "train", "image_captioning", 500),
        ("biglam/illustration_captions", "train", "illustration_captions", 200),
    ]

    all_samples = []
    for ds_name, split, category, limit in datasets_config:
        out_path = os.path.join(DATA_DIR, f"hf_{ds_name.replace('/', '_')}.jsonl")
        if os.path.exists(out_path):
            print(f"  {ds_name} already downloaded")
            with open(out_path) as f:
                all_samples.extend([json.loads(l) for l in f if l.strip()])
            continue

        print(f"  Downloading {ds_name} ({category})...")
        try:
            ds = load_dataset(ds_name, split=split, streaming=True)
            samples = []
            for i, ex in enumerate(ds):
                if i >= limit:
                    break
                caption = ex.get("caption", ex.get("comment", str(ex)))
                samples.append({
                    "source": ds_name,
                    "category": category,
                    "caption": caption if isinstance(caption, str) else str(caption),
                })
            with open(out_path, "w") as f:
                for s in samples:
                    f.write(json.dumps(s) + "\n")
            all_samples.extend(samples)
            print(f"    Saved {len(samples)} samples")
        except Exception as e:
            print(f"    Error: {e}")

    return all_samples


def gather_cinematography_samples():
    """Generate training samples from cinematography knowledge base."""
    sys.path.insert(0, PROJECT_ROOT)
    from nicto_neural.data.cinematography_knowledge import (
        CAMERA_ANGLES, LIGHTING_TECHNIQUES, GENRE_CONVENTIONS,
        COMPOSITION_RULES, COLOR_GRADING_STYLES,
    )

    samples = []

    for name, info in CAMERA_ANGLES.items():
        samples.append({
            "source": "cinematography_kb",
            "category": "camera_angle",
            "name": name,
            "description": info["description"],
            "effect": info["effect"],
            "best_for": info["best_for"],
            "lens": info.get("lens", "variable"),
            "movement": info.get("movement", "static"),
        })

    for name, info in LIGHTING_TECHNIQUES.items():
        samples.append({
            "source": "cinematography_kb",
            "category": "lighting",
            "name": name,
            "description": info["description"],
            "effect": info["effect"],
            "setup": info["setup"],
            "best_for": info["best_for"],
            "hardness": info["hardness"],
        })

    for name, info in GENRE_CONVENTIONS.items():
        samples.append({
            "source": "cinematography_kb",
            "category": "genre",
            "name": name,
            "camera_angles": info["camera_angles"],
            "lighting": info["lighting"],
            "color_palette": info["color_palette"],
            "lens_choices": info["lens_choices"],
            "camera_movement": info["camera_movement"],
            "editing_pace": info["editing_pace"],
            "sound_design": info["sound_design"],
            "composition": info["composition"],
        })

    for name, info in COMPOSITION_RULES.items():
        samples.append({
            "source": "cinematography_kb",
            "category": "composition",
            "name": name,
            "description": info["description"],
            "effect": info["effect"],
            "use_when": info["use_when"],
        })

    for name, info in COLOR_GRADING_STYLES.items():
        samples.append({
            "source": "cinematography_kb",
            "category": "color_grading",
            "name": name,
            "description": info["description"],
            "effect": info["effect"],
            "best_for": info["best_for"],
        })

    return samples


def generate_training_pairs(kb_samples, hf_samples):
    """Generate ChatML-style training pairs for creative brain."""
    pairs = []

    for s in kb_samples:
        cat = s["category"]
        if cat == "camera_angle":
            prompt = f"What is the {s['name']} camera angle and when should I use it?"
            response = (
                f"The {s['name']} angle positions the camera {s['description']} "
                f"It creates {s['effect']} "
                f"It's best for: {', '.join(s['best_for'])}. "
                f"Recommended lens: {s['lens']}."
            )
            pairs.append({"messages": [
                {"role": "system", "content": "You are NICTO Creative Brain, an expert cinematographer and visual artist."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response},
            ]})
        elif cat == "lighting":
            prompt = f"Explain {s['name']} lighting technique and how to set it up."
            response = (
                f"{s['description']} {s['effect']} "
                f"Setup: {s['setup']}. "
                f"Light hardness: {s['hardness']}. "
                f"Best for: {', '.join(s['best_for'])}."
            )
            pairs.append({"messages": [
                {"role": "system", "content": "You are NICTO Creative Brain, a cinematography lighting expert."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response},
            ]})
        elif cat == "genre":
            prompt = f"What are the cinematography conventions for {s['name']}?"
            response = (
                f"For {s['name']}, use {', '.join(s['camera_angles'])} camera angles, "
                f"{', '.join(s['lighting'])} lighting, "
                f"and a {s['editing_pace']} editing pace. "
                f"Color palette: {', '.join(s['color_palette']) if isinstance(s['color_palette'], list) else s['color_palette']}. "
                f"Lens choices: {', '.join(s['lens_choices']) if isinstance(s['lens_choices'], list) else s['lens_choices']}. "
                f"Composition tips: {s['composition']}."
            )
            pairs.append({"messages": [
                {"role": "system", "content": "You are NICTO Creative Brain, a genre-specialist cinematographer."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response},
            ]})

    return pairs


def main():
    print("=== NICTO Creative Data Gatherer ===\n")

    print("[1/3] Gathering cinematography knowledge base...")
    kb_samples = gather_cinematography_samples()
    kb_path = os.path.join(DATA_DIR, "cinematography_kb.jsonl")
    with open(kb_path, "w") as f:
        for s in kb_samples:
            f.write(json.dumps(s) + "\n")
    print(f"  {len(kb_samples)} samples saved to {kb_path}\n")

    print("[2/3] Downloading HuggingFace datasets...")
    hf_samples = gather_huggingface_datasets()
    print(f"  {len(hf_samples)} total HF samples\n")

    print("[3/3] Generating training pairs...")
    pairs = generate_training_pairs(kb_samples, hf_samples)
    random.shuffle(pairs)
    pairs_path = os.path.join(DATA_DIR, "creative_training_pairs.jsonl")
    with open(pairs_path, "w") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")
    print(f"  {len(pairs)} training pairs saved to {pairs_path}")

    print(f"\nDone! Total samples: {len(kb_samples) + len(hf_samples)}, training pairs: {len(pairs)}")


if __name__ == "__main__":
    main()
