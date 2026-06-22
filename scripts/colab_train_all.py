"""
NICTO Colab Super-Training Pipeline
Train all 4 base models × both strategies (universal + 4 specialized adapters).
Run this in Google Colab with GPU runtime enabled.
"""
import json, os, sys, time, math, random, shutil
from pathlib import Path

# ─── Colab Setup ─────────────────────────────────────────────
COLAB = "google.colab" in sys.modules
if COLAB:
    from google.colab import drive, files
    drive.mount("/content/drive")
    OUTPUT_DIR = Path("/content/drive/MyDrive/nicto_training")
else:
    OUTPUT_DIR = Path(__file__).parent.parent / "colab_output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = OUTPUT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ─── Configuration ───────────────────────────────────────────
BASE_MODELS = {
    "phi3": {"id": "microsoft/Phi-3-mini-4k-instruct", "params": "3.8B", "max_seq": 4096},
    "llama32": {"id": "meta-llama/Llama-3.2-3B-Instruct", "params": "3B", "max_seq": 8192},
    "qwen25": {"id": "Qwen/Qwen2.5-7B-Instruct", "params": "7B", "max_seq": 32768},
    "mistral": {"id": "mistralai/Mistral-7B-Instruct-v0.3", "params": "7B", "max_seq": 32768},
}

SUBSETS = ["kyros", "omega", "main", "x", "universal"]
SUBSET_SIZES = {"kyros": 55000, "omega": 150000, "main": 119303, "x": 125118, "universal": 365300}

MODEL_SYSTEM_PROMPTS = {
    "kyros": "You are NICTO Kyros — a fast, minimal AI assistant. Give short, direct answers. No reasoning chains.",
    "omega": "You are NICTO Omega — a balanced reasoning engine. Think step-by-step, consider ethics, learn from context.",
    "main": "You are NICTO Main — a full-featured AI. Reason deeply, scan for security issues, analyze code for vulnerabilities.",
    "x": "You are NICTO X — a frontier agent orchestrator. Coordinate research, code generation, planning, evaluation.",
    "universal": "You are NICTO, an advanced AI with deep knowledge across all domains. Provide accurate, detailed responses.",
}

# ─── Step 1: Install Dependencies ────────────────────────────
def step1_install():
    """Install Unsloth and dependencies."""
    print("=" * 60)
    print("STEP 1: Installing Unsloth + dependencies")
    print("=" * 60)
    start = time.time()

    os.system("pip install -q unsloth unsloth_zoo transformers datasets trl accelerate tensorboard")
    os.system("pip install -q xformers --index-url https://download.pytorch.org/whl/cu121")

    import torch
    has_gpu = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if has_gpu else "NONE"
    print(f"  GPU: {gpu_name} | VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f}GB")
    print(f"  Time: {time.time()-start:.1f}s")
    return has_gpu


# ─── Step 2: Download Data ───────────────────────────────────
def step2_download_data():
    """Download training data from GitHub or local."""
    print("\n" + "=" * 60)
    print("STEP 2: Downloading training data")
    print("=" * 60)
    start = time.time()

    # Check if local (pre-uploaded) data exists
    local_paths = {s: DATA_DIR / f"{s}_chatml.jsonl" for s in SUBSETS}
    all_exist = all(p.exists() for p in local_paths.values())

    if not all_exist and COLAB:
        # Download from GitHub
        base_url = "https://raw.githubusercontent.com/stephenwahogo0-arch/NICTO/main/kaggle_data"
        for s in SUBSETS:
            url = f"{base_url}/{s}_chatml.jsonl"
            dest = local_paths[s]
            print(f"  Downloading {s}...")
            os.system(f"wget -q '{url}' -O '{dest}'")
            if dest.exists():
                size_mb = dest.stat().st_size / (1024 * 1024)
                print(f"    {size_mb:.0f}MB")
    elif all_exist:
        print("  All data files found locally")
    else:
        print("  WARNING: No data found. Upload manually to", DATA_DIR)
        return False

    for s in SUBSETS:
        p = local_paths[s]
        if p.exists():
            count = sum(1 for _ in open(p, encoding="utf-8") if _.strip())
            print(f"  {s}: {count} entries ({(p.stat().st_size/1024/1024):.0f}MB)")
    print(f"  Time: {time.time()-start:.1f}s")
    return True


