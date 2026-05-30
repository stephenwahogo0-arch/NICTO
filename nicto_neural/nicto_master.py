#!/usr/bin/env python3
"""
NICTO Real AI — Master Orchestrator
Unified entry point for all Real AI modules: setup, train, run, generate.
"""
import json, os, sys, subprocess, argparse
from pathlib import Path

HERE = Path(__file__).parent

MODULES = {
    "setup": {"file": "setup_real_ai.py", "desc": "Detect hardware and select best model"},
    "build_data": {"file": "build_training_data.py", "desc": "Generate 500+ ChatML training pairs"},
    "train": {"file": "train_nicto.py", "desc": "Fine-tune model with Unsloth LoRA"},
    "run": {"file": "run_nicto.py", "desc": "Interactive inference with NICTO model"},
    "image": {"file": "nicto_image_gen.py", "desc": "Image generation (GPU SDXL / CPU prompt)"},
    "video": {"file": "nicto_video_gen.py", "desc": "Video generation (GPU AnimateDiff / CPU code)"},
    "game": {"file": "nicto_game_builder.py", "desc": "3D raycasting FPS game builder"},
}


def print_banner():
    print("""
   +------------------------------------------+
   |     NICTO REAL AI - MASTER ORCHESTRATOR  |
   |          Autonomous. Learning. Evolving.  |
   +------------------------------------------+
    """)


def check_gpu():
    try:
        import torch
        if torch.cuda.is_available():
            vram = torch.cuda.get_device_properties(0).total_memory / 1e9
            return True, torch.cuda.get_device_name(0), vram
        return False, None, 0
    except ImportError:
        return False, None, 0


def run_module(name: str, extra_args: list = None):
    if name not in MODULES:
        print(f"Unknown module: {name}. Available: {', '.join(MODULES.keys())}")
        return False
    info = MODULES[name]
    script = HERE / info["file"]
    if not script.exists():
        print(f"ERROR: {script} not found.")
        return False
    print(f"\n{'=' * 60}")
    print(f"  Module: {name} — {info['desc']}")
    print(f"{'=' * 60}\n")
    cmd = [sys.executable, str(script)]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd)
    return result.returncode == 0


def status():
    print("\nNICTO Real AI - System Status\n")
    has_gpu, gpu_name, vram = check_gpu()
    print(f"  GPU:        {'YES - ' + gpu_name + f' ({vram:.1f}GB VRAM)' if has_gpu else 'NO (CPU only)'}")
    print(f"  Python:     {sys.version.split()[0]}")
    print(f"  Platform:   {sys.platform}")

    config_path = HERE / "hardware_config.json"
    if config_path.exists():
        with open(config_path) as f:
            cfg = json.load(f)
        print(f"  Config:     {cfg.get('model_display', 'N/A')} ({cfg.get('mode', 'N/A')})")

    data_path = HERE / "training_data" / "nicto_chatml.jsonl"
    if data_path.exists():
        with open(data_path) as f:
            count = sum(1 for _ in f)
        print(f"  Training:   {count} examples loaded")
    else:
        print(f"  Training:   No data - run `build_data` first")

    # Check module files
    for name, info in MODULES.items():
        path = HERE / info["file"]
        status_icon = "[OK]" if path.exists() else "[FAIL]"
        print(f"  {status_icon:8} {name:12s} - {info['desc']}")

    print()


def pipeline():
    """Run full pipeline: setup → build_data → train → run."""
    steps = ["setup", "build_data", "train", "run"]
    for step in steps:
        if not run_module(step):
            print(f"\n  Pipeline stopped at: {step}")
            return False
        print(f"\n  Step '{step}' completed.\n")
    print("\n  Full pipeline completed successfully!")
    return True


def main():
    print_banner()
    parser = argparse.ArgumentParser(description="NICTO Real AI Master Orchestrator")
    parser.add_argument("command", nargs="?", default="status",
                        choices=list(MODULES.keys()) + ["status", "pipeline", "all", "help"],
                        help="Command to execute")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Extra arguments for module")
    args = parser.parse_args()

    if args.command == "help":
        print("Commands:")
        for name, info in MODULES.items():
            print(f"  {name:12s} — {info['desc']}")
        print(f"  {'status':12s} — Show system status")
        print(f"  {'pipeline':12s} — Run full pipeline (setup→build→train→run)")
        print(f"  {'all':12s} — Run all modules sequentially")
        return

    if args.command == "status":
        status()
    elif args.command == "pipeline":
        pipeline()
    elif args.command == "all":
        for name in MODULES:
            if not run_module(name):
                print(f"\n  Stopped at: {name}")
                break
        print("\n  All modules completed.")
    else:
        run_module(args.command, args.args)


if __name__ == "__main__":
    main()
