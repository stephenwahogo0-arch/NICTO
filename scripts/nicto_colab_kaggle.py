"""NICTO — Automated Colab/Kaggle Training Pipeline.

Run this in a Colab or Kaggle notebook to:
1. Detect and configure CUDA environment
2. Clone the NICTO repository
3. Install dependencies
4. Download and prepare training data
5. Run the 7-brain MoE+MLA training loop
6. Export trained weights and shard for multi-GPU
7. Save checkpoints to Google Drive or Kaggle datasets

Usage (Colab):
  !python scripts/nicto_colab_kaggle.py --mode colab --epochs 3 --batch_size 4

Usage (Kaggle):
  !python scripts/nicto_colab_kaggle.py --mode kaggle --epochs 5 --batch_size 8
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Optional


REPO_URL = "https://github.com/stephenwahogo0-arch/NICTO.git"
REPO_DIR = "NICTO"
REQUIRED_PACKAGES = [
    "torch>=2.1.0",
    "torchvision",
    "transformers>=4.36.0",
    "datasets",
    "accelerate",
    "sentencepiece",
    "wandb",
    "tqdm",
    "numpy",
    "psutil",
]
COLAB_DRIVE_PATH = "/content/drive/MyDrive/nicto_checkpoints"
KAGGLE_OUTPUT_PATH = "/kaggle/working/nicto_checkpoints"


def log(msg: str) -> None:
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def run_cmd(cmd: str, capture: bool = False) -> subprocess.CompletedProcess:
    log(f"Running: {cmd[:120]}...")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture, text=True, timeout=7200
        )
        if result.returncode != 0:
            log(f"Command failed (code {result.returncode}): {result.stderr[:500]}")
        return result
    except subprocess.TimeoutExpired:
        log(f"Command timed out: {cmd[:80]}")
        raise


def detect_hardware() -> dict[str, Any]:
    hw = {
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "cuda_available": False,
        "cuda_version": None,
        "gpu_count": 0,
        "gpu_names": [],
        "total_vram_gb": 0,
        "ram_gb": 0,
        "is_colab": "COLAB_GPU" in os.environ or "COLAB_TPU_ADDR" in os.environ,
        "is_kaggle": "KAGGLE_KERNEL_RUN_TYPE" in os.environ,
    }

    try:
        import psutil
        hw["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
    except ImportError:
        pass

    try:
        import torch
        hw["cuda_available"] = torch.cuda.is_available()
        if hw["cuda_available"]:
            hw["cuda_version"] = torch.version.cuda
            hw["gpu_count"] = torch.cuda.device_count()
            hw["gpu_names"] = [torch.cuda.get_device_name(i) for i in range(hw["gpu_count"])]
            total_vram = 0
            for i in range(hw["gpu_count"]):
                total_vram += torch.cuda.get_device_properties(i).total_memory
            hw["total_vram_gb"] = round(total_vram / (1024**3), 1)
    except ImportError:
        pass

    return hw


def install_dependencies(hw: dict[str, Any]) -> None:
    log("Installing Python dependencies...")
    for pkg in REQUIRED_PACKAGES:
        run_cmd(f"{sys.executable} -m pip install -q {pkg}")

    if hw["cuda_available"]:
        log("CUDA detected — ensuring torch CUDA compatibility")
        run_cmd(f"{sys.executable} -m pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cu121")

    log("Dependencies installed")


def clone_repository() -> str:
    repo_path = os.path.join(os.getcwd(), REPO_DIR)
    if os.path.exists(repo_path):
        log(f"Repository exists at {repo_path}, pulling latest...")
        run_cmd(f"cd {repo_path} && git pull")
    else:
        log(f"Cloning repository from {REPO_URL}...")
        run_cmd(f"git clone {REPO_URL} {REPO_DIR}")
    return repo_path


def prepare_checkpoint_dir(hw: dict[str, Any]) -> str:
    if hw["is_colab"]:
        ckpt_dir = COLAB_DRIVE_PATH
        os.makedirs(ckpt_dir, exist_ok=True)
        log(f"Checkpoints will be saved to Google Drive: {ckpt_dir}")
    elif hw["is_kaggle"]:
        ckpt_dir = KAGGLE_OUTPUT_PATH
        os.makedirs(ckpt_dir, exist_ok=True)
        log(f"Checkpoints will be saved to Kaggle working: {ckpt_dir}")
    else:
        ckpt_dir = os.path.join(os.getcwd(), "checkpoints")
        os.makedirs(ckpt_dir, exist_ok=True)
        log(f"Checkpoints will be saved locally: {ckpt_dir}")
    return ckpt_dir


def build_training_data(repo_path: str) -> str:
    log("Building training dataset...")
    data_script = os.path.join(repo_path, "nicto_neural", "build_training_data.py")
    if os.path.exists(data_script):
        run_cmd(f"{sys.executable} {data_script} --output training_data --n_samples 1000")
    else:
        log("build_training_data.py not found, generating synthetic data...")
        data_dir = os.path.join(repo_path, "training_data")
        os.makedirs(data_dir, exist_ok=True)
        _generate_synthetic_data(data_dir)
    return os.path.join(repo_path, "training_data")


def _generate_synthetic_data(data_dir: str) -> None:
    import random
    log("Generating 500 synthetic ChatML training pairs...")
    categories = [
        "identity", "cybersecurity", "programming", "creative",
        "analysis", "planning", "memory", "reasoning",
    ]
    templates = [
        ("What is {topic}?", "{topic} is a fundamental concept in {domain}. It involves {detail}."),
        ("Explain how {topic} works", "{topic} operates through {mechanism}, which enables {outcome}."),
        ("What are the key aspects of {topic}?", "The key aspects of {topic} include {aspect1}, {aspect2}, and {aspect3}."),
    ]
    domains = {
        "identity": {"topic": "NICTO", "domain": "AI systems", "detail": "autonomous cognitive architecture", "mechanism": "7-brain MoE+MLA", "outcome": "creative reasoning", "aspect1": "consciousness", "aspect2": "memory", "aspect3": "learning"},
        "cybersecurity": {"topic": "XSS prevention", "domain": "web security", "detail": "input sanitization and CSP headers", "mechanism": "context-aware escaping", "outcome": "safe rendering", "aspect1": "input validation", "aspect2": "output encoding", "aspect3": "CSP"},
        "programming": {"topic": "recursion", "domain": "computer science", "detail": "functions calling themselves", "mechanism": "stack-based execution", "outcome": "elegant problem solving", "aspect1": "base case", "aspect2": "recursive case", "aspect3": "stack depth"},
        "creative": {"topic": "visual storytelling", "domain": "cinematography", "detail": "narrative through images", "mechanism": "composition and lighting", "outcome": "emotional impact", "aspect1": "camera angles", "aspect2": "color grading", "aspect3": "blocking"},
        "analysis": {"topic": "data patterns", "domain": "data science", "detail": "identifying trends in data", "mechanism": "statistical analysis", "outcome": "actionable insights", "aspect1": "correlation", "aspect2": "causation", "aspect3": "significance"},
        "planning": {"topic": "goal decomposition", "domain": "AI planning", "detail": "breaking goals into subgoals", "mechanism": "hierarchical task networks", "outcome": "efficient execution", "aspect1": "prioritization", "aspect2": "scheduling", "aspect3": "resource allocation"},
        "memory": {"topic": "episodic memory", "domain": "cognitive science", "detail": "remembering past events", "mechanism": "hippocampal indexing", "outcome": "experience-based learning", "aspect1": "encoding", "aspect2": "consolidation", "aspect3": "retrieval"},
        "reasoning": {"topic": "deductive logic", "domain": "philosophy", "detail": "necessary conclusions from premises", "mechanism": "syllogistic inference", "outcome": "valid arguments", "aspect1": "premises", "aspect2": "entailment", "aspect3": "soundness"},
    }

    pairs = []
    for i in range(500):
        cat = random.choice(categories)
        template = random.choice(templates)
        info = domains[cat]
        question = template[0].format(topic=info["topic"])
        answer = template[1].format(**info)
        pairs.append({"messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]})

    output_file = os.path.join(data_dir, "synthetic_chatml.json")
    with open(output_file, "w") as f:
        json.dump(pairs, f, indent=2)
    log(f"Generated {len(pairs)} synthetic training pairs to {output_file}")


def run_training(
    repo_path: str,
    data_dir: str,
    checkpoint_dir: str,
    hw: dict[str, Any],
    epochs: int,
    batch_size: int,
    use_wandb: bool,
) -> str:
    log(f"Starting 7-brain MoE+MLA training ({epochs} epochs, batch_size={batch_size})...")

    os.chdir(repo_path)
    sys.path.insert(0, repo_path)

    os.environ["NIKTO_ENABLE_EXPERIMENTAL"] = "1"
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"

    if hw["gpu_count"] > 1:
        os.environ["WORLD_SIZE"] = str(hw["gpu_count"])
        log(f"Multi-GPU training with {hw['gpu_count']} GPUs")

    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, Dataset
    from transformers import get_cosine_schedule_with_warmup

    class QADataset(Dataset):
        def __init__(self, data_dir: str, max_len: int = 64, vocab_size: int = 2048):
            self.samples = []
            self.max_len = max_len
            self.vocab_size = vocab_size
            data_file = os.path.join(data_dir, "synthetic_chatml.json")
            if os.path.exists(data_file):
                with open(data_file) as f:
                    data = json.load(f)
                for item in data:
                    text = ""
                    for msg in item.get("messages", []):
                        text += msg.get("content", "") + " "
                    if text.strip():
                        self.samples.append(text.strip())
            if not self.samples:
                self.samples = [
                    "NICTO uses 7-brain MoE+MLA architecture with 19 specialized heads.",
                    "The system learns recursively through self-play generation and evaluation.",
                    "Multi-Head Latent Attention compresses KV cache for efficient inference.",
                ] * 50

        def __len__(self) -> int:
            return len(self.samples)

        def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
            text = self.samples[idx]
            ids = [hash(c) % self.vocab_size for c in text[:self.max_len]]
            ids = ids + [0] * (self.max_len - len(ids))
            x = torch.tensor(ids[:-1], dtype=torch.long)
            y = torch.tensor(ids[1:], dtype=torch.long)
            return {"input_ids": x, "labels": y}

    from nicto_neural.neural.super_config import SuperConfig
    from nicto_neural.neural.super_core import SuperNeuralCore
    from nicto_neural.neural.heads import SuperHeadEnsemble, BRAIN_HEAD_NAMES

    device = "cuda" if torch.cuda.is_available() else "cpu"
    log(f"Training device: {device}")

    config = SuperConfig(
        d_model=256,
        n_heads=4,
        n_kv_heads=2,
        n_layers=4,
        d_ff=1024,
        n_experts=4,
        n_active_experts=2,
        n_brain_heads=19,
        max_seq_len=64,
        vocab_size=2048,
        use_enhanced_moe=True,
        use_mla=True,
        dropout=0.1,
    )

    core = SuperNeuralCore(config).to(device)
    heads = SuperHeadEnsemble(config).to(device)

    n_core = sum(p.numel() for p in core.parameters())
    n_heads = sum(p.numel() for p in heads.parameters())
    log(f"Core: {n_core:,} params | Heads: {n_heads:,} params | Total: {n_core + n_heads:,}")

    dataset = QADataset(data_dir)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)

    optimizer = optim.AdamW(
        list(core.parameters()) + list(heads.parameters()),
        lr=3e-4,
        weight_decay=0.01,
        betas=(0.9, 0.95),
    )
    total_steps = len(loader) * epochs
    scheduler = get_cosine_schedule_with_warmup(
        optimizer, num_warmup_steps=total_steps // 10, num_training_steps=total_steps
    )
    criterion = nn.CrossEntropyLoss()

    if use_wandb:
        try:
            import wandb
            wandb.init(project="nicto-training", config={
                "epochs": epochs, "batch_size": batch_size, "d_model": 256,
                "n_layers": 4, "n_heads": 4, "n_experts": 4,
            })
        except ImportError:
            log("wandb not available — skipping logging")
            use_wandb = False

    log(f"Training: {len(dataset)} samples, {epochs} epochs, {total_steps} steps")
    core.train()
    heads.train()

    best_loss = float("inf")
    for epoch in range(epochs):
        epoch_loss = 0.0
        epoch_steps = 0
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()
            core_out = core(input_ids)
            hidden = core_out["hidden_states"]
            head_out = heads(hidden, active_heads=BRAIN_HEAD_NAMES)
            fused = head_out["fused"]

            loss = criterion(fused.view(-1, config.vocab_size), labels.view(-1))
            loss.backward()

            torch.nn.utils.clip_grad_norm_(
                list(core.parameters()) + list(heads.parameters()), max_norm=1.0
            )
            optimizer.step()
            scheduler.step()

            epoch_loss += loss.item()
            epoch_steps += 1

            if epoch_steps % 10 == 0:
                log(f"Epoch {epoch+1}/{epochs} Step {epoch_steps}/{len(loader)} Loss: {loss.item():.4f}")
                if use_wandb:
                    import wandb
                    wandb.log({"loss": loss.item(), "lr": scheduler.get_last_lr()[0]})

        avg_loss = epoch_loss / max(epoch_steps, 1)
        log(f"Epoch {epoch+1}/{epochs} complete. Avg loss: {avg_loss:.4f}")

        if avg_loss < best_loss:
            best_loss = avg_loss
            ckpt = {
                "epoch": epoch + 1,
                "core_state_dict": core.state_dict(),
                "heads_state_dict": heads.state_dict(),
                "optimizer": optimizer.state_dict(),
                "scheduler": scheduler.state_dict(),
                "loss": avg_loss,
                "config": config.__dict__,
            }
            ckpt_path = os.path.join(checkpoint_dir, f"nicto_7brain_epoch{epoch+1}.pt")
            torch.save(ckpt, ckpt_path)
            log(f"Checkpoint saved: {ckpt_path} ({os.path.getsize(ckpt_path) / 1024**2:.1f} MB)")

    log("Training complete!")
    return checkpoint_dir


def shard_checkpoints(checkpoint_dir: str, hw: dict[str, Any]) -> None:
    log("Sharding checkpoints for multi-GPU...")
    for fname in os.listdir(checkpoint_dir):
        if fname.endswith(".pt"):
            fpath = os.path.join(checkpoint_dir, fname)
            if os.path.getsize(fpath) > 500 * 1024 * 1024:
                log(f"Sharding {fname} ({os.path.getsize(fpath) / 1024**2:.0f} MB)...")
                shard_dir = fpath.replace(".pt", "_shards")
                os.makedirs(shard_dir, exist_ok=True)
                ckpt = torch.load(fpath, map_location="cpu")
                shard_size = len(ckpt) // hw["gpu_count"] if hw["gpu_count"] > 0 else 1
                for i in range(hw["gpu_count"] if hw["gpu_count"] > 0 else 1):
                    shard = {k: v for j, (k, v) in enumerate(ckpt.items()) if j % max(hw["gpu_count"], 1) == i}
                    torch.save(shard, os.path.join(shard_dir, f"shard_{i:02d}.pt"))
                log(f"Sharded into {max(hw['gpu_count'], 1)} shards in {shard_dir}")


def run_pipeline(
    mode: str = "auto",
    epochs: int = 3,
    batch_size: int = 4,
    use_wandb: bool = False,
    no_shard: bool = False,
) -> None:
    log(f"{'='*60}")
    log(f"  NICTO 7-Brain MoE+MLA Training Pipeline")
    log(f"  Mode: {mode} | Epochs: {epochs} | Batch: {batch_size}")
    log(f"{'='*60}")

    hw = detect_hardware()
    log(f"Hardware: {json.dumps(hw, indent=2, default=str)}")

    install_dependencies(hw)
    repo_path = clone_repository()
    ckpt_dir = prepare_checkpoint_dir(hw)
    data_dir = build_training_data(repo_path)

    ckpt_dir = run_training(repo_path, data_dir, ckpt_dir, hw, epochs, batch_size, use_wandb)

    if not no_shard and hw["gpu_count"] > 1:
        shard_checkpoints(ckpt_dir, hw)

    log(f"{'='*60}")
    log(f"  Pipeline Complete!")
    log(f"  Checkpoints: {ckpt_dir}")
    log(f"  Hardware: {hw['gpu_count']}x GPU ({hw['total_vram_gb']}GB VRAM)")
    log(f"{'='*60}")


def main() -> None:
    parser = argparse.ArgumentParser(description="NICTO Colab/Kaggle Training Pipeline")
    parser.add_argument("--mode", choices=["colab", "kaggle", "auto"], default="auto")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--wandb", action="store_true", help="Use Weights & Biases logging")
    parser.add_argument("--no-shard", action="store_true", help="Skip multi-GPU sharding")
    args = parser.parse_args()

    try:
        run_pipeline(
            mode=args.mode,
            epochs=args.epochs,
            batch_size=args.batch_size,
            use_wandb=args.wandb,
            no_shard=args.no_shard,
        )
    except Exception as exc:
        log(f"PIPELINE FAILED: {exc}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