# ─── Step 3: Load & Format Data ─────────────────────────────
def load_dataset(path: Path, max_samples: int = None):
    """Load JSONL file and return formatted dataset."""
    import json
    raw = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                raw.append(json.loads(line))
    if max_samples and len(raw) > max_samples:
        random.shuffle(raw)
        raw = raw[:max_samples]
    return raw


# ─── Step 4: Train One Adapter ────────────────────────────────
def train_adapter(base_model_id: str, model_name: str, adapter_name: str,
                  data_path: Path, output_dir: Path, max_seq: int = 4096):
    """Train a single LoRA adapter using Unsloth. Returns training stats."""
    print(f"\n{'─' * 60}")
    print(f"TRAINING: {model_name} → {adapter_name}")
    print(f"{'─' * 60}")
    start = time.time()

    from unsloth import FastLanguageModel, is_bfloat16_supported
    from unsloth.chat_templates import get_chat_template, train_on_responses_only
    from datasets import Dataset
    from transformers import TrainingArguments
    from trl import SFTTrainer
    import torch

    # Load base model in 4-bit
    print(f"  Loading {base_model_id} in 4-bit...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model_id,
        max_seq_length=max_seq,
        dtype=torch.bfloat16 if is_bfloat16_supported() else torch.float16,
        load_in_4bit=True,
    )

    # Set chat template
    tokenizer = get_chat_template(tokenizer, chat_template="chatml")

    # Apply LoRA
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
        use_rslora=True,
    )

    # Load data
    print(f"  Loading data from {data_path}...")
    with open(data_path, "r", encoding="utf-8") as f:
        raw_data = [json.loads(line) for line in f if line.strip()]

    # Apply system prompt for specialized adapters
    if adapter_name in MODEL_SYSTEM_PROMPTS:
        sys_prompt = MODEL_SYSTEM_PROMPTS[adapter_name]
        for entry in raw_data:
            if entry["messages"][0]["role"] == "system":
                entry["messages"][0]["content"] = sys_prompt

    dataset = Dataset.from_list(raw_data)
    print(f"  Dataset: {len(dataset)} examples")

    # Training args — scale batch size based on available VRAM
    import torch
    vram_gb = torch.cuda.get_device_properties(0).total_mem / 1e9
    per_device = 4 if vram_gb > 20 else 2
    grad_acc = 4 if vram_gb > 20 else 8

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=per_device,
            gradient_accumulation_steps=grad_acc,
            warmup_steps=10,
            num_train_epochs=1,
            learning_rate=2e-4,
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=42,
            output_dir=str(output_dir),
            report_to="none",
            save_strategy="steps",
            save_steps=500,
            max_grad_norm=0.3,
        ),
    )

    trainer = train_on_responses_only(
        trainer,
        instruction_part="<|im_start|>user\n",
        response_part="<|im_start|>assistant\n",
    )

    # Train
    print(f"  Starting training... ({len(raw_data)} examples, 1 epoch)")
    train_start = time.time()
    trainer_stats = trainer.train()
    train_time = time.time() - train_start
    loss = trainer_stats.training_loss if hasattr(trainer_stats, "training_loss") else 0

    print(f"  Training complete. Loss: {loss:.4f}, Time: {train_time:.0f}s")

    # Save adapter
    adapter_path = output_dir / f"nicto_lora_{adapter_name}"
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    print(f"  Adapter saved: {adapter_path}")

    # Save merged GGUF
    gguf_path = output_dir / f"nicto_lora_{adapter_name}_gguf"
    model.save_pretrained_gguf(str(gguf_path), tokenizer, quantization_method="q4_k_m")
    gguf_files = list(gguf_path.glob("*.gguf"))
    for gf in gguf_files:
        print(f"  GGUF: {gf.name} ({gf.stat().st_size/1024/1024:.0f}MB)")

    # Clean up to free VRAM
    del model, tokenizer, trainer, dataset
    torch.cuda.empty_cache()

    elapsed = time.time() - start
    return {
        "model": model_name,
        "adapter": adapter_name,
        "loss": round(loss, 4),
        "train_time_s": round(train_time),
        "total_time_s": round(elapsed),
        "examples": len(raw_data),
        "gguf_path": str(gguf_path),
        "adapter_path": str(adapter_path),
    }


