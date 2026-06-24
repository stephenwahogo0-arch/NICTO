"""Corpus generator — generates all AKNOW training data for NICTO.

Output (in aknow_corpus/):
  aknow_meta.jsonl       — 30,000 meta-corpus samples
  aknow_domains.jsonl    — 160,000 domain samples (16 domains x 10k)
  aknow_cross.jsonl      — 5,000 cross-domain synthesis samples
  aknow_full.jsonl       — 195,000 total samples (merged)
  train.jsonl            — 80% split
  val.jsonl              — 10% split
  test.jsonl             — 10% split
"""

import json
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from aknow_nicto_bridge import AknowNictoBridge
except ImportError:
    AknowNictoBridge = None


def main():
    if AknowNictoBridge is None:
        print("ERROR: aknow_nicto_bridge module not found. Install it first.")
        return

    bridge = AknowNictoBridge()
    corpus_dir = os.path.dirname(os.path.abspath(__file__))
    domains = bridge.get_all_domains()
    domain_names = sorted(domains.keys())
    print(f"Domains available: {len(domain_names)}")
    print(f"  {', '.join(domain_names)}")
    print()

    start = time.time()

    # Phase 1: Domain corpus — 10k samples per domain
    print("Phase 1: Domain corpus (160k samples)...")
    all_domain_samples = []
    for domain in domain_names:
        print(f"  Generating {domain}...", end=" ", flush=True)
        t0 = time.time()
        samples = bridge.generate_corpus(domain, count=10000, length=200)
        bridge.save_corpus(samples, os.path.join(corpus_dir, f"domain_{domain}.jsonl"))
        all_domain_samples.extend(samples)
        dur = time.time() - t0
        print(f"{len(samples)} samples in {dur:.1f}s ({dur/100:.2f}s per 1k)")

    domain_path = os.path.join(corpus_dir, "aknow_domains.jsonl")
    bridge.save_corpus(all_domain_samples, domain_path)
    print(f"  Total domain samples: {len(all_domain_samples)}")
    print()

    # Phase 2: Meta corpus — 30k samples
    print("Phase 2: Meta corpus (30k samples)...")
    t0 = time.time()
    meta_samples = bridge.generate_meta_corpus(count=30000, length=100)
    meta_path = os.path.join(corpus_dir, "aknow_meta.jsonl")
    bridge.save_corpus(meta_samples, meta_path)
    dur = time.time() - t0
    print(f"  {len(meta_samples)} samples in {dur:.1f}s")
    print()

    # Phase 3: Cross-domain corpus
    cross_count = min(5000, len(all_domain_samples) * 3)
    print(f"Phase 3: Cross-domain corpus ({cross_count} samples)...")
    t0 = time.time()
    cross_samples = []
    for i in range(cross_count):
        d1 = domain_names[i % len(domain_names)]
        d2 = domain_names[(i * 7 + 3) % len(domain_names)]
        s1 = bridge.generate_corpus(d1, count=1, length=100)
        s2 = bridge.generate_corpus(d2, count=1, length=100)
        if s1 and s2:
            cross_samples.append({
                "domain_a": d1, "domain_b": d2,
                "source_a": s1[0], "source_b": s2[0],
                "synthesis": f"Synthesizing {d1} with {d2}: {s1[0][:50]} + {s2[0][:50]}",
            })
    cross_path = os.path.join(corpus_dir, "aknow_cross.jsonl")
    bridge.save_corpus(cross_samples, cross_path)
    dur = time.time() - t0
    print(f"  {len(cross_samples)} samples in {dur:.1f}s")
    print()

    # Phase 4: Full merge
    full = all_domain_samples + meta_samples + [c["synthesis"] for c in cross_samples]
    full_path = os.path.join(corpus_dir, "aknow_full.jsonl")
    bridge.save_corpus(full, full_path)
    print(f"Phase 4: Full corpus — {len(full)} samples")
    print()

    # Phase 5: Train/val/test split (80/10/10)
    import random
    random.shuffle(full)
    n = len(full)
    n_train = int(n * 0.8)
    n_val = int(n * 0.1)
    train_set = full[:n_train]
    val_set = full[n_train:n_train + n_val]
    test_set = full[n_train + n_val:]

    bridge.save_corpus(train_set, os.path.join(corpus_dir, "train.jsonl"))
    bridge.save_corpus(val_set, os.path.join(corpus_dir, "val.jsonl"))
    bridge.save_corpus(test_set, os.path.join(corpus_dir, "test.jsonl"))

    print(f"Phase 6: Train/val/test — {len(train_set)}/{len(val_set)}/{len(test_set)}")
    print(f"Total time: {time.time() - start:.1f}s")
    print("Done!")


if __name__ == "__main__":
    main()