# ─── Step 5: Benchmark Trained Model ─────────────────────────
def step5_benchmark(results: list):
    """Compare all trained adapters and pick the best."""
    print("\n" + "=" * 60)
    print("STEP 5: Benchmark Results & Recommendation")
    print("=" * 60)

    universal_results = [r for r in results if r["adapter"] == "universal"]
    print(f"\n{'Model':<20} {'Loss':<10} {'Time':<10} {'Examples':<10}")
    print("-" * 50)
    for r in universal_results:
        print(f"{r['model']:<20} {r['loss']:<10} {r['train_time_s']:<10}s {r['examples']:<10}")

    if universal_results:
        best = min(universal_results, key=lambda r: r["loss"])
        print(f"\n  🏆 Best base model: {best['model']} (loss={best['loss']})")

    # Generate report
    report_path = OUTPUT_DIR / "training_report.json"
    with open(report_path, "w") as f:
        json.dump({"results": results, "best": best if universal_results else None}, f, indent=2)
    print(f"\n  Report saved: {report_path}")

    return best if universal_results else None


# ─── Full Pipeline ────────────────────────────────────────────
def run_full_pipeline():
    """Run the complete training pipeline."""
    print("=" * 60)
    print("  NICTO COLAB SUPER-TRAINING PIPELINE")
    print("  4 Base Models × 5 Adapters = 20 trainings")
    print("=" * 60)

    if not step1_install():
        print("ERROR: No GPU available. Colab requires GPU runtime.")
        return

    if not step2_download_data():
        print("ERROR: Training data not available.")
        return

    all_results = []

    # Train each base model
    for model_key, model_cfg in BASE_MODELS.items():
        model_dir = OUTPUT_DIR / model_key
        model_dir.mkdir(exist_ok=True)

        print(f"\n{'#' * 60}")
        print(f"# TRAINING BASE MODEL: {model_cfg['id']} ({model_cfg['params']})")
        print(f"{'#' * 60}")

        # Train universal first (all data)
        data_path = DATA_DIR / "universal_chatml.jsonl"
        if data_path.exists():
            result = train_adapter(
                base_model_id=model_cfg["id"],
                model_name=model_key,
                adapter_name="universal",
                data_path=data_path,
                output_dir=model_dir,
                max_seq=model_cfg["max_seq"],
            )
            all_results.append(result)

            # Train specialized adapters (smaller subsets, faster)
            for subset in ["kyros", "omega", "main", "x"]:
                sub_path = DATA_DIR / f"{subset}_chatml.jsonl"
                if sub_path.exists():
                    result = train_adapter(
                        base_model_id=model_cfg["id"],
                        model_name=model_key,
                        adapter_name=subset,
                        data_path=sub_path,
                        output_dir=model_dir,
                        max_seq=model_cfg["max_seq"],
                    )
                    all_results.append(result)

    # Benchmark and pick winner
    step5_benchmark(all_results)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  PIPELINE COMPLETE")
    print(f"  Total trainings: {len(all_results)}")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Next:")
    print(f"    1. Download GGUF files from Drive")
    print(f"    2. Run integrate_gguf.py to wire into NeuralCore")
    print(f"    3. Run benchmark suite to measure improvement")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run_full_pipeline()
